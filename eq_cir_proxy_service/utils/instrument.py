

import os

from urllib.parse import urlencode

from eq_cir_proxy_service.config.logging_config import logging
from eq_cir_proxy_service.types.custom_types import Instrument

CIR_RETRIEVE_COLLECTION_INSTRUMENT_URL = "/v2/retrieve_collection_instrument"

logger = logging.getLogger(__name__)


def load_schema_from_instrument_id(
    *, cir_instrument_id: str, language_code: str | None
) -> Instrument:
    parameters = {"guid": cir_instrument_id}
    cir_url = f"{current_app.config['CIR_API_BASE_URL']}{CIR_RETRIEVE_COLLECTION_INSTRUMENT_URL}?{urlencode(parameters)}"
    return load_schema_from_url(url=cir_url, language_code=language_code)


@lru_cache(maxsize=None)
def load_schema_from_url(
    url: str, *, language_code: str | None
) -> Instrument:
    """Fetches a schema from the provided url.

    The caller is responsible for including any required query parameters in the url
    """
    language_code = language_code or DEFAULT_LANGUAGE_CODE
    pid = os.getpid()
    logger.info(
        "loading schema from URL",
        schema_url=url,
        language_code=language_code,
        pid=pid,
    )

    session = get_retryable_session(
        max_retries=SCHEMA_REQUEST_MAX_RETRIES,
        retry_status_codes=SCHEMA_REQUEST_RETRY_STATUS_CODES,
        backoff_factor=SCHEMA_REQUEST_BACKOFF_FACTOR,
    )

    # Type ignore: CIR_OAUTH2_CLIENT_ID is an env var which must exist as it is verified in setup.py
    fetch_and_apply_oidc_credentials(session=session, client_id=CIR_OAUTH2_CLIENT_ID)  # type: ignore

    try:
        req = session.get(url, timeout=SCHEMA_REQUEST_TIMEOUT)
    except RequestException as exc:
        logger.exception(
            "schema request errored",
            schema_url=url,
        )
        raise SchemaRequestFailed from exc

    if req.status_code == 200:
        schema_response = req.content.decode()
        response_duration_in_milliseconds = req.elapsed.total_seconds() * 1000

        logger.info(
            f"schema request took {response_duration_in_milliseconds:.2f} milliseconds",
            pid=pid,
        )

        return Instrument(json_loads(schema_response), language_code)

    logger.error(
        "got a non-200 response for schema url request",
        status_code=req.status_code,
        schema_url=url,
    )

    raise SchemaRequestFailed
