from dataclasses import dataclass

@dataclass
class InitialConnectionRequestDTO:
    chat_id: str
    ds_doc: str

@dataclass
class ChatConnectionRequestDTO:
    chat_id: str
    user_endpoint: str
    return_object: str
    question: str
