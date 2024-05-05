import os
import logging
import requests
import re
from django.http import HttpResponseForbidden
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
CYODA_AUTH_ENDPOINT = os.getenv("CYODA_AUTH_ENDPOINT")
LOCAL = os.getenv("LOCAL")

logging.basicConfig(level=logging.INFO)

class TokenValidationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.api_v1_regex = re.compile(r'^/api/v1/.*')

    def __call__(self, request):
        if LOCAL or not self.api_v1_regex.match(request.path):
            return self.get_response(request)
        token = request.headers.get('Authorization')
        if not token:
            return HttpResponseForbidden('No token provided')
        headers = {'Authorization': token}
        try:
            response = requests.get(CYODA_AUTH_ENDPOINT, headers=headers, timeout=10)
            if response.status_code != 200:
                return HttpResponseForbidden('Invalid token')
        except requests.exceptions.RequestException as e:
            logging.error('Error validating token: %s', e)
            return HttpResponseForbidden('Error validating token')
        response = self.get_response(request)
        return response