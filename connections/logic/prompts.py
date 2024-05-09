RETURN_DATA = {
    "endpoints": "Return only resulting HttpEndpointDto json object. Remove any leading text. If you do not know something - just return empty json",
    "random": ""
}

INITIAL_API_ANALYSIS_PROMPT= "{}. Do you know this API? Get related documentation with 100 percent accuracy."
INITIAL_REQUEST_ANALYSIS_PROMPT= "Is {} POST or GET request? What is the structure of HttpEndpointDto.java object? What is the structure of HttpParameterDto.ParameterType object?"
INITIAL_PARAMETERS_ANALYSIS_PROMPT="What HttpParameterDto.ParameterType enum values do you know? Which ones are used for POST or GET? What  HttpParameterDto.ParameterType enum value should we use for {}? Why?"
INITIAL_API_PROMPT="{}. Do your best to map the api to HttpEndpointDto.java object with a list of HttpParameterDto parameters included. Specify query path according to the API documentstion."

COLLECTIONS_DEFAULT_PROMPTS=[
    "Write a curl request for this endpoint. Use parameters placeholders in the body, e.g. \"parameter_name\": \"${name}\"",
    "API: {}, endpoint: {}",
    "Add a request parameter \"date\". It should be a template parameter with a templateValue = velocity function to calculate current date."
]