import time
class RequestLoggerMiddleware:
    def __init__(self, get_response): self.get_response = get_response
    def __call__(self, request):
        started = time.time()
        response = self.get_response(request)
        response['X-Request-Duration'] = str(round((time.time() - started) * 1000, 2))
        return response
