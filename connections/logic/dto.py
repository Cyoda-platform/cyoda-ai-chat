class InitialConnectionRequestDTO:
    def __init__(self, chat_id, ds_doc):
        self.chat_id = chat_id
        self.ds_doc = ds_doc
        
class ChatMappingRequestDTO:
    def __init__(self, chat_id, user_endpoint, question, return_object):
        self.chat_id = chat_id
        self.question = question
        self.user_endpoint = user_endpoint
        self.return_object = return_object