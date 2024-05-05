from dataclasses import dataclass

@dataclass
class InitialMappingRequestDTO:
    """Data Transfer Object for initial mapping request."""
    chat_id: str
    entity: str
    ds_input: str

@dataclass
class ChatMappingRequestDTO:
    """Data Transfer Object for chat mapping request."""
    chat_id: str
    question: str
    user_script: str
    return_object: str