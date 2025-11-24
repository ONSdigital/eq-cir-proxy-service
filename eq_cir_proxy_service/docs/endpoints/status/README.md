# GET /status

The /status endpoint provides a simple health check used by Cloud Run to verify that the Proxy Service is running and able to respond to requests.

The endpoint does not require any parameters and returns a small JSON response confirming the service is running.

## Request

`GET /status`

### Query parameters

| Parameter name | Value | Description                                   | Additional |
| -------------- | ----- | --------------------------------------------- | ---------- |
| None           | ----- | No parameters are required for this endpoint. | ----       |

## Responses

### 200

Success. A JSON return of the matched (and converted) instrument.

### 500

Internal server error. Failed to process the request due to an internal error.

## Sample Output

```json
{
    "status": "OK"
}
```
