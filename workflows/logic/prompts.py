from enum import Enum


class Keys(Enum):
    GENERATE_WORKFLOW_FROM_IMAGE = "workflow-from-image"
    GENERATE_WORKFLOW_FROM_URL = "workflow-from-url"
    GENERATE_WORKFLOW= "workflow"
    GENERATE_TRANSITION = "transitions"
    SOURCES = "sources"
    SAVE_WORKFLOW = "save"
    RANDOM = "random"


RETURN_DATA = {
    Keys.GENERATE_WORKFLOW_FROM_IMAGE.value: "",
    Keys.GENERATE_WORKFLOW_FROM_URL.value: "",
    Keys.GENERATE_TRANSITION.value: "",
    Keys.GENERATE_WORKFLOW.value: "",
    Keys.SOURCES.value: "",
    Keys.SAVE_WORKFLOW.value: "",
    Keys.RANDOM.value: ""
}

WORKFLOWS_DEFAULT_PROMPTS = []