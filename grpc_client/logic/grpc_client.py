import logging
import grpc
import json
import asyncio
import uuid
from common_utils.utils import get_env_var
import cloudevents_pb2 as cloudevents_pb2
import cloudevents_pb2_grpc as cloudevents_pb2_grpc
import cyoda_cloud_api_pb2 as cyoda_cloud_api_pb2
import cyoda_cloud_api_pb2_grpc as cyoda_cloud_api_pb2_grpc
from workflows.tools.data_ingestion_tools import DataIngestionTools

GRPC_ADDRESS = get_env_var("GRPC_ADDRESS")

logger = logging.getLogger('django')
data_ingestion_tools = DataIngestionTools()
from enum import Enum

class CloudEventType(str, Enum):
    BASE_EVENT = "BaseEvent"
    CALCULATION_MEMBER_JOIN_EVENT = "CalculationMemberJoinEvent"
    CALCULATION_MEMBER_GREET_EVENT = "CalculationMemberGreetEvent"
    ENTITY_PROCESSOR_CALCULATION_REQUEST = "EntityProcessorCalculationRequest"
    ENTITY_PROCESSOR_CALCULATION_RESPONSE = "EntityProcessorCalculationResponse" 
    
class GRPCClient:

    def __init__(self):
        logger.info("Initializing GRPCClient v1...")
        
    @classmethod
    async def create(cls):
        instance = cls()
        await instance.start_grpc_client()
        return instance
        

    def create_cloud_event(self, event_id, source, event_type, data) -> cloudevents_pb2.CloudEvent:
        return cloudevents_pb2.CloudEvent(
            id=event_id,
            source=source,
            spec_version="1.0",
            type=event_type,
            text_data=json.dumps(data)
        )

    def get_notification(self, data) -> cloudevents_pb2.CloudEvent:
        return self.create_cloud_event(
            event_id=str(uuid.uuid1),
            source="GenAIWorkflow",
            event_type="EntityProcessorCalculationResponse",
            data={
                "requestId": data['requestId'],
                "entityId": data['entityId'],
                "owner": "PLAY",
                "payload": data['payload'],
                "success": True
            }
        )
        

    async def event_producer(self, queue):
        cloud_event = self.create_cloud_event(
            event_id=str(uuid.uuid1),
            source="GenAIWorkflow",
            event_type="CalculationMemberJoinEvent",
            data={"owner": "PLAY", "tags": ["ingest_data_with_aggregation_entity"]}
        )

        await queue.put(cloud_event)

    async def event_consumer(self, queue):
        async with grpc.aio.secure_channel(GRPC_ADDRESS, grpc.ssl_channel_credentials()) as channel:
            stub = cyoda_cloud_api_pb2_grpc.CloudEventsServiceStub(channel)

            async def generate_events():
                while True:
                    event = await queue.get()
                    if event is None:
                        break
                    yield event
                    queue.task_done()

            async for response in stub.startStreaming(generate_events()):
                logger.info(response)
                data = json.loads(response.text_data)
                if 'processorName' in data:
                    cloud_event = self.process_data(data)
                    await queue.put(cloud_event)

    async def start_grpc_client(self):
        queue = asyncio.Queue()
        producer = self.event_producer(queue)
        consumer = self.event_consumer(queue)
        await asyncio.gather(producer, consumer)
        
    def process_data(self, data):
        if 'processorName' in data and data['processorName'] == 'add_connection_for_data_model':
            ##ai logic
            logger.info("add_connection_for_data_model")
            entity = data['payload']['data']
            data_ingestion_tools.add_connection_for_data_model(entity)
            
        elif 'processorName' in data and data['processorName'] == 'import_data_model_schema':
            logger.info("import_data_model_schema")
            entity = data['payload']['data']
            data_ingestion_tools.import_data_model_schema(entity)
            
        elif 'processorName' in data and data['processorName'] == 'add_connection_for_data_agg_model':
            ##ai logic
            logger.info("add_connection_for_data_agg_model")
            entity = data['payload']['data']
            data_ingestion_tools.add_connection_for_data_agg_model(entity)
            
        elif 'processorName' in data and data['processorName'] == 'import_data_model_agg_schema':
            ##ai logic
            logger.info("import_data_model_agg_schema")
            entity = data['payload']['data']
            data_ingestion_tools.import_data_model_agg_schema(entity)
            
        elif 'processorName' in data and data['processorName'] == 'add_connection_for_data':
            ##ai logic
            logger.info("add_connection_for_data")
            entity = data['payload']['data']
            data_ingestion_tools.add_connection_for_data(entity)
            
        elif 'processorName' in data and data['processorName'] == 'import_data':
            ##ai logic
            logger.info("import_data")
            entity = data['payload']['data']
            data_ingestion_tools.import_data(entity)
            
        elif 'processorName' in data and data['processorName'] == 'notify_success':
            ##ai logic
            logger.info("notify_success")
            entity = data['payload']['data']
            data_ingestion_tools.notify_success(entity)
            
        cloud_event = self.get_notification(data)
        return cloud_event