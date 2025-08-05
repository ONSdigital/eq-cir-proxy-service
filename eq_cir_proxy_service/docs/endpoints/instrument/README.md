# GET /instrument/{instrument_id}

Retrieves a Collection Instrument (CI) from CIR using the provided instrument_id, and returns the instrument to the caller.

If a version query parameter is provided, and the version parameter does not match the one in the
retrieved instrument, the instrument is updated via the Converter Service API.

## Request

`GET /instrument/{instrument_id}`

### Query parameters

| Parameter name | Value  | Description                                                    | Additional |
|----------------|--------|----------------------------------------------------------------|------------|
| version        | string | Required validator version of retrieved collection instrument. | Optional   |

## Responses

### 200

Success. A JSON return of the matched (and converted) instrument.

### 400

Bad request. Indicates an issue with the request. Further details are provided in the response.

### 404

Not found. The requested CI was not found in CIR, or no instrument_id was provided.

### 422

Unprocessable Entity. The provided instrument_id is not a valid UUID.

### 500

Internal server error. Failed to process the request due to an internal error.

## Sample Queries

`1f8f9f26-90a6-4765-be9e-b6a8631c56e1`
`38cf4789-1756-42bb-b51a-0de44c43535e`

## Sample Output

Output will follow the format of the CIR-approved schema structure

```json
{
    "data_version": "1",
    "language": "en",
    "survey_id": "3456",
    "title": "ExampleTitle",
    "form_type": "business",
    "legal_basis": "",
    "metadata": [],
    "mime_type": "",
    "navigation": {},
    "questionnaire_flow": {},
    "post_submission": {},
    "sds_schema": "",
    "sections": [],
    "submission": {},
    "theme": ""
}
```
