from dataclasses import dataclass, field
from typing import Optional, Dict
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
  
    
@dataclass
class DataSourceOperation:
    operation: str
    request_fields: Optional[Dict[str, str]] = field(default=None)
    clientData: Optional[Dict[str, str]] = field(default=None)


@dataclass
class ChatIngestDataRequestDTO:
    data_source_operations: Optional[list[DataSourceOperation]] = field(default=None)
    datasource_id: Optional[str] = field(default=None)
    dataFormat: Optional[str] = field(default=None)
    entityType: Optional[str] = field(default=None)
    entityName: Optional[str] = field(default=None)
    modelVersion: Optional[str] = field(default=None)