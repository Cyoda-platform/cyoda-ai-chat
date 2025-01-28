import logging

import grpc
import uuid
import json
import asyncio
from cloudevents_pb2 import CloudEvent
from common_utils import config
from common_utils.config import CYODA_GRPC_PROCESSOR_TAG
from cyoda_cloud_api_pb2_grpc import CloudEventsServiceStub
from middleware.repository.cyoda.entity.workflow import process_dispatch, process_event

# These tags are configured in the workflow UI for external processor
TAGS = [CYODA_GRPC_PROCESSOR_TAG]
OWNER = "PLAY"
SPEC_VERSION = "1.0"
SOURCE = "SimpleSample"
JOIN_EVENT_TYPE = "CalculationMemberJoinEvent"
CALC_RESP_EVENT_TYPE = "EntityProcessorCalculationResponse"
CALC_REQ_EVENT_TYPE = "EntityProcessorCalculationRequest"
GREET_EVENT_TYPE = "CalculationMemberGreetEvent"
KEEP_ALIVE_EVENT_TYPE = "CalculationMemberKeepAliveEvent"
EVENT_ACK_TYPE = "EventAckResponse"
EVENT_ID_FORMAT = "{uuid}"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_cloud_event(event_id: str, source: str, event_type: str, data: dict) -> CloudEvent:
    """
    Create a CloudEvent instance with the given parameters.

    :param event_id: Unique identifier for the event.
    :param source: Source of the event.
    :param event_type: Type of the event.
    :param data: Data associated with the event.
    :return: A CloudEvent instance.
    """
    return CloudEvent(
        id=event_id,
        source=source,
        spec_version=SPEC_VERSION,
        type=event_type,
        text_data=json.dumps(data)
    )


def create_join_event() -> CloudEvent:
    """
    Create a CloudEvent for a member join event.

    :return: A CloudEvent instance for the join event.
    """
    return create_cloud_event(
        event_id=str(uuid.uuid4()),
        source=SOURCE,
        event_type=JOIN_EVENT_TYPE,
        data={"owner": OWNER, "tags": TAGS}
    )


def create_notification_event(data: dict) -> CloudEvent:
    """
    Create a CloudEvent for a notification response.

    :param data: Data from the notification response.
    :return: A CloudEvent instance for the notification event.
    """
    return create_cloud_event(
        event_id=str(uuid.uuid4()),
        source=SOURCE,
        event_type=CALC_RESP_EVENT_TYPE,
        data={
            "requestId": data.get('requestId'),
            "entityId": data.get('entityId'),
            "owner": OWNER,
            "payload": data.get('payload'),
            "success": True
        }
    )


async def event_generator(queue: asyncio.Queue):
    """
    Generate and yield events including initial and follow-up events.

    :param queue: Async queue to get events from.
    :yield: CloudEvent instances.
    """
    # Yield the initial join event
    yield create_join_event()
    while True:
        event = await queue.get()
        if event is None:
            break
        yield event
        queue.task_done()


# Utility function to set up gRPC credentials
def get_grpc_credentials(token: str):
    """
    Create gRPC credentials using the provided token.

    :param token: Authentication token for the gRPC service.
    :return: Composite credentials for secure gRPC communication.
    """
    auth_creds = grpc.access_token_call_credentials(token)
    return grpc.composite_channel_credentials(grpc.ssl_channel_credentials(), auth_creds)


# Function to handle greeting response
def handle_greet_event():
    """
    Handle the GREET_EVENT_TYPE response.

    :param response: gRPC response containing the event details.
    """
    logger.info("handle_greet_event:")


async def handle_keep_alive_event(response, queue: asyncio.Queue):
    logger.debug(f"handle_keep_alive_event: {response}")
    data = json.loads(response.text_data)
    event = create_cloud_event(
        event_id=str(uuid.uuid4()),
        source=SOURCE,
        event_type=EVENT_ACK_TYPE,
        data={
            "sourceEventId": data.get('id'),
            "owner": OWNER,
            "payload": None,
            "success": True
        })
    await queue.put(event)


# Function to process notification data and create the notification event
async def process_calc_req_event(token, data: dict, queue: asyncio.Queue):
    """
    Process notification data and create a notification event to be added to the event queue.

    :param data: The notification data received from the response.
    :param queue: The asyncio queue for event processing.
    """
    processor_name = data.get('processorName')

    try:
        # Process the first or subsequent versions of the entity
        if processor_name in process_dispatch:
            logger.info(f"Processing notification data: {data}")
            process_event(token, data, processor_name)

    except Exception as e:
        logger.error(e)
    #Create notification event and put it in the queue
    notification_event = create_notification_event(data)
    await queue.put(notification_event)


# Function to handle finish_workflow processor
async def handle_finish_workflow(data: dict, queue: asyncio.Queue):
    """
    Handle the 'finish_workflow' processorName and signal the end of the stream.

    :param data: Data from the response.
    :param queue: Event queue to place the notification event and signal end of stream.
    """
    notification_event = create_notification_event(data)
    await queue.put(notification_event)
    # await queue.put(None)  # Signal the end of the stream


# Main function to consume the gRPC stream
async def consume_stream(token):
    """
    Handle bi-directional streaming with response-driven event generation.
    """
    credentials = get_grpc_credentials(token)
    queue = asyncio.Queue()

    async with grpc.aio.secure_channel(config.CYODA_GRPC_ADDRESS, credentials) as channel:
        stub = CloudEventsServiceStub(channel)
        call = stub.startStreaming(event_generator(queue))

        async for response in call:
            logger.info(f"Received response: {response}")

            if response.type == GREET_EVENT_TYPE:
                handle_greet_event()
            elif response.type == KEEP_ALIVE_EVENT_TYPE:
                await handle_keep_alive_event(response, queue)
            elif response.type == CALC_REQ_EVENT_TYPE:
                logger.info(f"Received calc request: {response}")
                # Parse response data
                data = json.loads(response.text_data)
                processor_name = data.get('processorName')

                if processor_name in process_dispatch:
                    await process_calc_req_event(token, data, queue)
                elif processor_name == "finish_workflow":
                    await handle_finish_workflow(data, queue)
            else:
                logger.debug(response)


async def grpc_stream(token):
    try:
        while True:
            await consume_stream(token)
            logger.info("Working...")
    except asyncio.CancelledError:
        logger.info("consume_stream was cancelled")
        raise
