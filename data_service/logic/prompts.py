from enum import Enum

class Keys(Enum):
    CHAT = "chat"
    RUN_QUERY = "run-query"

RETURN_DATA = {
    Keys.CHAT.value: "",
    Keys.RUN_QUERY.value: ""
}
