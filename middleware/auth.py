import logging
import re
import requests
from django.http import HttpResponseForbidden
from common_utils.config import (
    ENABLE_AUTH,
    CYODA_AUTH_ENDPOINT,
    API_URL
)

logger = logging.getLogger('django')


class TokenValidationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.api_v1_regex = re.compile(r"^/api/v1/.*")

    def __call__(self, request):
        if not self.api_v1_regex.match(request.path) or ENABLE_AUTH == "false":
            logger.info("Request not authenticated")
            return self.get_response(request)
        token = request.headers.get("Authorization")
        if not token:
            logger.error("No token provided")
            return HttpResponseForbidden("No token provided")
        headers = {"Authorization": token}
        try:
            url = f"{API_URL}/{CYODA_AUTH_ENDPOINT}"
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                logger.error("Invalid token")
                return HttpResponseForbidden("Invalid token")
        except requests.exceptions.RequestException as e:
            logger.error("Error validating token: %s", e)
            return HttpResponseForbidden("Error validating token")
        response = self.get_response(request)
        return response
