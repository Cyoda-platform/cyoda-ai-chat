import logging
import requests
import re
from django.http import HttpResponseForbidden
from dotenv import load_dotenv

from common_utils.utils import get_env_var

# Load environment variables
load_dotenv()

# Constants
API_URL = get_env_var("API_URL")
CYODA_AUTH_ENDPOINT = get_env_var("CYODA_AUTH_ENDPOINT")
ENABLE_AUTH = get_env_var("ENABLE_AUTH")

logger = logging.getLogger('django')

class TokenValidationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.api_v1_regex = re.compile(r"^/api/v1/.*")

    def __call__(self, request):
        if not self.api_v1_regex.match(request.path) or not ENABLE_AUTH:
            logger.info("Request not authenticated")
            return self.get_response(request)
        token = request.headers.get("Authorization")
        if not token:
            return HttpResponseForbidden("No token provided")
        headers = {"Authorization": token}
        try:
            url = f"{API_URL}/{CYODA_AUTH_ENDPOINT}"
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return HttpResponseForbidden("Invalid token")
        except requests.exceptions.RequestException as e:
            logger.error("Error validating token: %s", e)
            return HttpResponseForbidden("Error validating token")
        response = self.get_response(request)
        return response
