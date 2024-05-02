# Cyoda AI Chat Application

This document provides a step-by-step guide to setting up and running the Cyoda AI Chat application, which is a Django-based chat application leveraging AI for enhanced user interaction with Cyoda.

## Prerequisites

Before you begin, ensure you have the following:

- Python 3.10 or higher
- Docker
- Git

## Installation

Follow these steps to install and run the Cyoda AI Chat application:

1. Clone the repository:

```bash
git clone https://github.com/your-repo/cyoda-ai-chat.git
cd cyoda-ai-chat
```

2. Install the required Python packages:

```bash
pip install -r requirements.txt
```

3. Build the Docker image:

```bash
docker build -t chat_app .
```

4. Run the Docker container:

```bash
docker run -p 31179:8000 chat_app
```

5. Apply database migrations:

```bash
python3 manage.py migrate
```

6. Start the Django development server:

```bash
find . | grep -E "(/__pycache__$|\.pyc$|\.pyo$)" | xargs rm -rf
python3 manage.py runserver
```

## Usage

Once the application is running, you can interact with it using the following API endpoints:

## Mappings

### Endpoint 1: Return Data

```bash
curl -X GET 'http://localhost:8000/api/v1/mappings/return-data'
```

### Endpoint 2: Clear Chat Mapping

```bash
curl -X GET 'http://localhost:8000/api/v1/mappings/chat-clear?id=9bcfef68-fdfc-4468-a0a1-21b2804d560b'
```

### Endpoint 3: Initial Mapping

```bash
curl -X POST -H "Content-Type: application/json" -d '{"id":"9bcfef68-fdfc-4468-a0a1-21b2804d560b", "entity": "net.cyoda.saas.model.TenderEntity", "input":"{\"id\":\"1\",\"date\":\"2019-07-16\",\"deadline_date\":\"2019-07-25\",\"deadline_length_days\":\"9\",\"title\":\"SustitucindeduchasdelosbaosdelpasilloCyDdelaResidenciaJuvenilBaltasarGracian\",\"category\":\"constructions\",\"sid\":\"3996914\",\"src_url\":\"https\",\"src_final_url\":\"https\",\"awarded_value\":\"20252.00\",\"awarded_currency\":\"EUR\",\"purchaser\":{\"id\":\"1\",\"sid\":null,\"name\":null},\"type\":{\"id\":\"minor-contract\",\"name\":\"Minorcontract\",\"slug\":\"minor-contract\"},\"notices\":[{\"id\":null,\"sid\":null,\"date\":\"2019-08-30\",\"type\":{},\"src_id\":null,\"src_url\":null,\"data\":{\"date\":\"2019-08-30\",\"type\":\"AnunciodeAdjudicacin\"},\"sections\":[]},{\"id\":null,\"sid\":null,\"date\":\"2019-07-16\",\"type\":{},\"src_id\":null,\"src_url\":null,\"data\":{\"date\":\"2019-07-16\",\"type\":\"AnunciodeLicitacin\"},\"sections\":[]}],\"awarded\":[{\"date\":\"2019-08-07\",\"suppliers_id\":\"1\",\"count\":\"1\",\"value\":\"20252.00\",\"suppliers_name\":\"GESTIMAX,GestinyServicios,S.L.\",\"suppliers\":[{\"id\":\"1\",\"slug\":\"gestimax-gestion-y-servicios-s-l\",\"name\":\"GESTIMAX,GestinyServicios,S.L.\"}],\"offers_count\":2,\"offers_count_data\":{\"2\":{\"count\":1,\"value\":\"20252.00\"}},\"value_for_one\":0,\"value_for_two\":20252,\"value_for_three\":20252}]}"}' http://localhost:8000/api/v1/mappings/initial
```

```json
{"@bean":"com.cyoda.plugins.mapping.core.dtos.DataMappingConfigDto","id":"c784c270-f0fe-11ee-9561-ee157423307a","name":"tender","lastUpdated":1712069164720,"dataType":"JSON","description":"","entityMappings":[{"id":{"id":"c77e59d0-f0fe-11ee-9561-ee157423307a"},"name":"tender","entityClass":"net.cyoda.saas.model.TenderEntity","entityRelationConfigs":[{"srcRelativeRootPath":"root:/"}],"columns":[{"srcColumnPath":"date","dstCyodaColumnPath":"date","dstCyodaColumnPathType":"java.lang.String","dstCollectionElementSetModes":[],"transformer":{"type":"COMPOSITE","children":[]}},{"srcColumnPath":"deadline_date","dstCyodaColumnPath":"deadlineDate","dstCyodaColumnPathType":"java.lang.String","dstCollectionElementSetModes":[],"transformer":{"type":"COMPOSITE","children":[]}},{"srcColumnPath":"deadline_length_days","dstCyodaColumnPath":"deadlineLengthDays","dstCyodaColumnPathType":"java.lang.Integer","dstCollectionElementSetModes":[],"transformer":{"type":"COMPOSITE","children":[]}},{"srcColumnPath":"title","dstCyodaColumnPath":"name","dstCyodaColumnPathType":"java.lang.String","dstCollectionElementSetModes":[],"transformer":{"type":"COMPOSITE","children":[]}},{"srcColumnPath":"category","dstCyodaColumnPath":"category","dstCyodaColumnPathType":"java.lang.String","dstCollectionElementSetModes":[],"transformer":{"type":"COMPOSITE","children":[]}},{"srcColumnPath":"awarded_value","dstCyodaColumnPath":"awardedValue","dstCyodaColumnPathType":"java.lang.Double","dstCollectionElementSetModes":[],"transformer":{"type":"COMPOSITE","children":[]}}]}]}
```

### Endpoint 5: AI Chat

```bash
curl -X POST -H "Content-Type: application/json" -d '{"id":"9bcfef68-fdfc-4468-a0a1-21b2804d560b", "question": "how to write a loop in js", "return_object":"random"}' http://localhost:8000/api/v1/mappings/chat
```

```json
{"answer":"To write a loop in JavaScript, you can use the following constructs:\n\n1. For Loop:\n   The for loop is used to iterate a block of code a specific number of times.\n\n   Syntax:\n   ```javascript\n   for (initialization; condition; increment/decrement) {\n     // code to be executed\n   }\n   ```\n\n   Example:\n   ```javascript\n   for (var i = 0; i < 5; i++) {\n     console.log(i);\n   }\n   ```\n\n2. While Loop:\n   The while loop is used to execute a block of code as long as a specified condition is true.\n\n   Syntax:\n   ```javascript\n   while (condition) {\n     // code to be executed\n   }\n   ```\n\n   Example:\n   ```javascript\n   var i = 0;\n   while (i < 5) {\n     console.log(i);\n     i++;\n   }\n   ```\n\n3. Do...While Loop:\n   The do...while loop is similar to the while loop, but the condition is checked after executing the block of code. This means that the code will always be executed at least once.\n\n   Syntax:\n   ```javascript\n   do {\n     // code to be executed\n   } while (condition);\n   ```\n\n   Example:\n   ```javascript\n   var i = 0;\n   do {\n     console.log(i);\n     i++;\n   } while (i < 5);\n   ```\n\nThese are the basic loop constructs in JavaScript. You can choose the one that suits your specific use case."}
```

### Endpoint 6: Edit Code

```bash
curl -X POST -H "Content-Type: application/json" -d '{"id":"9bcfef68-fdfc-4468-a0a1-21b2804d560b", "question": "Edit the script - if notices date is null the default date is 12-01-01. Do not return any comments just the code", "return_object":"code"}' http://localhost:8000/api/v1/mappings/chat
```

```json
{"answer":"```javascript\nvar notices = [];\nvar Notice = Java.type('net.cyoda.saas.model.Notice');\n\n// Add notices from input\nfor (var i = 0; i < input.notices.length; i++) {\n    var notice = new Notice();\n    notice.setId(input.notices[i].id != null ? input.notices[i].id : 0);\n    notice.setDate(input.notices[i].date != null ? input.notices[i].date : \"12-01-01\");\n    notice.setType(input.notices[i].type != null ? input.notices[i].type : \"Unknown type\");\n    notices.push(notice);\n}\n\nentity.setNotices(notices);\n```"
```

### Endpoint 7: Edit Script

```bash
curl -X POST -H "Content-Type: application/json" -d '{"id":"9bcfef68-fdfc-4468-a0a1-21b2804d560b", "question": "Edit the script - if notices date is null the default date is 12-01-01.", "return_object":"script"}' http://localhost:8000/api/v1/mappings/chat
```

```json
{"script":{"body":"var notices = [];\nvar Notice = Java.type('net.cyoda.saas.model.Notice');\n\n// Add notices from input\nfor (var i = 0; i < input.notices.length; i++) {\n    var notice = new Notice();\n    notice.setId(input.notices[i].id != null ? input.notices[i].id : 0);\n    notice.setDate(input.notices[i].date != null ? input.notices[i].date : \"12-01-01\");\n    notice.setType(input.notices[i].type != null ? input.notices[i].type : \"Unknown type\");\n    notices.push(notice);\n}\nentity.setNotices(notices);\n","inputSrcPaths":["notices/*/name","notices/*/id","notices/*/sid","notices/*/date","notices/*/type","notices/*/srcId","notices/*/srcUrl","notices/*/data"]}}
```

### Endpoint 8: Edit column mappings

```bash
curl -X POST -H "Content-Type: application/json" -d '{"id":"9bcfef68-fdfc-4468-a0a1-21b2804d560b", "question": "Add column mapping for date", "return_object":"columns"}' http://localhost:8000/api/v1/mappings/chat
```

```json
{"column":{"srcColumnPath":"date","dstCyodaColumnPath":"date","dstCyodaColumnPathType":"java.lang.String","dstCollectionElementSetModes":[],"transformer":{"type":"COMPOSITE","children":[{"type":"SINGLE","transformerKey":"com.cyoda.plugins.mapping.core.parser.valuetransformers.SourceObjectValueTransformer$ToString","parameters":[]},{"type":"SINGLE","transformerKey":"com.cyoda.plugins.mapping.core.parser.valuetransformers.StringValueTransformer$Trim","parameters":[]}]}},"action":"add"}
```


## Connections:

### Endpoint 1: Return Data

```bash
curl -X GET 'http://localhost:8000/api/v1/connections/return-data'
```


### Endpoint 2: Clear Chat Mapping

```bash
curl -X GET 'http://localhost:8000/api/v1/connections/chat-clear?id=9bcfef68-fdfc-4468-a0a1-21b2804d560b'
```
### Endpoint 3: AI Chat

```bash
curl -X POST -H "Content-Type: application/json" -d '{"id":"9bcfef68-fdfc-4468-a0a1-21b2804d560b", "question": "write an endpoint for cats", "return_object":"endpoints"}' http://localhost:8000/api/v1/connections/chat
```

```json
{"@bean":"com.cyoda.plugins.datasource.dtos.endpoint.HttpEndpointDto","chainings":[],"operation":"facts","cache":{"parameters":[],"ttl":0},"connectionIndex":0,"type":"test","query":"/facts","method":"GET","parameters":[],"bodyTemplate":"","connectionTimeout":300,"readWriteTimeout":300}
```

## Prompts library

List of topics: mappings, connections, workflows
```
GET /prompts/<topic>/<user>/: Returns all prompts for a user in a topic.

GET /prompts/<topic>/<user>/<index>/: Returns a specific prompt for a user in a topic.

POST /prompts/<topic>/<user>/: Adds a new prompt for a user in a topic.

DELETE /prompts/<topic>/<user>/<index>/: Deletes a specific prompt for a user in a topic.
```

- Add a new prompt:

```bash
curl -X POST -H "Content-Type: application/json" -d '{"prompt": "1"}' http://localhost:8000/api/v1/prompts/topic1/userA/
```

- Get all prompts for a user in a topic:

```bash
curl -X GET http://localhost:8000/api/v1/prompts/topic1/userA/
```

- Get a specific prompt for a user in a topic:

```bash
curl -X GET http://localhost:8000/api/v1/prompts/topic1/userA/0/
```

- Delete a specific prompt for a user in a topic:

```bash
curl -X DELETE http://localhost:8000/api/v1/prompts/topic1/userA/0/
```


## Troubleshooting

If you encounter any issues, please check the application logs for error messages. If the problem persists, please contact the support team.

## Contributing

If you'd like to contribute to the project, please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes and commit them with clear messages.
4. Push your changes to your fork.
5. Submit a pull request detailing your changes.

## License

This project is licensed under the [Apache License 2.0](https://github.com/Cyoda-platform/cyoda-ai-chat/blob/main/LICENSE).