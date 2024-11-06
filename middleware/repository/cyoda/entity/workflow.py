import inspect

from middleware.repository.cyoda.entity.cache_entity import workflow as cache_workflow
from middleware.repository.cyoda.entity.chat_history_entity import workflow as chat_workflow


process_dispatch = {
}

def build_process_dispatch(workflow_module):
    """Builds a dictionary of public functions from the given workflow module."""
    return {
        name: func
        for name, func in inspect.getmembers(workflow_module, inspect.isfunction)
        if not name.startswith("_")  # Filter out private functions
    }

def process_event(token, data, processor_name):
    meta = {"token": token, "entity_model": "ENTITY_PROCESSED_NAME", "entity_version": "ENTITY_VERSION"}
    # data = data['payload']['data']
    if processor_name in process_dispatch:
        response = process_dispatch[processor_name](meta, data)
    else:
        raise ValueError(f"Unknown processing step: {processor_name}")
    return response

cache_process_dispatch = build_process_dispatch(cache_workflow)
chat_process_dispatch = build_process_dispatch(chat_workflow)


