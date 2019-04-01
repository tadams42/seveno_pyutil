try:
    import simplejson as json
except Exception:
    import json

import logging

import pygments
from pygments.formatters import Terminal256Formatter

logger = logging.getLogger(__name__)


def _colored_json(data):
    try:
        if isinstance(data, (dict, list)):
            json_str = json.dumps(data)
        else:
            json_str = None
    except Exception:
        json_str = None

    if not json_str:
        return data

    return pygments.highlight(
        json_str,
        pygments.lexers.get_lexer_for_mimetype("application/json"),
        Terminal256Formatter(style="monokai"),
    )


def log_http_request(request, colorized=False):
    """
    Log some stuff from HTTP request.

    Known to work with Flask and Django request objects.

    Todo:
        Convert into `logging.Filter`
    """

    # Requests received by local Flask will have "path" and "url".
    # Requests outgoing from local Flask to some other service will have only
    # "url".
    destination = getattr(request, "path", None) or getattr(request, "url", None)

    logger.info("Started HTTP request %s: %s", request.method, destination)

    headers = [(k.strip(), v.strip()) for k, v in request.headers]

    logger.debug(
        "HTTP request headers: %s",
        (
            _colored_json(dict(headers)) if colorized else json.dumps(dict(headers))
        ).strip(),
    )

    if (
        getattr(request, "is_json", None)
        or request.headers.get("Content-Type", None) == "application/json"
    ):
        logger.info(
            "HTTP request payload: %s",
            _colored_json(request.json).strip()
            if colorized
            else str(request.json).strip(),
        )


def log_http_response(for_request, response, colorized=False, response_metrics=None):
    """
    Log some stuff from HTTP request.

    Known to work with Flask and Django request objects.

    Todo:
        Convert into `logging.Filter`
    """

    try:

        headers = [(k.strip(), v.strip()) for k, v in response.headers]

        logger.debug(
            "HTTP response headers: %s",
            (
                _colored_json(dict(headers)) if colorized else json.dumps(dict(headers))
            ).strip(),
        )

        if (
            getattr(response, "content_type", None) == "application/json"
            or response.headers.get("Content-Type", None) == "application/json"
        ):
            payload = getattr(response, "json", "") or response.data.decode("UTF-8")

            if callable(payload):
                payload = payload()

            if isinstance(payload, str):
                payload = json.loads(payload)

            logger.info(
                "HTTP response payload: %s",
                (_colored_json(payload) if colorized else json.dumps(payload)).strip(),
            )

        if response_metrics:
            logger.info(
                "Completed %s %s %s %s",
                for_request.method,
                getattr(for_request, "path", None) or getattr(for_request, "url", None),
                getattr(response, "status", None)
                or getattr(response, "status_code", None),
                (
                    _colored_json(dict(response_metrics))
                    if colorized
                    else json.dumps(dict(response_metrics))
                ).strip(),
            )
        else:
            logger.info(
                "Completed %s %s %s",
                for_request.method,
                getattr(for_request, "path", None) or getattr(for_request, "url", None),
                getattr(response, "status", None)
                or getattr(response, "status_code", None),
            )

    except Exception:
        logger.warning("Failed to log HTTP response!", exc_info=True)

    return response
