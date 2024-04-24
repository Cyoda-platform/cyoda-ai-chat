class InitialMappingRequestDTO:
    def __init__(self, chat_id, entity, ds_input):
        self.chat_id = chat_id
        self.entity = entity
        self.ds_input = ds_input
        
class ChatMappingRequestDTO:
    def __init__(self, chat_id, question, user_script, return_object):
        self.chat_id = chat_id
        self.question = question
        self.user_script = user_script
        self.return_object = return_object