from enum import Enum


class Keys(Enum):
    CONNECTIONS = "connections"
    ENDPOINTS = "endpoints"
    PARAMETERS = "parameters"
    SOURCES = "sources"
    RANDOM = "random"
    IMPORT_CONNECTION = "import-connections"


RETURN_DATA = {
    Keys.ENDPOINTS.value: "Return only resulting HttpEndpointDto json object. Remove any leading text. If you do not know something - just return empty json.",
    Keys.PARAMETERS.value: "Return only resulting HttpParameterDto-s. Include only parameters asked for, not all parameters. Remove any leading text. If you do not know something - just return empty json.",
    Keys.SOURCES.value: "",
    Keys.RANDOM.value: "",
}

INITIAL_API_ANALYSIS_PROMPT = "{}. Do you know this API? Print all the parameters for this API. How would you represent it as HttpEndpointDto json object?"
INITIAL_API_PROMPT = "Return `HttpEndpointDto` representation for this endpoint."
COLLECTIONS_DEFAULT_PROMPTS = [
    'Write a curl request for this endpoint. Use parameters placeholders in the body, e.g. "parameter_name": "${name}"',
    "API: {}, endpoint: {}",
    'Add a request parameter "date". It should be a template parameter with a templateValue = velocity function to calculate current date.',
]
# INITIAL_API_ANALYSIS_PROMPT= "{}. Do you know this API? Get related documentation with the list of all parameters. Check the structure of HttpEndpointDto.java and HttpParameterDto.ParameterType java objects."
# INITIAL_REQUEST_ANALYSIS_PROMPT= "Is {} POST or GET request? What is the structure of HttpEndpointDto.java object? What is the structure of HttpParameterDto.ParameterType object?"
# INITIAL_PARAMETERS_ANALYSIS_PROMPT = "What HttpParameterDto.ParameterType enum values do you know? Which ones are used for POST or GET? What  HttpParameterDto.ParameterType enum value should we use for {}? Why?"
