# CargoURL AI

A Flask REST API that analyzes URL click data to surface content optimization
signals — including predicted high-engagement posting windows, audience
segmentation, and click-through rate metrics.

Built as the analytics and AI backend for [CargoURL](https://cargourl.com), a link
management platform. The frontend currently displays AI features as previews using
mock data while the full API integration is in progress.

> **Status:** Work in progress. The API is functional and deployed; AI features on
> cargourl.com are shown as previews with mock data pending full frontend integration.
> See [Roadmap](#roadmap) for planned work.

---

## Features

- **Posting time prediction** — uses [Prophet](https://facebook.github.io/prophet/) to forecast high-engagement windows from historical click timestamps
- **Audience segmentation** — applies KMeans clustering to location and platform fields to identify dominant traffic segments
- **CTR reporting** — computes click-through rate from submitted impression and click data
- **Trend-aware descriptions** *(optional)* — integrates with the Twitter API to pull trending topics into suggested link descriptions
- **API key authentication** — all write endpoints require a header-based key

---

## Stack

| Layer | Technology |
|---|---|
| Web framework | Flask 2.3 |
| Time series forecasting | Prophet (Facebook/Meta) |
| Clustering | scikit-learn KMeans |
| Data handling | pandas |
| Deployment | Railway / Render (Nixpacks) |

---

## Project Structure

```
cargourl-ai/
├── src/
│   ├── app.py           # Flask application and route handlers
│   ├── requirements.txt # Python dependencies
│   ├── Procfile         # Process definition (Heroku-compatible)
│   └── render.yaml      # Render deployment config
└── railway.toml         # Railway deployment config
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- pip

### Installation

```bash
git clone https://github.com/<your-username>/cargourl-ai.git
cd cargourl-ai/src
pip install -r requirements.txt
```

### Environment Variables

| Variable | Required | Description |
|---|---|---|
| `FLASK_API_KEY` | Yes | API key for authenticating POST requests |
| `PORT` | No | Port to bind (default: `5000`) |

Create a `.env` file in `src/` or export these variables in your shell before running.

### Running Locally

```bash
cd src
python app.py
```

The API will be available at `http://localhost:5000`.

---

## API Reference

### `GET /`

Health check.

**Response**
```json
{
  "message": "CargoURL AI API is running!",
  "status": "healthy"
}
```

---

### `POST /optimize`

Analyzes a batch of click events and returns optimization signals.

**Headers**

```
X-API-Key: <your-api-key>
Content-Type: application/json
```

**Request Body**

```json
{
  "clicks": [
    {
      "click_time": "2024-06-01T14:30:00",
      "location": "US",
      "platform": "Instagram",
      "impressions": 500
    },
    {
      "click_time": "2024-06-02T19:00:00",
      "location": "UK",
      "platform": "Twitter",
      "impressions": 300
    }
  ]
}
```

All fields are optional. With no data supplied the endpoint returns conservative
defaults; with 3 or more records the ML models produce data-driven outputs.

**Response**

```json
{
  "optimalTime": "Saturday 07 PM",
  "targetAudience": "US Instagram users",
  "description": null,
  "ctr": 4.5,
  "ctrDelta": 2.5,
  "baselineCtr": 2.0
}
```

Fields are `null` when there is insufficient data to produce a meaningful result.
`ctrDelta` is the difference between the computed CTR and `baselineCtr` (percentage points).

**Status Codes**

| Code | Meaning |
|---|---|
| `200` | Success |
| `401` | Missing or invalid API key |
| `500` | Internal error — check request body format |

---

## Deployment

The repository includes configuration for both **Railway** and **Render**.

### Railway

Push to `main`. Railway picks up `railway.toml` automatically and builds via Nixpacks.

### Render

The `src/render.yaml` service definition targets Python 3.11 on the free plan.
Connect the repo in the Render dashboard; it will use `pip install -r requirements.txt`
and `python app.py` as the start command.

---

## Known Limitations

- KMeans audience segmentation requires at least 3 data points; below that threshold
  `targetAudience` returns `null`.
- All fields return `null` when the corresponding input columns are absent — no default
  values are fabricated.
- Description generation is not yet implemented; the field is reserved for a planned
  trend-keyword integration.

---

## Roadmap

- [ ] Connect frontend to live API endpoints (replace mock data with real responses)
- [ ] LinkedIn Share API integration for posting and retrieving post-level analytics
- [ ] Add input validation and structured error responses
- [ ] Add unit tests for the `/optimize` endpoint
- [ ] Switch production start command to `gunicorn`
- [ ] Add a CI workflow (GitHub Actions)

---

## License

MIT
