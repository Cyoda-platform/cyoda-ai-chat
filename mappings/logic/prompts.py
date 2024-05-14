RETURN_DATA = {
    "script": 'Return ONLY javascript nashorn "script" json object which contains body with javascript code and inputSrcPaths (remember p1/*/p2 template) inside "script" attribute. Remove any leading text',
    "code": "Return JavaScript Nashorn code only that can be used for code autocomplete. Remove any leading text. Return code only i.e. the contents of script body.",
    "random": "",
    "autocomplete": "Return only the relevant code for autocomplete. Do not return all code, just a few lines of code that answer the exact question - this is just autocomplete.",
    "columns": 'Return only column mapping json object which contains srcColumnPath and etc inside "column" attribute. Add to this json one more attribute "action" with the value either add or delete depending on the question. Return inside an array. Remove any leading text',
    "transformers": "Return a relevant transformerKey for this column mapping from the list of available transformers. Return only transformerKey WITHOUT any other text.",
}

#MAPPINGS_INITIAL_PROMPT = "Produce a list of column mappings from input to this target entity. Input: {}. Target Entity: {}. Do NOT add mappings for lists or arrays. If a column is not present in net.cyoda.saas.model.TenderEntity remove it. Use slash for src Return json array of column mappings."


MAPPINGS_INITIAL_PROMPT = "Input: {}. Target Entity: {}. What is the structure of the {}? What are the input attributes?"
MAPPINGS_INITIAL_RELATIONS_PROMPT = "How do does input correspond to the entity? Which attributes can be mapped from the input to the entity. Return json array in the form of [src_json_path:dst_json_path]. Use your common knowledge and semantic analysis."


MAPPINGS_INITIAL_PROMPT_COLUMNS = "How to produce column mappings for a target entity? Which transformers would you use for Integer dst?"
MAPPINGS_INITIAL_PROMPT_SCRIPT = "How to initialize Java objects according to the docs in javascript nashorn scripting? What are the cyoda rules of writing inputSrcPaths for arrays, e.g. should you use p1/*/p2 pattern? When should inputSrcPaths equal p1/* and when p1/*/p2?"

SCRIPT_GEN_PROMPT = "Write a JavaScript Nashorn script to map the given input to the given entity. Use the instruction. Return only JavaScript Nashorn script."
SCRIPT_REFINE_PROMPT = "Provide a list of inputSrcPaths for this script. Write correct inputSrcPaths with a forward slash and wildcard if applicable. Return a json array."

MAPPINGS_DEFAULT_PROMPTS=["analyze the script and add all missing inputSrcPaths (they should be available for all input attributes used in the script)"]