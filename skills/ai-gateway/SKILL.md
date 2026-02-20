---
name: domino-ai-gateway
description: Access external LLM providers through Domino AI Gateway - a secure proxy with centralized API key management, usage monitoring, and compliance. Supports OpenAI, AWS Bedrock, Azure OpenAI, Anthropic, and more. Use when calling LLMs from Domino, configuring AI Gateway endpoints, or monitoring LLM usage and costs.
---

# Domino AI Gateway Skill

## Description
This skill helps users work with Domino AI Gateway - a secure proxy for accessing external Large Language Model (LLM) providers with centralized management, monitoring, and compliance.

## Activation
Activate this skill when users want to:
- Access LLM providers (OpenAI, AWS Bedrock, etc.) in Domino
- Configure AI Gateway endpoints
- Monitor LLM usage and costs
- Understand secure API key management
- Use LLMs in workspaces and jobs

## What is AI Gateway?

Domino AI Gateway provides:
- **Secure LLM Access**: Proxy to external LLM providers
- **Centralized API Keys**: Keys stored securely, never exposed to users
- **Usage Monitoring**: Track all LLM interactions
- **Access Control**: Granular permissions per endpoint
- **Audit Logging**: Compliance-ready logs

## Supported LLM Providers

| Provider | Models |
|----------|--------|
| OpenAI | GPT-4, GPT-4 Turbo, GPT-3.5 |
| AWS Bedrock | Claude, Titan, Llama 2 |
| Azure OpenAI | GPT-4, GPT-3.5 |
| Anthropic | Claude 3, Claude 2 |
| Google Vertex AI | PaLM, Gemini |
| Cohere | Command, Embed |

## Creating an AI Gateway Endpoint

### Via Domino UI
1. Go to **Endpoints** > **Gateway LLMs**
2. Click **Create Endpoint**
3. Configure:
   - **Name**: Endpoint name (e.g., `openai-gpt4`)
   - **Provider**: Select LLM provider
   - **Model**: Specific model to use
   - **API Key**: Provider API key (stored securely)
   - **Access**: Who can use this endpoint
4. Click **Create**

### Via API
```python
# Create endpoint via Domino API
import requests

response = requests.post(
    "https://your-domino.com/api/aigateway/v1/endpoints",
    headers={"X-Domino-Api-Key": "YOUR_API_KEY"},
    json={
        "name": "openai-gpt4",
        "provider": "openai",
        "model": "gpt-4",
        "providerApiKey": "sk-..."
    }
)
```

## Using AI Gateway in Code

### OpenAI-Compatible Interface
AI Gateway provides an OpenAI-compatible interface:

```python
from openai import OpenAI

# Configure client to use AI Gateway
client = OpenAI(
    api_key="not-needed",  # Handled by AI Gateway
    base_url="https://your-domino.com/api/aigateway/v1/openai"
)

# Use like standard OpenAI
response = client.chat.completions.create(
    model="openai-gpt4",  # Your endpoint name
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ]
)

print(response.choices[0].message.content)
```

### With LangChain
```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="openai-gpt4",  # Endpoint name
    openai_api_key="not-needed",
    openai_api_base="https://your-domino.com/api/aigateway/v1/openai"
)

response = llm.invoke("What is machine learning?")
print(response.content)
```

### Direct API Call
```python
import requests

response = requests.post(
    "https://your-domino.com/api/aigateway/v1/chat/completions",
    headers={
        "Content-Type": "application/json",
        "X-Domino-Api-Key": "YOUR_DOMINO_API_KEY"
    },
    json={
        "model": "openai-gpt4",
        "messages": [{"role": "user", "content": "Hello!"}]
    }
)

result = response.json()
print(result["choices"][0]["message"]["content"])
```

## Access Control

### Endpoint Permissions
Configure who can use each endpoint:
- **Everyone**: All Domino users
- **Specific Users**: Named individuals
- **Organizations**: Specific Domino organizations

### Setting Permissions
1. Go to endpoint settings
2. Click **Access Control**
3. Add users or organizations
4. Save changes

## Monitoring and Logging

### View Usage
1. Go to **Endpoints** > **Gateway LLMs**
2. Click on endpoint name
3. View metrics:
   - Request count
   - Token usage
   - Response times
   - Error rates

### Download Logs
```bash
# Via UI: Endpoints > Gateway LLMs > Download logs

# Logs include:
# - Timestamp
# - User
# - Model
# - Input/Output tokens
# - Response time
# - Status
```

### Log Format
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "user": "user@company.com",
  "endpoint": "openai-gpt4",
  "model": "gpt-4",
  "inputTokens": 150,
  "outputTokens": 200,
  "durationMs": 1500,
  "status": "success"
}
```

## Cost Management

### Track Costs
AI Gateway tracks token usage per:
- User
- Project
- Endpoint
- Time period

### Set Limits (Admin)
Admins can configure:
- Token limits per user/project
- Request rate limits
- Cost alerts

## Best Practices

### 1. Use Endpoint Names Consistently
```python
# Define endpoint once
LLM_ENDPOINT = "production-gpt4"

# Use throughout code
response = client.chat.completions.create(
    model=LLM_ENDPOINT,
    messages=[...]
)
```

### 2. Handle Rate Limits
```python
import time
from openai import RateLimitError

def call_llm_with_retry(messages, max_retries=3):
    for attempt in range(max_retries):
        try:
            return client.chat.completions.create(
                model="openai-gpt4",
                messages=messages
            )
        except RateLimitError:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise
```

### 3. Log Important Calls
```python
import logging

logger = logging.getLogger(__name__)

def query_llm(prompt):
    logger.info(f"Querying LLM with prompt length: {len(prompt)}")
    response = client.chat.completions.create(
        model="openai-gpt4",
        messages=[{"role": "user", "content": prompt}]
    )
    logger.info(f"Response tokens: {response.usage.total_tokens}")
    return response.choices[0].message.content
```

### 4. Use Streaming for Long Responses
```python
# Streaming response
stream = client.chat.completions.create(
    model="openai-gpt4",
    messages=[{"role": "user", "content": "Write a long story"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

## Security

### API Key Management
- Keys stored in Domino's secure vault
- Never exposed to end users
- Rotatable without code changes

### Data Privacy
- Requests logged for audit
- PII can be masked (admin config)
- Data retention policies configurable

## Troubleshooting

### Authentication Error
```
Error: 401 Unauthorized
```
- Verify Domino API key is valid
- Check endpoint access permissions
- Ensure correct base URL

### Rate Limit Exceeded
```
Error: 429 Too Many Requests
```
- Implement retry logic
- Contact admin for limit increase
- Use multiple endpoints for load distribution

### Model Not Found
```
Error: Model 'model-name' not found
```
- Verify endpoint name is correct
- Check endpoint exists and is active
- Confirm you have access to the endpoint

## Documentation Reference
- [AI Gateway](https://docs.dominodatalab.com/en/latest/user_guide/c9ac47/ai-gateway/)
- [Monitor AI Gateway LLM logs](https://docs.dominodatalab.com/en/cloud/admin_guide/984c09/monitor-ai-gateway-large-language-model-llm-logs/)
