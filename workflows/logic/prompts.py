from enum import Enum


class Keys(Enum):
    GENERATE_WORKFLOW_FROM_IMAGE = "workflow-from-image"
    GENERATE_WORKFLOW_FROM_URL = "workflow-from-url"
    GENERATE_WORKFLOW= "workflow"
    # GENERATE_TRANSITION = "transitions"
    SOURCES = "sources"
    SAVE_WORKFLOW = "save"
    RANDOM = "random"


RETURN_DATA = {
    Keys.GENERATE_WORKFLOW_FROM_IMAGE.value: "Generate a workflow JSON from an attached image",
    Keys.GENERATE_WORKFLOW_FROM_URL.value: "Generate a workflow JSON from an image URL",
    Keys.GENERATE_WORKFLOW.value: "Generate a workflow JSON from a text description",
    Keys.SOURCES.value: "Add sources from a URL to the knowledge base",
    Keys.SAVE_WORKFLOW.value: "Save the workflow from a JSON message",
    Keys.RANDOM.value: "Get a free-form response from the chatbot"
}


WORKFLOWS_DEFAULT_PROMPTS = []