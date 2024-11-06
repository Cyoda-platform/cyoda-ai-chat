from typing import Any, List, Dict

from middleware.repository.crud_repository import CrudRepository
from middleware.repository.cyoda.cyoda_service import CyodaService
from middleware.service.entity_service_interface import EntityService

repository: CrudRepository = CyodaService()
class EntityServiceImpl(EntityService):

    def get_item(self, token: str, entity_model: str, entity_version: str, id: str) -> Any:
        """Retrieve a single item based on its ID."""
        meta = repository.get_meta(token, entity_model, entity_version)
        resp = repository.find_by_id(meta, id)
        return resp

    def get_items(self, token: str, entity_model: str, entity_version: str) -> List[Any]:
        """Retrieve multiple items based on their IDs."""
        meta = repository.get_meta(token, entity_model, entity_version)
        resp = repository.find_all(meta)
        return resp

    def get_single_item_by_condition(self, token: str, entity_model: str, entity_version: str, condition: Any) -> List[Any]:
        """Retrieve multiple items based on their IDs."""
        resp = self._find_by_criteria(token, entity_model, entity_version, condition)
        return resp[0]

    def get_items_by_condition(self, token: str, entity_model: str, entity_version: str, condition: Any) -> List[Any]:
        """Retrieve multiple items based on their IDs."""
        resp = self._find_by_criteria(token, entity_model, entity_version, condition)
        return resp

#User:
#'{"name": "test", "email": "q@q.q", "user_id": "da6ec603-8b26-11ef-9688-40c2ba0ac9eb", "role": "Start-up"}'
#{'entity_model': 'user_v1', 'entity_version': '1000', 'token': 'eyJr'}
#
    def add_item(self, token: str, entity_model: str, entity_version: str, entity: Any) -> Any:
        """Add a new item to the repository."""
        meta = repository.get_meta(token, entity_model, entity_version)
        resp = repository.save(meta, entity)
        return resp

    def update_item(self, token: str, entity_model: str, entity_version: str, id: str, entity: Any, meta: Any) -> Any:
        """Update an existing item in the repository."""
        meta = meta.update(repository.get_meta(token, entity_model, entity_version))
        resp = repository.update(meta, id, entity)
        return resp

    def _find_by_criteria(self, token, entity_model, entity_version, condition):
        meta = repository.get_meta(token, entity_model, entity_version)
        resp = repository.find_all_by_criteria(meta, condition)
        if (resp['page']['totalElements'] == 0):
            #resp = {'page': {'number': 0, 'size': 10, 'totalElements': 0, 'totalPages': 0}}
            return []
        #resp = {'_embedded': {'objectNodes': [{'id': 'f04bce86-89a9-11b2-aa0c-169608d9bc9e', 'tree': {'email': '4126cf85-61b6-48ec-b7bc-89fc1999d9b9@q.q', 'name': 'test', 'role': 'Start-up', 'user_id': '1703b76f-8b2f-11ef-9910-40c2ba0ac9eb'}}]}, 'page': {'number': 0, 'size': 10, 'totalElements': 1, 'totalPages': 1}}
        resp = resp["_embedded"]["objectNodes"]
        return resp