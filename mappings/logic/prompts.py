from enum import Enum


class Keys(Enum):
    SCRIPT = "script"
    CODE = "code"
    RANDOM = "random"
    AUTOCOMPLETE = "autocomplete"
    COLUMNS = "columns"
    TRANSFORMERS = "transformers"
    SOURCES = "sources"


RETURN_DATA = {
    Keys.SCRIPT.value: 'Base your answer on the available list_of_input_to_entity_properties. Remove any leading text',
    Keys.CODE.value: "Base your answer on the available list_of_input_to_entity_properties.",
    Keys.RANDOM.value: "",
    Keys.AUTOCOMPLETE.value: "Return only the relevant code for autocomplete.",
    Keys.COLUMNS.value: 'Return only column mapping json object which contains srcColumnPath and etc inside "column" attribute. Add to this json one more attribute "action" with the value either add or delete depending on the question. Return inside an array. Remove any leading text',
    Keys.TRANSFORMERS.value: "Return a relevant transformerKey for this column mapping from the list of available transformers. Return only transformerKey WITHOUT any other text.",
    Keys.SOURCES.value: "",
}

MAPPINGS_INITIAL_PROMPT = "Input: {}. Target Entity: {}. What is the structure of the {}? What are the input attributes? How do does input correspond to the entity? Which attributes can be mapped from the input to the entity. Return json array in the form of [src_json_path:dst_json_path]. Use your common knowledge and semantic analysis."
#MAPPINGS_INITIAL_ADD_ENTITY = "Remember this {} entity json schema: {}."
MAPPINGS_INITIAL_PROMPT_SCRIPT = "Fill in Mappings Questionnaire json based on the input: {} and target entity model {}. Return the resulting Questionnaire json."

MAPPINGS_DEFAULT_PROMPTS = [
    'analyze the script and add all missing inputSrcPaths (they should be available for all input attributes used in the script). Use slash "/" for the jsonpath.',
    "Write a JavaScript Nashorn script to map the given input to the given Cyoda target entity based on Instruction e31a2c74-4c85-4c3b-b0ab-3b0cd7a9fe58",
]

SCRIPT_REFINE_PROMPT = "Provide a list of inputSrcPaths for this script. Write correct inputSrcPaths with a forward slash and wildcard if applicable. Return a json array."
