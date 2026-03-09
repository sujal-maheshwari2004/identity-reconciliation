
CREATE TYPE link_precedence AS ENUM ('primary', 'secondary');

CREATE TABLE IF NOT EXISTS contact (
    id              SERIAL PRIMARY KEY,
    phone_number    VARCHAR(15),
    email           VARCHAR(255),
    linked_id       INTEGER REFERENCES contact(id) ON DELETE SET NULL,
    link_precedence link_precedence NOT NULL,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at      TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_contact_email        ON contact(email);
CREATE INDEX IF NOT EXISTS idx_contact_phone_number ON contact(phone_number);
CREATE INDEX IF NOT EXISTS idx_contact_linked_id    ON contact(linked_id);