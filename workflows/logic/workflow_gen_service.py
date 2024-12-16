import logging
import json
from common_utils.utils import (
    send_get_request,
    send_post_request,
    send_delete_request,
    read_json_file
)
from common_utils.config import (
    API_URL,
    ENV,
    WORK_DIR
)

logger = logging.getLogger('django')
initialized_requests = set()


class ConfigGenerationError(Exception):
    """Custom exception for errors in configuration generation."""
    pass


class WorkflowGenerationService:
    def __init__(self):
        logger.info("Initializing WorkflowService...")

    def generate_workflow_from_json(self, token, data, class_name):
        """Generate and configure a workflow from a JSON configuration."""
        workflow_file_path = f"{WORK_DIR}/data/v1/workflows/workflow.json"
        return self._process_workflow(token, data, class_name, workflow_file_path)

    def generate_workflow_transitions_from_json(self, token, transitions, class_name, workflow_id):
        """Generate and configure workflow transitions from a JSON configuration."""
        data = {"transitions": transitions}
        return self._process_workflow(token, data, class_name, None, workflow_id)

    def _process_workflow(self, token, data, class_name, workflow_file_path=None, workflow_id=None):
        """Process the workflow configuration and update states, criteria, processes, and transitions."""
        if workflow_file_path:
            workflow_id = self._create_workflow(token, data, workflow_file_path, class_name)

        workflow_full_dto = self.retrieve_existing_workflow(token, workflow_id)

        state_maps = self._create_mapping(workflow_full_dto, 'states')
        criteria_maps = self._retrieve_existing_criteria(token, class_name)
        process_maps = self._retrieve_existing_processes(token, class_name)

        self._update_criteria(token, workflow_id, data, criteria_maps['id_map'], class_name)
        self._update_processes(token, workflow_id, data, process_maps['id_map'], class_name)
        self._update_states(token, workflow_id, data, state_maps['id_map'], class_name)
        self._update_transitions(token, data, state_maps['id_map'], criteria_maps['id_map'], process_maps['id_map'],
                                 workflow_id, class_name)

        return workflow_id

    def _create_workflow(self, token, data, file_path, class_name):
        """Create a new workflow by posting data from a JSON file."""
        workflow_data = read_json_file(file_path)
        workflow_data.update({"name": data["name"], "entityClassName": class_name})
        response = send_post_request(token, API_URL, "platform-api/statemachine/persisted/workflows",
                                     json.dumps(workflow_data))
        self._check_response(response, "POST")
        return response.json()['id']

    def save_workflow(self, token, workflow_dto, workflow_id):
        response = send_post_request(token, API_URL, "platform-api/statemachine/import?needRewrite=true",
                                     json=workflow_dto)
        self._check_response(response, "POST")
        if response.content:
            return response.json()
        else:
            return f"Workflow {workflow_id} was updated."

    def retrieve_existing_workflow(self, token, workflow_id):
        """Retrieve existing workflowDto"""
        response = send_get_request(token, API_URL,
                                    f"platform-api/statemachine/export?includeIds={workflow_id}")
        self._check_response(response, "GET")
        return response.json()

    def _retrieve_existing_states(self, token, workflow_id):
        """Retrieve and map existing states for a workflow."""
        response = send_get_request(token, API_URL,
                                    f"platform-api/statemachine/persisted/workflows/{workflow_id}/states")
        self._check_response(response, "GET")
        return self._create_mapping(response.json(), 'Data')

    def _retrieve_existing_criteria(self, token, class_name):
        """Retrieve and map existing criteria."""
        response = send_get_request(token, API_URL, f"platform-api/statemachine/criteria?entityClassName={class_name}")
        self._check_response(response, "GET")
        return self._create_mapping(response.json())

    def _retrieve_existing_processes(self, token, class_name):
        """Retrieve and map existing processes."""
        response = send_get_request(token, API_URL, f"platform-api/statemachine/processes?entityClassName={class_name}")
        self._check_response(response, "GET")
        return self._create_mapping(response.json())

    def _create_mapping(self, data, key=''):
        """Create a mapping of names to descriptions and IDs."""
        if isinstance(data, dict) and key:
            items = data.get(key, [])
        else:
            items = data if isinstance(data, list) else []
        description_map = {item['name']: item['description'] for item in items}
        id_map = {item['name']: item['id'] for item in items}
        id_map['None'] = "noneState"
        return {'description_map': description_map, 'id_map': id_map}

    def _update_states(self, token, workflow_id, data, existing_state_id_map, class_name):
        """Update states based on provided transitions."""
        states = {item['end_state']: item.get('end_state_description', '') for item in data['transitions']}
        empty_transition_id = self._create_empty_transition(token, workflow_id, class_name)
        state_template = read_json_file(f"{WORK_DIR}/data/v1/workflows/state.json")

        for name, description in states.items():
            if name not in existing_state_id_map:
                state_template.update({"name": name, "description": description, "entityClassName": class_name})
                response = send_post_request(token, API_URL,
                                             f"platform-api/statemachine/persisted/workflows/{workflow_id}/transitions/{empty_transition_id}/states",
                                             json.dumps(state_template))
                self._check_response(response, "POST")
                existing_state_id_map[name] = response.json()["Data"]["id"]

        send_delete_request(token, API_URL,
                            f"platform-api/statemachine/persisted/workflows/{workflow_id}/transitions/{empty_transition_id}")

    def _update_criteria(self, token, workflow_id, data, existing_criteria_id_map, class_name):
        """Update criteria based on provided transitions."""
        criteria = {item['criteria']['name']: item['criteria']['description'] for item in data['transitions'] if
                    'criteria' in item}
        criteria_template = read_json_file(f"{WORK_DIR}/data/v1/workflows/criteria.json")

        for name, description in criteria.items():
            if name not in existing_criteria_id_map:
                criteria_template.update({"name": name, "description": description, "entityClassName": class_name})
                response = send_post_request(token, API_URL, "platform-api/statemachine/persisted/criteria",
                                             json.dumps(criteria_template))
                self._check_response(response, "POST")
                existing_criteria_id_map[name] = response.json()["id"]

    def _update_processes(self, token, workflow_id, data, existing_process_id_map, class_name):
        """Update processes based on provided transitions."""
        processes = {item['process']['name']: item['process']['description'] for item in data['transitions'] if
                     'process' in item}
        process_template = read_json_file(f"{WORK_DIR}/data/v1/workflows/process.json")

        for name, description in processes.items():
            if name not in existing_process_id_map:
                process_template.update({"name": name, "description": description, "entityClassName": class_name})
                for param in process_template['parameters']:
                    if param['name'] == "Tags for filtering calculation nodes (separated by ',' or ';')":
                        param['value']['value'] = data['name']
                response = send_post_request(token, API_URL, "platform-api/statemachine/persisted/processes",
                                             json.dumps(process_template))
                self._check_response(response, "POST")
                existing_process_id_map[name] = response.json()["id"]

    def _update_transitions(self, token, data, existing_state_id_map, existing_criteria_id_map, existing_process_id_map,
                            workflow_id, class_name):
        """Update transitions based on provided data."""
        transition_template = read_json_file(f"{WORK_DIR}/data/v1/workflows/transition.json")
        save_transition_path = f"platform-api/statemachine/persisted/workflows/{workflow_id}/transitions"

        for item in data['transitions']:
            transition_template.update({
                'name': item['name'],
                'entityClassName': class_name,
                'description': item['description'],
                'startStateId': existing_state_id_map[item['start_state']],
                'endStateId': existing_state_id_map[item['end_state']],
                'workflowId': workflow_id,
                'criteriaIds': [existing_criteria_id_map.get(item['criteria']['name'])] if 'criteria' in item else [],
                'endProcessesIds': [existing_process_id_map.get(item['process']['name'])] if 'process' in item else []
            })
            response = send_post_request(token, API_URL, save_transition_path, json.dumps(transition_template))
            self._check_response(response, "POST")

    def _create_empty_transition(self, token, workflow_id, class_name):
        """Create an empty transition to use as a placeholder."""
        transition_data = read_json_file(f"{WORK_DIR}/data/v1/workflows/initial_transition.json")
        transition_data.update({"workflowId": workflow_id, "entityClassName": class_name})
        response = send_post_request(token, API_URL,
                                     f"platform-api/statemachine/persisted/workflows/{workflow_id}/transitions",
                                     json.dumps(transition_data))
        self._check_response(response, "POST")
        return response.json()['Data']['id']

    def _check_response(self, response, method):
        """Check the HTTP response status and log errors if needed."""
        if response.status_code // 100 != 2:
            logger.error(f"{method} request failed with status code {response.status_code}")
            logger.error(f"Response: {response.json()}")
            response.raise_for_status()
