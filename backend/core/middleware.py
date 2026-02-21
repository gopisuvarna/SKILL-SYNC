"""Custom middleware for security and CSRF handling."""
import re
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin


class RateLimitMiddleware(MiddlewareMixin):
    """
    Simple in-memory rate limiter. Use Redis in production for distributed systems.
    Rate: 100 requests per minute per IP for auth endpoints.
    """
    _requests = {}
    RATE_LIMIT = 100
    WINDOW = 60

    def process_request(self, request):
        if not re.match(r'^/api/auth/(login|register)', request.path):
            return None
        ip = self._get_client_ip(request)
        import time
        now = time.time()
        if ip not in self._requests:
            self._requests[ip] = []
        self._requests[ip] = [t for t in self._requests[ip] if now - t < self.WINDOW]
        if len(self._requests[ip]) >= self.RATE_LIMIT:
            return JsonResponse({'detail': 'Rate limit exceeded'}, status=429)
        self._requests[ip].append(now)
        return None

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '127.0.0.1')


class CSRFCookieMiddleware(MiddlewareMixin):
    """Ensure CSRF cookie is set for cookie-based auth."""
    def process_response(self, request, response):
        if request.path.startswith('/api/') and not response.cookies.get('csrftoken'):
            from django.middleware.csrf import get_token
            get_token(request)
        return response
