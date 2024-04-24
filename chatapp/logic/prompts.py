RETURN_DATA = {
    "mapping": "Return only json array of column mappings.",
    "script": 'Return ONLY javascript nashorn "script" json object which contains body with javascript code and inputSrcPaths inside "script" attribute.. Remove any leading text',
    "code": "Return JavaScript Nashorn code only that can be used for code autocomplete. Remove any leading text. Return code only i.e. the contents of script body.",
    "random": "",
    "autocomplete": "Return only the relevant code for autocomplete. Do not return all code, just a few lines of code that answer the exact question - this is just autocomplete.",
    "columns": 'Return only column mapping json object which contains srcColumnPath and etc inside "column" attribute. Add to this json one more attribute "action" with the value either add or delete depending on the question. Return inside an array',
    "transformers": "Return a relevant transformerKey for this column mapping from the list of available transformers. Return only transformerKey WITHOUT any other text.",
}

MAPPINGS_INITIAL_PROMPT = "Produce a list of column mappings from input to this target entity. Input: {}. Target Entity: {}. Do NOT add mappings for lists or arrays. If a column is not present in net.cyoda.saas.model.TenderEntity remove it. Use slash for src Return json array of column mappings."

RESPONSE_TEMPLATE = {
    "@bean": "com.cyoda.plugins.mapping.core.dtos.DataMappingConfigDto",
    "id": "ef7bf900-00b3-11ef-b006-ba4744165259",
    "name": "test",
    "lastUpdated": 1713795828907,
    "dataType": "JSON",
    "description": "",
    "entityMappings": [
        {
            "id": {"id": "ef79fd30-00b3-11ef-b006-ba4744165259"},
            "name": "test",
            "entityClass": "net.cyoda.saas.model.TenderEntity",
            "entityRelationConfigs": [{"srcRelativeRootPath": "root:/"}],
            "columns": [],  # Initialize the columns list
            "functionalMappings": [],
            "columnPathsForUniqueCheck": [],
            "metadata": [],
            "cobiCoreMetadata": [],
            "script": {},
            "entityFilter": {
                "@bean": "com.cyoda.core.conditions.GroupCondition",
                "operator": "AND",
                "conditions": [],
            },
        }
    ],
}



SCRIPT_GEN_PROMPT = "Write a JavaScript Nashorn script to map the given input to the given entity. Use the instruction. Return only JavaScript Nashorn script."
SCRIPT_REFINE_PROMPT = "Provide a list of inputSrcPaths for this script. Write correct inputSrcPaths with a forward slash and wildcard if applicable. Return a json array."
