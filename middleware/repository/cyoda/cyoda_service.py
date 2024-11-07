import json
import threading
import time
from typing import List, Any, Optional

import logging

from middleware.entity.entity import BaseEntity
from middleware.entity.entity_factory import base_entity_from_dict
from middleware.repository.crud_repository import CrudRepository
from common_utils.config import (CYODA_AI_IMPORT_MODEL_PATH,
                                 API_URL
                                 )
from common_utils.utils import (send_get_request,
                                send_put_request,
                                send_post_request,
                                send_delete_request, now)

logger = logging.getLogger('django')


class CyodaService(CrudRepository):
    _instance = None
    _lock = threading.Lock()  # Lock for thread safety

    def __new__(cls):
        logger.info("initializing CyodaService")
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(CyodaService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        pass

    def count(self, meta) -> int:
        pass

    def delete_all(self, meta) -> None:
        pass

    def delete_all_entities(self, meta, entities: List[Any]) -> None:
        pass

    def delete_all_by_key(self, meta, keys: List[Any]) -> None:
        pass

    def delete_by_key(self, meta, key: Any) -> None:
        pass

    def exists_by_key(self, meta, key: Any) -> bool:
        pass

    def find_all(self, meta) -> List[BaseEntity]:
        pass

    def find_all_by_key(self, meta, keys: List[Any]) -> List[BaseEntity]:
        return self._get_all_by_ids(meta, keys)

    def find_by_key(self, meta, key: Any) -> Optional[BaseEntity]:
        return self._get_by_id(meta, key)

    def save(self, meta, entity: Any) -> Any:
        pass

    def save_all(self, meta, entities: List[BaseEntity]) -> bool:
        return self._save_new_entities(meta, entities)

    def update_all(self, meta, entities: List[Any]) -> List[BaseEntity]:
        return self._update_entities(meta, entities)

    def _search_entities(self, meta, key):
        # Create a snapshot search
        snapshot_response = self._create_snapshot_search(
            token=meta["token"],
            model_name=meta["entity_model"],
            model_version=meta["entity_version"],
            condition=meta["get_by_id_condition"]
        )
        snapshot_id = snapshot_response
        if not snapshot_id:
            logger.error(f"Snapshot ID not found in response: {snapshot_response}")
            return None

        # Wait for the search to complete
        status_response = self._wait_for_search_completion(
            token=meta["token"],
            snapshot_id=snapshot_id,
            timeout=60,  # Adjust timeout as needed
            interval=300  # Adjust interval (in milliseconds) as needed
        )

        # Retrieve search results
        search_result = self._get_search_result(
            token=meta["token"],
            snapshot_id=snapshot_id,
            page_size=100,  # Adjust page size as needed
            page_number=1  # Starting with the first page
        )
        return search_result

    def _get_all_by_ids(self, meta, keys) -> List[BaseEntity]:
        try:
            entities = []
            for key in keys:
                search_result = self._search_entities(meta, key)
                if search_result.get('page').get('totalElements', 0) == 0:
                    return []
                result_entities = self.convert_to_entities(search_result)
                base_entities = [base_entity_from_dict(meta["entity_model"], entity) for entity in result_entities]
                entities.extend(base_entities)
                logger.info(f"Successfully retrieved CacheEntity for key '{key}'.")
            return entities


        except TimeoutError as te:
            logger.error(f"Timeout while reading key '{key}': {te}")
        except Exception as e:
            logger.error(f"Error reading key '{key}': {e}")
            logger.exception("An exception occurred")

        return None

    def _get_by_id(self, meta, key) -> Optional[BaseEntity]:
        try:
            search_result = self._search_entities(meta, key)
            # Convert search results to CacheEntity
            if search_result.get('page').get('totalElements', 0) == 0:
                return None
            result_entities = self.convert_to_entities(search_result)
            entity = base_entity_from_dict(meta["entity_model"], result_entities[0])
            logger.info(f"Successfully retrieved CacheEntity for key '{key}'.")
            if entity is not None:
                return entity
            return None

        except TimeoutError as te:
            logger.error(f"Timeout while reading key '{key}': {te}")
        except Exception as e:
            logger.error(f"Error reading key '{key}': {e}")
            logger.exception("An exception occurred")

        return None

    def _save_new_entities(self, meta, entities: List[Any]) -> bool:
        try:
            entities_data = json.dumps([
                {key: value for key, value in entity.to_dict().items() if (value is not None and key != "technical_id")}
                for entity in entities
            ])
            self._save_new_entity(
                token=meta["token"],
                model=meta["entity_model"],
                version=meta["entity_version"],
                data=entities_data
            )
            return True
        except Exception as e:
            logger.error(f"Exception occurred while saving entity: {e}")
            logger.exception("An exception occurred")
            raise e

    def delete(self, meta, entity: Any) -> None:
        pass

    @staticmethod
    def _save_entity_schema(token, entity_name, version, data):
        path = f"{CYODA_AI_IMPORT_MODEL_PATH}/JSON/SAMPLE_DATA/{entity_name}/{version}"

        try:
            response = send_post_request(token=token, api_url=API_URL, path=path, data=data)
            if response.status_code == 200:
                logger.info(
                    f"Successfully saved schema for entity '{entity_name}' with version '{version}'. Response: {response}")
            else:
                logger.error(
                    f"Failed to save schema for entity '{entity_name}' with version '{version}'. Response: {response}")

            return response

        except Exception as e:
            logger.error(
                f"An error occurred while saving schema for entity '{entity_name}' with version '{version}': {e}")
            logger.exception("An exception occurred")
            return {'error': str(e)}

    @staticmethod
    def _lock_entity_schema(token, entity_name, version, data):
        path = f"treeNode/model/{entity_name}/{version}/lock"

        try:
            response = send_put_request(token=token, api_url=API_URL, path=path, data=data)

            if response.status_code == 200:
                logger.info(
                    f"Successfully locked schema for entity '{entity_name}' with version '{version}'. Response: {response}")
            else:
                logger.error(
                    f"Failed to lock schema for entity '{entity_name}' with version '{version}'. Response: {response}")

            return response
        except Exception as e:
            logger.error(
                f"An error occurred while locking schema for entity '{entity_name}' with version '{version}': {e}")
            logger.exception("An exception occurred")
            return {'error': str(e)}

    @staticmethod
    def _save_new_entity(token, model, version, data):
        path = f"entity/JSON/TREE/{model}/{version}"
        logger.info(f"Saving new entity to path: {path}")

        try:
            response = send_post_request(token=token, api_url=API_URL, path=path, data=data)

            if response.status_code == 200:
                logger.info(f"Successfully saved new entity. Response: {response}")
                return response
            else:
                logger.error(f"Failed to save new entity. Response: {response}")
                raise Exception(f"Failed to save new entity. Response: {response}")

        except Exception as e:
            logger.error(f"An error occurred while saving new entity '{model}' with version '{version}': {e}")
            logger.exception("An exception occurred")
            raise e

    @staticmethod
    def _model_exists(token, model_name, model_version):
        export_model_url = f"treeNode/model/export/SIMPLE_VIEW/{model_name}/{model_version}"

        response = send_get_request(token, API_URL, export_model_url)

        if response.status_code == 200:
            return True
        elif response.status_code == 404:
            return False
        else:
            raise Exception(f"Get: {response.status_code} {response.text}")

    @staticmethod
    def _delete_all_entities(token, model_name, model_version):
        delete_entities_url = f"entity/TREE/{model_name}/{model_version}"

        response = send_delete_request(token, API_URL, delete_entities_url)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Deletion failed: {response.status_code} {response.text}")

    @staticmethod
    def _create_snapshot_search(token, model_name, model_version, condition):
        search_url = f"treeNode/search/snapshot/{model_name}/{model_version}"
        logger.info(condition)
        response = send_post_request(token, API_URL, search_url, data=json.dumps(condition))
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Snapshot search trigger failed: {response.status_code} {response.text}")

    @staticmethod
    def _get_snapshot_status(token, snapshot_id):
        status_url = f"treeNode/search/snapshot/{snapshot_id}/status"

        response = send_get_request(token, API_URL, status_url)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Snapshot search trigger failed: {response.status_code} {response.text}")

    def _wait_for_search_completion(self, token, snapshot_id, timeout=5, interval=10):
        start_time = now()  # Record the start time

        while True:
            status_response = self._get_snapshot_status(token, snapshot_id)
            status = status_response.get("snapshotStatus")

            # Check if the status is SUCCESSFUL or FAILED
            if status == "SUCCESSFUL":
                return status_response
            elif status != "RUNNING":
                raise Exception(f"Snapshot search failed: {json.dumps(status_response, indent=4)}")

            elapsed_time = now() - start_time

            if elapsed_time > timeout:
                raise TimeoutError(f"Timeout exceeded after {timeout} seconds")

            time.sleep(interval / 1000)  # Wait for the given interval (msec) before checking again

    @staticmethod
    def _get_search_result(token, snapshot_id, page_size, page_number):
        result_url = f"treeNode/search/snapshot/{snapshot_id}"

        params = {
            'pageSize': f"{page_size}",
            'pageNumber': f"{page_number}"
        }

        response = send_get_request(token=token, api_url=API_URL, path=result_url)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Get search result failed: {response.status_code} {response.text}")

    @staticmethod
    def _update_entities(meta, entities: List[Any]) -> List[Any]:
        path = "entity/JSON/TREE"
        payload = []
        for entity in entities:
            entities_data = {
                key: value for key, value in entity.to_dict().items()
                if value is not None and key != "technical_id"
            }

            payload_json = json.dumps(entities_data)

            payload.append({
                "id": entity.technical_id,
                "transition": meta["update_transition"],
                "payload": payload_json
            })
            data = json.dumps(payload)
            response = send_put_request(meta["token"], API_URL, path, data=data)
            if response.status_code == 200:
                return entities
            else:
                raise Exception(f"Get search result failed: {response.status_code} {response.text}")

        return entities

    @staticmethod
    def _update_entity(meta, entities: List[Any]) -> List[Any]:
        path = "entity/JSON/TREE"
        for entity in entities:
            entities_data = {
                key: value for key, value in entity.to_dict().items()
                if value is not None and key != "technical_id"
            }
            payload_json = json.dumps(entities_data)
            update_transition = meta["update_transition"]
            response = send_put_request(meta["token"], API_URL,
                                        f"{path}/{entity.technical_id}/{update_transition}", data=payload_json)
            if response.status_code == 200:
                return entities
            else:
                raise Exception(f"Get search result failed: {response.status_code} {response.text}")

        return entities

    @staticmethod
    def convert_to_entities(data):
        # Check if totalElements is zero
        if data.get("page", {}).get("totalElements", 0) == 0:
            return None

        # Extract entities from _embedded.objectNodes
        entities = []
        object_nodes = data.get("_embedded", {}).get("objectNodes", [])

        for node in object_nodes:
            # Extract the tree object
            tree = node.get("tree")
            tree["technical_id"] = node.get("id")
            if tree:
                entities.append(tree)

        return entities
