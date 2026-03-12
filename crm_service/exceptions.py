## crm_service\crm_service\exceptions.py
import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        original_data = response.data

        code_map = {
            400: "bad_request",
            401: "unauthorized",
            403: "forbidden",
            404: "not_found",
            405: "method_not_allowed",
            409: "conflict",
            422: "unprocessable_entity",
            429: "too_many_requests",
        }

        code = code_map.get(response.status_code, "error")

        if isinstance(original_data, dict) and "detail" in original_data:
            message = str(original_data["detail"])
            details = None
        elif isinstance(original_data, dict):
            message = "Validation error. Check 'details' for field-level errors."
            details = original_data
            code = "validation_error"
        else:
            message = str(original_data)
            details = None

        payload = {"error": {"code": code, "message": message}}
        if details:
            payload["error"]["details"] = details

        response.data = payload

    else:
        logger.exception("Unhandled exception: %s", exc)
        response = Response(
            {"error": {"code": "internal_error", "message": "An unexpected error occurred."}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response
