# API Examples

This document provides `curl` examples for interacting with the Telematics Risk API.

**Assumptions:**
*   The API is running locally at `http://127.0.0.1:8000`.
*   You have set your `API_TOKEN` in a `.env` file or as an environment variable. Replace `YOUR_API_TOKEN` with your actual token.

---

## 1. Get Root Message

Checks if the API is running.

```bash
curl -X GET "http://127.0.0.1:8000/"
```

---

## 2. Score Driver

Scores a driver and provides risk contributors.

**Request Body Example:**
```json
{
  "driver_id": "driver_1"
}
```

**cURL Command:**
```bash
curl -X POST "http://127.0.0.1:8000/score" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_API_TOKEN" \
     -d '{
           "driver_id": "driver_1"
         }'
```

---

## 3. Calculate Premium

Calculates the insurance premium based on a risk score.

**Request Body Example:**
```json
{
  "driver_id": "driver_1",
  "base_premium": 100.0,
  "score": 0.5
}
```

**cURL Command:**
```bash
curl -X POST "http://127.0.0.1:8000/price" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_API_TOKEN" \
     -d '{
           "driver_id": "driver_1",
           "base_premium": 100.0,
           "score": 0.5
         }'
```
