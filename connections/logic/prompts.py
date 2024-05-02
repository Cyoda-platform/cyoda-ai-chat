RETURN_DATA = {
    "endpoints": "Return only resulting HttpEndpointDto json object. Remove any leading text. If you do not know something - just return empty json",
    "random": ""
}
INITIAL_REQUEST_ANALYSIS_PROMPT= "Is {} POST or GET request? What is the structure of HttpEndpointDto.java object? What is the structure of HttpParameterDto.ParameterType object?"
INITIAL_PARAMETERS_ANALYSIS_PROMPT="What HttpParameterDto.ParameterType enum values do you know? Which ones are used for POST or GET? What  HttpParameterDto.ParameterType enum value should we use for {}? Why?"
INITIAL_API_PROMPT="{}. Do your best to map the api to HttpEndpointDto.java object with a list of HttpParameterDto parameters included. Use HttpParameterDto.ParameterType that you have already decided to use if it is a correct choice."



