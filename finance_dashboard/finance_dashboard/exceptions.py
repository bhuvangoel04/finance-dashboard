# Custom exception handler for consistent error response format.

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        error_data = {
            "success": False,
            "error": {
                "code": _get_error_code(response.status_code),
                "message": _get_human_message(response.status_code, response.data),
            }
        }

        # Attach field-level validation errors when present
        if isinstance(response.data, dict) and any(
            k != 'detail' for k in response.data
        ):
            error_data["error"]["details"] = response.data
        elif isinstance(response.data, dict) and 'detail' in response.data:
            error_data["error"]["message"] = str(response.data['detail'])

        response.data = error_data

    return response


def _get_error_code(status_code):
    codes = {
        400: "VALIDATION_ERROR",
        401: "AUTHENTICATION_REQUIRED",
        403: "PERMISSION_DENIED",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        429: "RATE_LIMITED",
        500: "SERVER_ERROR",
    }
    return codes.get(status_code, f"HTTP_{status_code}")


def _get_human_message(status_code, data):
    messages = {
        400: "The request contains invalid or missing data.",
        401: "Authentication credentials were not provided or are invalid.",
        403: "You do not have permission to perform this action.",
        404: "The requested resource was not found.",
        405: "This HTTP method is not allowed for this endpoint.",
        429: "Too many requests. Please slow down.",
        500: "An internal server error occurred.",
    }
    return messages.get(status_code, "An unexpected error occurred.")