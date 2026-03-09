# app/service.py

from datetime import datetime
from app.models import IdentifyResponse, ContactResponse
from app.metrics import contacts_created_total, identity_merges_total, reconciliation_duration_seconds


# ─── Helpers ────────────────────────────────────────────────────────────────

def find_matches(email, phone, conn) -> list[dict]:
    """Fetch all contacts matching either email or phone."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, phone_number, email, linked_id, link_precedence, created_at
            FROM contact
            WHERE deleted_at IS NULL
              AND (email = %s OR phone_number = %s)
        """, (email, phone))
        rows = cur.fetchall()
        return [_row_to_dict(row) for row in rows]


def get_cluster(primary_id: int, conn) -> tuple[dict, list[dict]]:
    """Fetch the primary contact and all its secondaries."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, phone_number, email, linked_id, link_precedence, created_at
            FROM contact
            WHERE deleted_at IS NULL
              AND (id = %s OR linked_id = %s)
            ORDER BY created_at ASC
        """, (primary_id, primary_id))
        rows = cur.fetchall()
        contacts = [_row_to_dict(row) for row in rows]
        primary = next(c for c in contacts if c['link_precedence'] == 'primary')
        secondaries = [c for c in contacts if c['link_precedence'] == 'secondary']
        return primary, secondaries


def create_contact(email, phone, linked_id, precedence: str, conn) -> dict:
    """Insert a new contact row and return it."""
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO contact (email, phone_number, linked_id, link_precedence, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
            RETURNING id, phone_number, email, linked_id, link_precedence, created_at
        """, (email, phone, linked_id, precedence))
        conn.commit()
        return _row_to_dict(cur.fetchone())


def demote_to_secondary(contact_id: int, primary_id: int, conn) -> None:
    """Demote a primary contact to secondary and re-point its secondaries."""
    with conn.cursor() as cur:
        # Re-point all existing secondaries of the demoted primary
        cur.execute("""
            UPDATE contact
            SET linked_id = %s, updated_at = NOW()
            WHERE linked_id = %s AND deleted_at IS NULL
        """, (primary_id, contact_id))

        # Demote the contact itself
        cur.execute("""
            UPDATE contact
            SET link_precedence = 'secondary', linked_id = %s, updated_at = NOW()
            WHERE id = %s
        """, (primary_id, contact_id))

        conn.commit()


def build_response(primary: dict, secondaries: list[dict]) -> IdentifyResponse:
    """Construct the IdentifyResponse from primary and secondaries."""
    all_contacts = [primary] + secondaries

    emails = [primary['email']] if primary['email'] else []
    emails += [c['email'] for c in secondaries if c['email'] and c['email'] != primary['email']]

    phones = [primary['phone_number']] if primary['phone_number'] else []
    phones += [c['phone_number'] for c in secondaries if c['phone_number'] and c['phone_number'] != primary['phone_number']]

    secondary_ids = [c['id'] for c in secondaries]

    return IdentifyResponse(
        contact=ContactResponse(
        primaryContactId=primary['id'],
        emails=emails,
        phoneNumbers=phones,
        secondaryContactIds=secondary_ids
        )
    )


# ─── Core Logic ─────────────────────────────────────────────────────────────

def identify(email: str | None, phone: str | None, conn) -> IdentifyResponse:
    with reconciliation_duration_seconds.time():

        matches = find_matches(email, phone, conn)

        # Case 1 — No matches, brand new customer
        if not matches:
            new_contact = create_contact(email, phone, None, 'primary', conn)
            contacts_created_total.labels(type='primary').inc()
            return build_response(new_contact, [])

        # Resolve all matches to their primary contacts
        primary_ids = set()
        for contact in matches:
            if contact['link_precedence'] == 'primary':
                primary_ids.add(contact['id'])
            else:
                primary_ids.add(contact['linked_id'])

        # Case 4 — Two different clusters being bridged, merge them
        if len(primary_ids) > 1:
            primaries = []
            for pid in primary_ids:
                p, _ = get_cluster(pid, conn)
                primaries.append(p)

            # Oldest primary wins
            primaries.sort(key=lambda c: c['created_at'])
            winner = primaries[0]
            losers = primaries[1:]

            for loser in losers:
                demote_to_secondary(loser['id'], winner['id'], conn)
                identity_merges_total.inc()

        # Single cluster — get the winning primary id
        primary_id = min(primary_ids) if len(primary_ids) == 1 else winner['id']
        primary, secondaries = get_cluster(primary_id, conn)

        # Check if request contains new information
        existing_emails = {c['email'] for c in [primary] + secondaries if c['email']}
        existing_phones = {c['phone_number'] for c in [primary] + secondaries if c['phone_number']}

        has_new_email = email and email not in existing_emails
        has_new_phone = phone and phone not in existing_phones

        # Case 3 — New info on existing cluster, create secondary
        if has_new_email or has_new_phone:
            create_contact(email, phone, primary_id, 'secondary', conn)
            contacts_created_total.labels(type='secondary').inc()
            primary, secondaries = get_cluster(primary_id, conn)

        # Case 2 — Exact match, no new info, just return consolidated view
        return build_response(primary, secondaries)


# ─── Utility ────────────────────────────────────────────────────────────────

def _row_to_dict(row) -> dict:
    """Map a DB row tuple to a named dict."""
    return {
        'id': row[0],
        'phone_number': row[1],
        'email': row[2],
        'linked_id': row[3],
        'link_precedence': row[4],
        'created_at': row[5]
    }
