class PromptService:
    def __init__(self):
        self.prompts = {}

    def add_prompt(self, topic, user, prompt):
        if topic not in self.prompts:
            self.prompts[topic] = {}
        if user not in self.prompts[topic]:
            self.prompts[topic][user] = []
        self.prompts[topic][user].append(prompt)

    def delete_prompt(self, topic, user, index):
        if topic in self.prompts and user in self.prompts[topic] and index < len(self.prompts[topic][user]):
            del self.prompts[topic][user][index]

    def get_prompt(self, topic, user, index):
        return self.prompts.get(topic, {}).get(user, [])[index] if index < len(self.prompts.get(topic, {}).get(user, [])) else None

    def get_prompts(self, topic, user):
        return self.prompts.get(topic, {}).get(user, [])

    def get_all_prompts(self):
        return self.prompts