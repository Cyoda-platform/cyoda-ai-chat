from dataclasses import dataclass


@dataclass
class InitialMappingRequestDTO:
    """Data Transfer Object for initial mapping request."""

    id: str
    entity: str
    input: str


@dataclass
class ChatMappingRequestDTO:
    """Data Transfer Object for chat mapping request."""

    id: str
    question: str
    user_script: str
    return_object: str
