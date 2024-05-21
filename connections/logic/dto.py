from dataclasses import dataclass, field
from typing import Optional


@dataclass
class InitialConnectionRequestDTO:
    id: str
    ds_doc: str


@dataclass
class ChatConnectionRequestDTO:
    id: str
    return_object: str
    question: str
    user_endpoint: Optional[str] = field(default=None)
