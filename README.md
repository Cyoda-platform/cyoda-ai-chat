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
python3 manage.py runserver
```

## Usage

Once the application is running, you can interact with it using the following API endpoints:

### Endpoint 1: Return Data

```bash
curl -X GET 'http://localhost:8000/api/return-data'
```

### Endpoint 2: Clear Chat Mapping

```bash
curl -X GET 'http://localhost:8000/api/mappings-chat-clear?id=9bcfef68-fdfc-4468-a0a1-21b2804d560b'
```

### Endpoint 3: Initial Mapping

```bash
curl -X POST -H "Content-Type: application/json" -d '{"id":"9bcfef68-fdfc-4468-a0a1-21b2804d560b", "entity": "net.cyoda.saas.model.TenderEntity", "input":"..."}' http://localhost:8000/api/mappings-initial
```

### Endpoint 4: Get Script

```bash
curl -X GET 'http://localhost:8000/api/mappings-script?id=9bcfef68-fdfc-4468-a0a1-21b2804d560b'
```

### Endpoint 5: AI Chat

```bash
curl -X POST -H "Content-Type: application/json" -d '{"id":"9bcfef68-fdfc-4468-a0a1-21b2804d560b", "question": "how to write a loop in js", "return_object":"random"}' http://localhost:8000/api/mappings-ai-chat
```

### Endpoint 6: Edit Script

```bash
curl -X POST -H "Content-Type: application/json" -d '{"id":"9bcfef68-fdfc-4468-a0a1-21b2804d560b", "question": "Edit the script - if notices date is null the default date is 12-01-01. Do not return any comments just the code", "return_object":"code"}' http://localhost:8000/api/mappings-ai-chat
```

### Endpoint 7: Edit Script with Comments

```bash
curl -X POST -H "Content-Type: application/json" -d '{"id":"9bcfef68-fdfc-4468-a0a1-21b2804d560b", "question": "Edit the script - if notices date is null the default date is 12-01-01.", "return_object":"script"}' http://localhost:8000/api/mappings-ai-chat
```

Replace `"..."` with the actual JSON input data for the `mappings-initial` endpoint.

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