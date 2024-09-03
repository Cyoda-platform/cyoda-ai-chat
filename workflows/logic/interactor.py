import logging
import json
from typing import List, Dict
from common_utils.utils import get_env_var, send_get_request

logger = logging.getLogger('django')
API_URL = get_env_var("API_URL")
GET_NEXT_TRANSITION_PATH = get_env_var("GET_NEXT_TRANSITION_PATH")
GET_NEXT_TRANSITION_PATH
class WorkflowsInteractor:
    def __init__(self):
        logger.info("Initializing ConnectionsInteractor...")
        
    
    def save_workflow_entity(self, prompt):
        pass
    
    def get_next_transitions(self, token, workflow_id, entity_id, entity_class):
        #get next trnsitions
        next_transitions_path = f"platform-api/entity/fetch/transitions?entityId={entity_id}&entityClass={entity_class}"
        next_transitions = send_get_request(token, API_URL, next_transitions_path)
        #get all transitions
        all_transitions_path = f"platform-api/statemachine/persisted/workflows/{workflow_id}/transitions"
        all_transitions = send_get_request(token, API_URL, all_transitions_path)
        # Extract the required transitions
        data = all_transitions.json()
        next_transitions_list = next_transitions.json()
        transitions = []
        for transition in data["Data"]:
            if transition["name"] in next_transitions_list:
                transitions.append({
                    "name": transition["name"],
                    "description": transition["description"]
                })

        # Output the result as JSON
        result = {"transitions": transitions}

        # Print the resulting JSON
        return result