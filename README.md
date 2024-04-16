# cyoda-ai-chat
A Django-based chat application leveraging AI for enhanced user interaction with Cyoda

pip install -r requirements.txt 
docker build -t chat_app .    
docker run -p 31179:8000 chat_app
python3 manage.py migrate
python3 manage.py runserver 

=======
curl -X GET 'http://localhost:8000/api/return-data'

curl -X GET 'http://localhost:8000/api/mappings-chat-clear?id=9bcfef68-fdfc-4468-a0a1-21b2804d560b'

{"message":"Chat mapping with id 9bcfef68-fdfc-4468-a0a1-21b2804d560b cleared."}

curl -X POST -H "Content-Type: application/json" -d '{"id":"9bcfef68-fdfc-4468-a0a1-21b2804d560b", "entity": "net.cyoda.saas.model.TenderEntity", "input":"{\"id\":\"1\",\"date\":\"2019-07-16\",\"deadline_date\":\"2019-07-25\",\"deadline_length_days\":\"9\",\"title\":\"SustitucindeduchasdelosbaosdelpasilloCyDdelaResidenciaJuvenilBaltasarGracian\",\"category\":\"constructions\",\"sid\":\"3996914\",\"src_url\":\"https\",\"src_final_url\":\"https\",\"awarded_value\":\"20252.00\",\"awarded_currency\":\"EUR\",\"purchaser\":{\"id\":\"1\",\"sid\":null,\"name\":null},\"type\":{\"id\":\"minor-contract\",\"name\":\"Minorcontract\",\"slug\":\"minor-contract\"},\"notices\":[{\"id\":null,\"sid\":null,\"date\":\"2019-08-30\",\"type\":{},\"src_id\":null,\"src_url\":null,\"data\":{\"date\":\"2019-08-30\",\"type\":\"AnunciodeAdjudicacin\"},\"sections\":[]},{\"id\":null,\"sid\":null,\"date\":\"2019-07-16\",\"type\":{},\"src_id\":null,\"src_url\":null,\"data\":{\"date\":\"2019-07-16\",\"type\":\"AnunciodeLicitacin\"},\"sections\":[]}],\"awarded\":[{\"date\":\"2019-08-07\",\"suppliers_id\":\"1\",\"count\":\"1\",\"value\":\"20252.00\",\"suppliers_name\":\"GESTIMAX,GestinyServicios,S.L.\",\"suppliers\":[{\"id\":\"1\",\"slug\":\"gestimax-gestion-y-servicios-s-l\",\"name\":\"GESTIMAX,GestinyServicios,S.L.\"}],\"offers_count\":2,\"offers_count_data\":{\"2\":{\"count\":1,\"value\":\"20252.00\"}},\"value_for_one\":0,\"value_for_two\":20252,\"value_for_three\":20252}]}"}' http://localhost:8000/api/mappings-initial



curl -X GET 'http://localhost:8000/api/mappings-script?id=9bcfef68-fdfc-4468-a0a1-21b2804d560b'

{"script":{"body":"entity.setName(input.name);\nentity.setContactUser(input.contactUser);\nentity.setSystemAccount(input.systemAccount);\nentity.setDate(input.date);\nentity.setDeadlineDate(input.deadlineDate);\nentity.setDeadlineLengthDays(input.deadlineLengthDays);\nentity.setCategory(input.category);\nentity.setAwardedValue(input.awardedValue);\nentity.setPurchaser(input.purchaser);","inputSrcPaths":["name","contactUser","systemAccount","date","deadlineDate","deadlineLengthDays","category","awardedValue","purchaser"]}}  

curl -X POST -H "Content-Type: application/json" -d '{"id":"9bcfef68-fdfc-4468-a0a1-21b2804d560b", "question": "how to write a loop in js", "return_object":"random"}' http://localhost:8000/api/mappings-ai-chat

{"answer":"To write a loop in JavaScript, you can use either the \"for\" loop or the \"while\" loop. Here are examples of both:\n\n1. \"for\" loop:\n```javascript\nfor (var i = 0; i < 5; i++) {\n  console.log(i);\n}\n```\nThis loop will iterate from 0 to 4, and for each iteration, it will print the value of \"i\" to the console.\n\n2. \"while\" loop:\n```javascript\nvar i = 0;\nwhile (i < 5) {\n  console.log(i);\n  i++;\n}\n```\nThis loop will also iterate from 0 to 4, and for each iteration, it will print the value of \"i\" to the console. The difference is that the condition is checked before each iteration.\n\nYou can modify the loop parameters based on your specific requirements."}%    


curl -X POST -H "Content-Type: application/json" -d '{"id":"9bcfef68-fdfc-4468-a0a1-21b2804d560b", "question": "Edit the script - if notices date is null the default date is 12-01-01. Do not return any comments just the code", "return_object":"code"}' http://localhost:8000/api/mappings-ai-chat
{"answer":"```javascript\nvar notices = [];\nvar Notice = Java.type('net.cyoda.saas.model.Notice');\n\nfor (var i = 0; i < input.notices.length; i++) {\n    var notice = new Notice();\n    notice.setId(input.notices[i].id != null ? input.notices[i].id : 0);\n    notice.setDate(input.notices[i].date != null ? input.notices[i].date : \"12-01-01\");\n    notice.setType(input.notices[i].type != null ? input.notices[i].type : \"Unknown type\");\n    notices.push(notice);\n}\n\nentity.setNotices(notices);\n```"}

curl -X POST -H "Content-Type: application/json" -d '{"id":"9bcfef68-fdfc-4468-a0a1-21b2804d560b", "question": "Edit the script - if notices date is null the default date is 12-01-01.", "return_object":"script"}' http://localhost:8000/api/mappings-ai-chat

{"script":{"body":"var notices = [];\nvar Notice = Java.type('net.cyoda.saas.model.Notice');\n\nfor (var i = 0; i < input.notices.length; i++) {\n    var notice = new Notice();\n    notice.setId(input.notices[i].id != null ? input.notices[i].id : 0);\n    notice.setDate(input.notices[i].date != null ? input.notices[i].date : \"12-01-01\");\n    notice.setType(input.notices[i].type != null ? input.notices[i].type : \"Unknown type\");\n    notices.push(notice);\n}\n\nentity.setNotices(notices);\n","inputSrcPaths":["notices/*/name","notices/*/id","notices/*/sid","notices/*/date","notices/*/type","notices/*/srcId","notices/*/srcUrl","notices/*/data"]}}


curl -X POST -H "Content-Type: application/json" -d '{"id":"9bcfef68-fdfc-4468-a0a1-21b2804d560b", "question": "Add column mapping from deadline_date to deadlineDate.", "return_object":"columns"}' http://localhost:8000/api/mappings-ai-chat

{"column":{"srcColumnPath":"deadline_date","dstCyodaColumnPath":"deadlineDate","dstCyodaColumnPathType":"java.lang.String","dstCollectionElementSetModes":[],"transformer":{"type":"COMPOSITE","children":[]}},"action":"add"}

curl -X POST -H "Content-Type: application/json" -d '{"id":"9bcfef68-fdfc-4468-a0a1-21b2804d560b", "question": "Delete column mapping from deadline_date to deadlineDate.", "return_object":"columns"}' http://localhost:8000/api/mappings-ai-chat

{"column":{"srcColumnPath":"deadline_date","dstCyodaColumnPath":"deadlineDate","dstCyodaColumnPathType":"java.lang.String","dstCollectionElementSetModes":[],"transformer":{"type":"COMPOSITE","children":[]}},"action":"delete"}