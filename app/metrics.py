# app/metrics.py

from prometheus_client import Counter, Histogram

# ─── Counters ───────────────────────────────────────────────────────────────

contacts_created_total = Counter(
    name="contacts_created_total",
    documentation="Total number of contacts created, labelled by type",
    labelnames=["type"]  # type: primary | secondary
)

identity_merges_total = Counter(
    name="identity_merges_total",
    documentation="Total number of times two primary clusters were merged"
)


# ─── Histograms ─────────────────────────────────────────────────────────────

reconciliation_duration_seconds = Histogram(
    name="reconciliation_duration_seconds",
    documentation="Time taken to execute the core reconciliation logic",
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)