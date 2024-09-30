from connections.logic.prompts import COLLECTIONS_DEFAULT_PROMPTS
from mappings.logic.prompts import MAPPINGS_DEFAULT_PROMPTS
from enum import Enum
#todo prompts - persistent

class PromptType(Enum):
    CONNECTIONS = "connections"
    MAPPINGS = "mappings"
    WORKFLOW = "workflow"


class PromptService:
    def __init__(self):
        self.prompts = {}
        # Initialize the 'connections' key with an empty dictionary and assign the 'default' value
        self.prompts[PromptType.CONNECTIONS.value] = {}
        self.prompts[PromptType.CONNECTIONS.value][
            "default"
        ] = COLLECTIONS_DEFAULT_PROMPTS

        # Initialize the 'mappings' key with an empty dictionary and assign the 'default' value
        self.prompts[PromptType.MAPPINGS.value] = {}
        self.prompts[PromptType.MAPPINGS.value]["default"] = MAPPINGS_DEFAULT_PROMPTS

    def add_prompt(self, topic, user, prompt):
        if topic not in self.prompts:
            self.prompts[topic] = {}
        if user not in self.prompts[topic]:
            self.prompts[topic][user] = []
        self.prompts[topic][user].append(prompt)

    def delete_prompt(self, topic, user, index):
        if (
            topic in self.prompts
            and user in self.prompts[topic]
            and index < len(self.prompts[topic][user])
        ):
            del self.prompts[topic][user][index]

    def get_prompt(self, topic, user, index):
        return (
            self.prompts.get(topic, {}).get(user, [])[index]
            if index < len(self.prompts.get(topic, {}).get(user, []))
            else None
        )

    def get_prompts(self, topic, user):
        return self.prompts.get(topic, {}).get(user, [])

    def get_all_prompts(self):
        return self.prompts
