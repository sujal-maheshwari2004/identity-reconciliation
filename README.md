# Identity Reconciliation

A backend service that identifies and consolidates customer identities across multiple purchases, even when different contact information is used.

Built for the [Bitespeed Backend Task](https://bitespeed.notion.site/Bitespeed-Backend-Task-Identity-Reconciliation-53392ab01fe149fab989422300423199).

## Live Endpoint
```
POST https://your-render-url.onrender.com/identify
```

## Tech Stack
- **Backend:** Python + FastAPI
- **Database:** PostgreSQL
- **Observability:** Prometheus + Grafana
- **Deployment:** Docker + Render

## Local Setup

### Prerequisites
- Docker Desktop
- Python 3.11+

### Run with Docker
```bash
git clone https://github.com/your-username/identity-reconciliation
cd identity-reconciliation
cp .env.example .env  # fill in your values
docker-compose up --build
```

### Services
| Service | URL |
|---------|-----|
| API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |
| Metrics | http://localhost:8000/metrics |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 |
| Dashboard Redirect | http://localhost:8000/dashboard |

## API Usage

### Identify Contact
```bash
curl -X POST https://your-render-url.onrender.com/identify \
  -H "Content-Type: application/json" \
  -d '{"email": "doc@hillvalley.edu", "phoneNumber": "123456"}'
```

### Response
```json
{
  "contact": {
    "primaryContactId": 1,
    "emails": ["doc@hillvalley.edu"],
    "phoneNumbers": ["123456"],
    "secondaryContactIds": []
  }
}
```

## Reconciliation Logic
| Case | Scenario | Action |
|------|----------|--------|
| 1 | No existing contact | Create new primary |
| 2 | Exact match exists | Return consolidated view |
| 3 | Partial match, new info | Create secondary contact |
| 4 | Two separate clusters bridged | Demote newer primary, merge clusters |

## Observability
Grafana dashboard available at `http://localhost:3000` after running docker-compose. Tracks:
- Request rate
- p95 latency
- Contacts created (primary vs secondary)
- Identity merges
- Reconciliation duration
