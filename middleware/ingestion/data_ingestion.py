import logging
from pathlib import Path

from common_utils.config import API_URL, CYODA_ENTITY_VERSION
from common_utils.utils import read_file, send_post_request, send_get_request
from middleware.repository.cyoda.cyoda_service import CyodaService

logger = logging.getLogger(__name__)

repository = CyodaService()
def ingest_data_from_connection(token, entity_name):
    file_path = Path(__file__).resolve().parent.parent.parent / f'entity/{entity_name}/ingestion/ingestion_request.json'
    data = read_file(file_path)
    resp = send_post_request(token, API_URL, "data-source/request/request", data)
    return resp.json()

def get_data_ingestion_status(token, request_id):
    resp = send_get_request(token, API_URL, f"data-source/request/result/{request_id}")
    return resp.json()

def get_all_entities(token, entity_name):
    response = repository.find_all({"token":token, "entity_model": entity_name,"entity_version": CYODA_ENTITY_VERSION})
    return response

def import_mapping(token, data: str):
    resp = send_post_request(token, API_URL, "data-source-config/import-cobi-config?cleanBeforeImport=false&doPostProcess=false", data)
    return resp.json()