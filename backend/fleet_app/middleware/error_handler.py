from django.http import JsonResponse

from fleet_app.services.exceptions import BadRequest, BusinessConflict


class ErrorHandlerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, BusinessConflict):
            return JsonResponse(
                {'code': exception.code, 'message': exception.message,
                 'details': exception.details},
                status=409,
            )
        if isinstance(exception, BadRequest):
            return JsonResponse(
                {'code': exception.code, 'message': exception.message},
                status=400,
            )
        return None
