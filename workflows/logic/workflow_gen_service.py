import logging
import json
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo
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

OPERATION_MAPPING = {
        "equals (disregard case)": {"operation": "IEQUALS", "@bean": "com.cyoda.core.conditions.nonqueryable.IEquals"},
        "not equal (disregard case)": {"operation": "INOT_EQUAL",
                                       "@bean": "com.cyoda.core.conditions.nonqueryable.INotEquals"},
        "between (inclusive)": {"operation": "BETWEEN", "@bean": "com.cyoda.core.conditions.queryable.Between"},
        "contains": {"operation": "CONTAINS", "@bean": "com.cyoda.core.conditions.nonqueryable.IContains"},
        "starts with": {"operation": "ISTARTS_WITH", "@bean": "com.cyoda.core.conditions.nonqueryable.IStartsWith"},
        "ends with": {"operation": "IENDS_WITH", "@bean": "com.cyoda.core.conditions.nonqueryable.IEndsWith"},
        "does not contain": {"operation": "INOT_CONTAINS",
                             "@bean": "com.cyoda.core.conditions.nonqueryable.INotContains"},
        "does not start with": {"operation": "INOT_STARTS_WITH",
                                "@bean": "com.cyoda.core.conditions.nonqueryable.INotStartsWith"},
        "does not end with": {"operation": "NOT_ENDS_WITH",
                              "@bean": "com.cyoda.core.conditions.nonqueryable.NotEndsWith"},
        "matches other field (case insensitive)": {"operation": "INOT_ENDS_WITH",
                                                   "@bean": "com.cyoda.core.conditions.nonqueryable.INotEndsWith"},
        "equals": {"operation": "EQUALS", "@bean": "com.cyoda.core.conditions.queryable.Equals"},
        "not equal": {"operation": "NOT_EQUAL", "@bean": "com.cyoda.core.conditions.nonqueryable.NotEquals"},
        "less than": {"operation": "LESS_THAN", "@bean": "com.cyoda.core.conditions.queryable.LessThan"},
        "greater than": {"operation": "GREATER_THAN", "@bean": "com.cyoda.core.conditions.queryable.GreaterThan"},
        "less than or equal to": {"operation": "LESS_OR_EQUAL",
                                  "@bean": "com.cyoda.core.conditions.queryable.LessThanEquals"},
        "greater than or equal to": {"operation": "GREATER_OR_EQUAL",
                                     "@bean": "com.cyoda.core.conditions.queryable.GreaterThanEquals"},
        "between (inclusive, match case)": {"operation": "BETWEEN_INCLUSIVE",
                                            "@bean": "com.cyoda.core.conditions.queryable.BetweenInclusive"},
        "is null": {"operation": "IS_NULL", "@bean": "com.cyoda.core.conditions.nonqueryable.IsNull"},
        "is not null": {"operation": "NOT_NULL", "@bean": "com.cyoda.core.conditions.nonqueryable.NotNull"}
    }


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

    def save_workflow(self, token, workflow_dto):
        response = send_post_request(token, API_URL, "platform-api/statemachine/import?needRewrite=true",
                                     json=workflow_dto)
        self._check_response(response, "POST")
        return workflow_dto["workflow"][0]["id"]


    def transform_condition(self, condition):
        """Transforms a condition based on the provided enums mapping."""
        if "conditions" in condition:  # Handle group conditions
            return {
                "@bean": "com.cyoda.core.conditions.GroupCondition",
                "operator": condition.get("group_condition_operator", "AND"),
                "conditions": [self.transform_condition(sub_condition) for sub_condition in condition["conditions"]],
            }

        operation_label = condition.get("operation")
        mapping = OPERATION_MAPPING.get(operation_label)

        if not mapping:
            raise ValueError(f"Unsupported operation: {operation_label}")

        is_range = "BETWEEN" in mapping["operation"]
        is_meta_field = condition["is_meta_field"]

        # Determine the appropriate fieldName
        if not is_meta_field:
            field_name_prefix = "members.[*]@com#cyoda#tdb#model#treenode#NodeInfo.value@com#cyoda#tdb#model#treenode#PersistedValueMaps."
            fieldName = f"{field_name_prefix}{condition['value_type']}.[{condition['field_name']}]"
        else:
            fieldName = condition["field_name"]

        base_condition = {
            "@bean": mapping["@bean"],
            "fieldName": fieldName,
            "operation": mapping["operation"],
            "rangeField": str(is_range).lower(),
        }

        def parse_value(value):
            try:
                # Try converting to float
                return float(value)
            except (ValueError, TypeError):
                # Leave non-numeric values as-is
                return value

        # Add value if not disabled by "is null" or similar
        if "value" in condition and mapping["operation"] not in {"IS_NULL", "NOT_NULL"}:
            base_condition["value"] = parse_value(condition["value"])

        # Special handling for "does not start with" operation
        if condition.get("operation").lower() == "does not start with":
            base_condition["iStartsWith"] = {
                "@bean": "com.cyoda.core.conditions.nonqueryable.IStartsWith",
                "fieldName": condition["field_name"],
                "operation": "ISTARTS_WITH",
                "rangeField": "false",
                "value": parse_value(condition["value"])
            }

        return base_condition

    def transform_conditions(self, input_conditions):
        """Transforms the entire conditions list."""
        return [self.transform_condition(cond) for cond in input_conditions]

    def get_existing_state_id(self, state_name, dto):
        for state in dto["states"]:
            if state["name"] == state_name:
                return state["id"]
        return None

    def generate_id(self):
        return str(uuid.uuid1())

    def current_timestamp(self):
        now = datetime.now(ZoneInfo("UTC"))
        return now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + now.strftime("%z")[:3] + ":" + now.strftime("%z")[3:]

    def generate_ext_criteria_params(self, criteria):
        criteria_params = [
            {
                "persisted": True,
                "owner": "CYODA",
                "id": self.generate_id(),
                "name": "Tags for filtering calculation nodes (separated by ',' or ';')",
                "creationDate": self.current_timestamp(),
                "valueType": "STRING",
                "value": {
                    "@type": "String",
                    "value": criteria["calculation_nodes_tags"]
                }
            },
            {
                "persisted": True,
                "owner": "CYODA",
                "id": self.generate_id(),
                "name": "Attach entity",
                "creationDate": self.current_timestamp(),
                "valueType": "STRING",
                "value": {
                    "@type": "String",
                    "value": str(criteria["attach_entity"]).lower()
                }
            },
            {
                "persisted": True,
                "owner": "CYODA",
                "id": self.generate_id(),
                "name": "Calculation response timeout (ms)",
                "creationDate": self.current_timestamp(),
                "valueType": "INTEGER",
                "value": {"@type": "String", "value": criteria["calculation_response_timeout_ms"]}
            },
            {
                "persisted": True,
                "owner": "CYODA",
                "id": self.generate_id(),
                "name": "Retry policy",
                "creationDate": self.current_timestamp(),
                "valueType": "STRING",
                "value": {"@type": "String", "value": criteria["retry_policy"]}
            }
        ]
        return criteria_params

    def generate_ext_criteria(self, criteria, criteria_id, criteria_params, class_name):
        criteria_dto = {
                    "persisted": True,
                    "owner": "CYODA",
                    "id": criteria_id,
                    "name": criteria["name"],
                    "entityClassName": class_name,
                    "creationDate": self.current_timestamp(),
                    "description": criteria["description"],
                    "condition": {
                        "@bean": "com.cyoda.core.conditions.GroupCondition",
                        "operator": "AND",
                        "conditions": []
                    },
                    "aliasDefs": [],
                    "parameters": criteria_params,
                    "criteriaChecker": "ExternalizedCriteriaChecker",
                    "user": "CYODA"
                }
        return criteria_dto

    def parse_ai_to_cyoda_dto(self, input_json, class_name):
        dto = {
            "@bean": "com.cyoda.core.model.stateMachine.dto.FullWorkflowContainerDto",
            "workflow": [],
            "transitions": [],
            "criterias": [],
            "processes": [],
            "states": [],
            "processParams": []
        }

        # Map workflow
        workflow_id = self.generate_id()
        dto["workflow"].append({
            "persisted": True,
            "owner": "CYODA",
            "id": workflow_id,
            "name": input_json["name"],
            "entityClassName": class_name,
            "creationDate": self.current_timestamp(),
            "description": input_json.get("description", ""),
            "entityShortClassName": "TreeNodeEntity",
            "transitionIds": [],
            "criteriaIds": [],
            "stateIds": ["noneState"],
            "active": False,
            "useDecisionTree": False,
            "decisionTrees": [],
            "metaData": {"documentLink": ""}
        })

        # Process workflow's externalized_criteria
        workflow_criteria_ids = []

        for criteria in input_json["workflow_criteria"]["externalized_criteria"]:
            criteria_id = self.generate_id()
            workflow_criteria_ids.append(criteria_id)
            criteria_params = self.generate_ext_criteria_params(criteria)
            dto["processParams"].extend(criteria_params)
            criteria_dto = self.generate_ext_criteria(criteria, criteria_id, criteria_params, class_name)
            dto["criterias"].append(criteria_dto)

        # Process workflow's condition_criteria
        for criteria in input_json["workflow_criteria"]["condition_criteria"]:
            criteria_id = self.generate_id()
            workflow_criteria_ids.append(criteria_id)
            dto["criterias"].append({
                "persisted": True,
                "owner": "CYODA",
                "id": criteria_id,
                "name": criteria["name"],
                "entityClassName": class_name,
                "creationDate": self.current_timestamp(),
                "description": criteria["description"],
                "condition": {
                    "@bean": "com.cyoda.core.conditions.GroupCondition",
                    "operator": criteria["condition"]["group_condition_operator"],
                    "conditions": self.transform_conditions(criteria["condition"]["conditions"])
                },
                "aliasDefs": [],
                "parameters": [],
                "criteriaChecker": "ConditionCriteriaChecker",
                "user": "CYODA"
            })

        dto["workflow"][0]["criteriaIds"].extend(workflow_criteria_ids)

        # Process transitions
        for transition in input_json["transitions"]:
            transition_id = self.generate_id()
            process_ids = []
            criteria_ids = []

            # Process transition's externalized_criteria
            for criteria in transition["transition_criteria"]["externalized_criteria"]:
                criteria_id = self.generate_id()
                criteria_ids.append(criteria_id)
                criteria_params = self.generate_ext_criteria_params(criteria)
                dto["processParams"].extend(criteria_params)
                criteria_dto = self.generate_ext_criteria(criteria, criteria_id, criteria_params, class_name)
                dto["criterias"].append(criteria_dto)

            # Process transition's condition_criteria
            for criteria in transition["transition_criteria"]["condition_criteria"]:
                criteria_id = self.generate_id()
                criteria_ids.append(criteria_id)
                dto["criterias"].append({
                    "persisted": True,
                    "owner": "CYODA",
                    "id": criteria_id,
                    "name": criteria["name"],
                    "entityClassName": class_name,
                    "creationDate": self.current_timestamp(),
                    "description": criteria["description"],
                    "condition": {
                        "@bean": "com.cyoda.core.conditions.GroupCondition",
                        "operator": criteria["condition"]["group_condition_operator"],
                        "conditions": self.transform_conditions(criteria["condition"]["conditions"])
                    },
                    "aliasDefs": [],
                    "parameters": [],
                    "criteriaChecker": "ConditionCriteriaChecker",
                    "user": "CYODA"
                })

            # Process externalized_processor
            for process in transition["processes"]["externalized_processors"]:
                process_id = self.generate_id()
                process_ids.append(
                    {
                        "persisted": True,
                        "persistedId": process_id,
                        "runtimeId": 0
                    }
                )

                process_params = [
                        {
                            "persisted": True,
                            "owner": "CYODA",
                            "id": self.generate_id(),
                            "name": "Tags for filtering calculation nodes (separated by ',' or ';')",
                            "creationDate": self.current_timestamp(),
                            "valueType": "STRING",
                            "value": {
                                "@type": "String",
                                "value": process["calculation_nodes_tags"]
                            }
                        },
                        {
                            "persisted": True,
                            "owner": "CYODA",
                            "id": self.generate_id(),
                            "name": "Attach entity",
                            "creationDate": self.current_timestamp(),
                            "valueType": "STRING",
                            "value": {
                                "@type": "String",
                                "value": str(process["attach_entity"]).lower()
                            }
                        },
                        {
                            "persisted": True,
                            "owner": "CYODA",
                            "id": self.generate_id(),
                            "name": "Calculation response timeout (ms)",
                            "creationDate": self.current_timestamp(),
                            "valueType": "INTEGER",
                            "value": {"@type": "String", "value": str(process["calculation_response_timeout_ms"])}
                        },
                        {
                            "persisted": True,
                            "owner": "CYODA",
                            "id": self.generate_id(),
                            "name": "Retry policy",
                            "creationDate": self.current_timestamp(),
                            "valueType": "STRING",
                            "value": {"@type": "String", "value": process["retry_policy"]}
                        }
                    ]

                dto["processParams"].extend(process_params)

                # Process externalized_processor's externalized_criteria
                process_criteria_ids = []

                for criteria in process["processor_criteria"]["externalized_criteria"]:
                    criteria_id = self.generate_id()
                    process_criteria_ids.append(criteria_id)
                    criteria_params = self.generate_ext_criteria_params(criteria)
                    dto["processParams"].extend(criteria_params)
                    criteria_dto = self.generate_ext_criteria(criteria, criteria_id, criteria_params, class_name)
                    dto["criterias"].append(criteria_dto)

                # Process externalized_processor's condition_criteria
                for criteria in process["processor_criteria"]["condition_criteria"]:
                    criteria_id = self.generate_id()
                    process_criteria_ids.append(criteria_id)
                    dto["criterias"].append({
                        "persisted": True,
                        "owner": "CYODA",
                        "id": criteria_id,
                        "name": criteria["name"],
                        "entityClassName": class_name,
                        "creationDate": self.current_timestamp(),
                        "description": criteria["description"],
                        "condition": {
                            "@bean": "com.cyoda.core.conditions.GroupCondition",
                            "operator": criteria["condition"]["group_condition_operator"],
                            "conditions": self.transform_conditions(criteria["condition"]["conditions"])
                        },
                        "aliasDefs": [],
                        "parameters": [],
                        "criteriaChecker": "ConditionCriteriaChecker",
                        "user": "CYODA"
                    })

                # Process externalized_processor's dto
                dto["processes"].append({
                    "persisted": True,
                    "owner": "CYODA",
                    "id": {
                        "@bean": "com.cyoda.core.model.stateMachine.dto.ProcessIdDto",
                        "persisted": True,
                        "persistedId": process_id,
                        "runtimeId": 0
                    },
                    "name": process["name"],
                    "entityClassName": class_name,
                    "creationDate": self.current_timestamp(),
                    "description": process["description"],
                    "processorClassName": "net.cyoda.saas.externalize.processor.ExternalizedProcessor",
                    "parameters": process_params,
                    "fields": [],
                    "syncProcess": process["sync_process"],
                    "newTransactionForAsync": process["new_transaction_for_async"],
                    "noneTransactionalForAsync": process["none_transactional_for_async"],
                    "isTemplate": False,
                    "criteriaIds": process_criteria_ids,
                    "user": "CYODA"
                })

            # Process schedule_transition_processor
            for process in transition["processes"]["schedule_transition_processors"]:
                process_id = self.generate_id()
                process_ids.append(
                    {
                        "persisted": True,
                        "persistedId": process_id,
                        "runtimeId": 0
                    }
                )

                process_params = [
                    {
                        "persisted": True,
                        "owner": "CYODA",
                        "id": self.generate_id(),
                        "name": "Delay (ms)",
                        "creationDate": self.current_timestamp(),
                        "valueType": "INTEGER",
                        "value": {
                            "@type": "String",
                            "value": str(process["delay_ms"])
                        }
                    },
                    {
                        "persisted": True,
                        "owner": "CYODA",
                        "id": self.generate_id(),
                        "name": "Timeout (ms)",
                        "creationDate": self.current_timestamp(),
                        "valueType": "INTEGER",
                        "value": {
                            "@type": "String",
                            "value": str(process["timeout_ms"])
                        }
                    },
                    {
                        "persisted": True,
                        "owner": "CYODA",
                        "id": self.generate_id(),
                        "name": "Transition name",
                        "creationDate": self.current_timestamp(),
                        "valueType": "STRING",
                        "value": {"@type": "String", "value": process["transition_name"]}
                    }
                ]

                dto["processParams"].extend(process_params)

                # Process schedule_transition_processor's externalized_criteria
                process_criteria_ids = []

                for criteria in process["processor_criteria"]["externalized_criteria"]:
                    criteria_id = self.generate_id()
                    process_criteria_ids.append(criteria_id)
                    criteria_params = self.generate_ext_criteria_params(criteria)
                    dto["processParams"].extend(criteria_params)
                    criteria_dto = self.generate_ext_criteria(criteria, criteria_id, criteria_params, class_name)
                    dto["criterias"].append(criteria_dto)

                # Process schedule_transition_processor's condition_criteria
                for criteria in process["processor_criteria"]["condition_criteria"]:
                    criteria_id = self.generate_id()
                    process_criteria_ids.append(criteria_id)
                    dto["criterias"].append({
                        "persisted": True,
                        "owner": "CYODA",
                        "id": criteria_id,
                        "name": criteria["name"],
                        "entityClassName": class_name,
                        "creationDate": self.current_timestamp(),
                        "description": criteria["description"],
                        "condition": {
                            "@bean": "com.cyoda.core.conditions.GroupCondition",
                            "operator": criteria["condition"]["group_condition_operator"],
                            "conditions": self.transform_conditions(criteria["condition"]["conditions"])
                        },
                        "aliasDefs": [],
                        "parameters": [],
                        "criteriaChecker": "ConditionCriteriaChecker",
                        "user": "CYODA"
                    })

                # Process schedule_transition_processor's dto
                dto["processes"].append({
                    "persisted": True,
                    "owner": "CYODA",
                    "id": {
                        "@bean": "com.cyoda.core.model.stateMachine.dto.ProcessIdDto",
                        "persisted": True,
                        "persistedId": process_id,
                        "runtimeId": 0
                    },
                    "name": process["name"],
                    "entityClassName": class_name,
                    "creationDate": self.current_timestamp(),
                    "description": process["description"],
                    "processorClassName": "com.cyoda.plugins.cobi.processors.statemachine.ScheduleTransitionProcessor",
                    "parameters": process_params,
                    "fields": [],
                    "syncProcess": process["sync_process"],
                    "newTransactionForAsync": process["new_transaction_for_async"],
                    "noneTransactionalForAsync": process["none_transactional_for_async"],
                    "isTemplate": False,
                    "criteriaIds": process_criteria_ids,
                    "user": "CYODA"
                })

            # Process states
            start_state_id = "noneState"
            end_state_id = ""

            # Create a list to hold the new states
            new_states = []

            # Add start_state only if it is not "None"
            if transition["start_state"] != "None":
                start_state_id = self.get_existing_state_id(transition["start_state"], dto)

                if not start_state_id:
                    start_state_id = self.generate_id()
                    new_states.append({
                        "persisted": True,
                        "owner": "CYODA",
                        "id": start_state_id,
                        "name": transition["start_state"],
                        "entityClassName": class_name,
                        "creationDate": self.current_timestamp(),
                        "description": transition["start_state_description"]
                    })
            else:
                new_states.append({
                    "persisted": True,
                    "owner": "CYODA",
                    "id": start_state_id,
                    "name": "None",
                    "entityClassName": class_name,
                    "creationDate": self.current_timestamp(),
                    "description": "Initial state of the workflow."
                })

            # Add end_state
            end_state_id = self.get_existing_state_id(transition["end_state"], dto)
            if not end_state_id:
                end_state_id = self.generate_id()
                new_states.append({
                    "persisted": True,
                    "owner": "CYODA",
                    "id": end_state_id,
                    "name": transition["end_state"],
                    "entityClassName": class_name,
                    "creationDate": self.current_timestamp(),
                    "description": transition["end_state_description"]
                })

            # Extend the dto["states"] with the new states
            dto["states"].extend(new_states)

            # Process transitions
            dto["transitions"].append({
                "persisted": True,
                "owner": "CYODA",
                "id": transition_id,
                "name": transition["name"],
                "entityClassName": class_name,
                "creationDate": self.current_timestamp(),
                "description": transition["description"],
                "startStateId": start_state_id,
                "endStateId": end_state_id,
                "workflowId": workflow_id,
                "criteriaIds": criteria_ids,
                "endProcessesIds": process_ids,
                "active": True,
                "automated": transition["automated"],
                "logActivity": False
            })

            dto["workflow"][0]["transitionIds"].append(transition_id)

        return dto

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
