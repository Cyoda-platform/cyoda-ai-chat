import logging
from typing import List, Dict
from connections.logic.interactor import ConnectionsInteractor
from connections.logic.ingestion_service import DataIngestionService
from common_utils.utils import get_env_var
from .entity_tools import token_store
from workflows.logic.processor import WorkflowProcessor

logger = logging.getLogger("django")
connectionsInteractor = ConnectionsInteractor()
rag_processor = WorkflowProcessor()
ingestion_service = DataIngestionService()

class DataIngestionTools:

    def __init__(self):
        logger.info("Initializing RagProcessor v1...")

    def add_connection(self, entity, config_prompt_key, ds_id_key, operation_key):
        """Function to add a connection."""
        logger.info(entity)
        chat_id = entity["chat_id"]
        question = entity[config_prompt_key]
        response = connectionsInteractor.handle_import_connection(
            token_store[chat_id], chat_id, question
        )
        if response['success']:
            datasource_id = response["datasource_id"]
            operation_ai_result = rag_processor.ask_question(
                chat_id, f"The user has asked to create the connection configuration with the following instruction '{question}'. Please extract the value for the endpoint name specified by the user (or operation name, which is equivalent). Return only the name which i can propagate as a parameter. No more additional text or comments."
            )
            entity[ds_id_key] = datasource_id
            entity[operation_key] = operation_ai_result
            return entity
        raise Exception

    def add_connection_for_data_model(self, entity):
        """Function to add a connection for a data model."""
        return self.add_connection(
            entity,
            "schema_data_config_prompt",
            "schema_data_ds_id",
            "schema_data_operation",
        )

    def add_connection_for_data_agg_model(self, entity):
        """Function to add a connection for a data aggregation model."""
        return self.add_connection(
            entity,
            "schema_data_agg_config_prompt",
            "schema_data_agg_ds_id",
            "schema_data_agg_operation",
        )

    def add_connection_for_data(self, entity):
        """Function to add a connection for data."""
        return self.add_connection(
            entity,
            "data_ingestion_config_prompt",
            "ingestion_data_ds_id",
            "ingestion_data_operation",
        )

    def import_schema(self, entity, ds_id_key, operation_key, entity_name, schema_flag):
        """Function to import a schema."""
        chat_id = entity["chat_id"]
        request_data = {
            "ds_id": entity[ds_id_key],
            "operation": entity[operation_key],
            "schema_flag": schema_flag,
            "data_format": entity["dataFormat"],
            "entity_name": entity_name,
            "model_version": entity["modelVersion"],
            "entity_type": entity["entityType"],
        }
        ingestion_service.ingest_data(token_store[chat_id], request_data)
        return entity

    def import_data_model_schema(self, entity):
        """Function to import a data model schema."""
        return self.import_schema(
            entity, "schema_data_ds_id", "schema_data_operation", entity["entityName"], "true"
        )

    def import_data_model_agg_schema(self, entity):
        """Function to import a data aggregation model schema."""
        return self.import_schema(
            entity, "schema_data_agg_ds_id", "schema_data_agg_operation", f"{entity["entityName"]}_agg", "true"
        )

    def import_data(self, entity):
        """Function to import data."""
        return self.import_schema(
            entity, "ingestion_data_ds_id", "ingestion_data_operation", entity["entityName"], "false"
        )

    def notify_success(self, entity):
        """Function to notify success."""
        logger.info("THE DATA HAS BEEN INGESTED")
        return entity
