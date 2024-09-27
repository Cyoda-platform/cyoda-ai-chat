from enum import Enum

class Keys(Enum):
    CHAT = "chat"
    #GEN_QUERY = "generate-query"
    RUN_QUERY = "run-query"

RETURN_DATA = {
    Keys.CHAT.value: "",
    #Keys.GEN_QUERY.value: "",
    Keys.RUN_QUERY.value: ""
}
