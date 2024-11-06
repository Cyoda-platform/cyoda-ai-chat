import logging
from pathlib import Path

from common_utils.config import CYODA_ENTITY_VERSION
from middleware._auth.auth import authenticate
from middleware.ingestion.data_ingestion import import_mapping
from middleware.repository.cyoda.cyoda_service import CyodaService

logger = logging.getLogger('django')

def init_cyoda(cyoda_repository: CyodaService):
    entity_dir = Path(__file__).resolve().parent / 'entity'
    token = authenticate()
    for json_file in entity_dir.glob('*/**/*.json'):
        # Ensure the JSON file is in an immediate subdirectory
        if json_file.parent.parent.name != entity_dir.name:
            continue

        try:
            with open(json_file, 'r') as file:
                entity = file.read()
                entity_name = json_file.name.replace(".json", "")
                if not cyoda_repository._model_exists(token, entity_name, CYODA_ENTITY_VERSION):
                    cyoda_repository._save_entity_schema(token, entity_name, CYODA_ENTITY_VERSION, entity)
                    cyoda_repository._lock_entity_schema(token, entity_name, CYODA_ENTITY_VERSION, None)
        except Exception as e:
            logger.error(f"Error reading {json_file}: {e}")
    save_empty_mapping(token)
    token = None


def save_empty_mapping(token):
    json_file = Path(__file__).resolve().parent / 'empty_mapping.json'
    with open(json_file, 'r') as file:
        data = file.read()
        import_mapping(token, data)

