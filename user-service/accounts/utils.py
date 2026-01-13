from rest_framework.response import Response


def api_response(
    success: bool,
    message: str,
    data=None,
    error=None,
    meta=None,
    status=200,
):
    return Response(
        {
            "success": success,
            "message": message,
            "data": data,
            "error": error,
            "meta": meta,
        },
        status=status,
    )
