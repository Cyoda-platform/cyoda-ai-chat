import os
import logging
import requests
from typing import Optional
import uuid
import json
import jsonschema
from jsonschema import validate

logger = logging.getLogger('django')


def generate_uuid() -> uuid:
    return uuid.uuid1()
    
def parse_json(result: str) -> str:
    if result.startswith("```"):
        return "\n".join(result.split("\n")[1:-1])
    if not result.startswith("{"):
        start_index = result.find("```json")
        if start_index != -1:
            start_index += len("```json\n")
            end_index = result.find("```", start_index)
            return result[start_index:end_index].strip()
    return result

def validate_result(parsed_result: str, file_path: str) -> bool:
    try:
        with open(file_path, "r") as schema_file:
            schema = json.load(schema_file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error reading schema file {file_path}: {e}")
        raise

    try:
        json_data = json.loads(parsed_result)
        validate(instance=json_data, schema=schema)
        logger.info("JSON validation successful.")
        return True
    except jsonschema.exceptions.ValidationError as err:
        logger.error(f"JSON validation failed: {err.message}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON: {e}")
        raise

def get_env_var(name: str) -> str:
    value = os.getenv(name)
    if value is None:
        logger.warning(f"Environment variable {name} not found.")
    return value

def read_file(file_path: str):
    """Read and return JSON data from a file."""
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except Exception as e:
        logger.error(f"Failed to read JSON file {file_path}: {e}")
        raise

def read_json_file(file_path: str):
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
        logger.info(f"Successfully read JSON file: {file_path}")
        return data
    except FileNotFoundError as e:
        logger.error(f"File not found: {file_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"JSON decoding failed for file {file_path}: {e}")
        raise

def send_get_request(token: str, api_url: str, path: str) -> Optional[requests.Response]:
    url = f"{api_url}/{path}"
    token = f"Bearer {token}" if not token.startswith('Bearer') else token
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"{token}",
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad status codes
        logger.info(f"GET request to {url} successful.")
        return response
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error during GET request to {url}: {http_err}")
        raise
    except Exception as err:
        logger.error(f"Error during GET request to {url}: {err}")
        raise

def send_post_request(token: str, api_url: str, path: str, data=None, json=None) -> Optional[requests.Response]:
    url = f"{api_url}/{path}"
    token = f"Bearer {token}" if not token.startswith('Bearer') else token
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"{token}",
    }
    try:
        response = requests.post(url, headers=headers, data=data, json=json)
        response.raise_for_status()  # Raise an error for bad status codes
        logger.info(f"POST request to {url} successful.")
        return response
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error during POST request to {url}: {http_err}")
        raise
    except Exception as err:
        logger.error(f"Error during POST request to {url}: {err}")
        raise

def send_put_request(token: str, api_url: str, path: str, data=None, json=None) -> Optional[requests.Response]:
    url = f"{api_url}/{path}"
    token = f"Bearer {token}" if not token.startswith('Bearer') else token
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"{token}",
    }
    try:
        response = requests.put(url, headers=headers, data=data, json=json)
        response.raise_for_status()  # Raise an error for bad status codes
        logger.info(f"PUT request to {url} successful.")
        return response
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error during PUT request to {url}: {http_err}")
        raise
    except Exception as err:
        logger.error(f"Error during PUT request to {url}: {err}")
        raise

def send_delete_request(token: str, api_url: str, path: str) -> Optional[requests.Response]:
    url = f"{api_url}/{path}"
    token = f"Bearer {token}" if not token.startswith('Bearer') else token
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"{token}",
    }
    try:
        response = requests.delete(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad status codes
        logger.info(f"GET request to {url} successful.")
        return response
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error during GET request to {url}: {http_err}")
        raise
    except Exception as err:
        logger.error(f"Error during GET request to {url}: {err}")
        raise