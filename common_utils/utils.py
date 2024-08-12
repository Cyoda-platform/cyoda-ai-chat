import os
import logging
import requests
from typing import Optional


logger = logging.getLogger('django')

def parse_json(result):
    if result.startswith("```"):
        return "\n".join(result.split("\n")[1:-1])
    if not result.startswith("{"):
        start_index = result.find("```json")
        if start_index != -1:
            start_index += len("```json\n")
            end_index = result.find("```", start_index)
            return result[start_index:end_index].strip()
    return result


def get_env_var(name):
    return os.getenv(name)


def send_get_request(
    token: str, api_url: str, path: str
) -> Optional[requests.Response]:
    url = f"{api_url}/{path}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"{token}",
    }
    try:
        response = requests.get(url, headers=headers)
        return response
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err}")
    except Exception as err:
        logger.error(f"Other error occurred: {err}")
    return None


def send_post_request(
    token: str, api_url: str, path: str, data, json
) -> Optional[requests.Response]:
    url = f"{api_url}/{path}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"{token}",
    }
    try:
        response = requests.post(url, headers=headers, data=data, json=json)
        return response
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err}")
    except Exception as err:
        logger.error(f"Other error occurred: {err}")
    return None


def send_put_request(
    token: str, api_url: str, path: str, data, json
) -> Optional[requests.Response]:
    url = f"{api_url}/{path}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"{token}",
    }
    try:
        response = requests.put(url, headers=headers, data=data, json=json)
        return response
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err}")
    except Exception as err:
        logger.error(f"Other error occurred: {err}")
    return None
