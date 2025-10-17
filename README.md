# Vertex AI Agent Engine Gateway

Production-ready FastAPI gateway for deployed Vertex AI Agent Engine agents with complete session management, state handling, and streaming support.

## Features

- ✅ Query deployed agents (streaming & non-streaming)
- ✅ Complete session management (create, get, list, delete)
- ✅ Event management and conversation history
- ✅ State management via state_delta (ADK-compatible)
- ✅ Multi-agent support with configuration
- ✅ Server-Sent Events (SSE) for streaming
- ✅ Comprehensive error handling
- ✅ Health checks and monitoring
- ✅ Google Cloud authentication
- ✅ Production-ready logging
- ✅ CORS support

## Architecture
```
User → Gateway API → Vertex AI Agent Engine
                 ↓
            Sessions API
                 ↓
            Events & State
```

## Quick Start

### Prerequisites

- Python 3.11+
- Google Cloud Project with Vertex AI enabled
- Deployed Vertex AI Agent Engine agents
- Service account with proper permissions

### Installation
```bash
# Clone repository
git clone <repo-url>
cd vertex-ai-agent-gateway

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create `.env` file:
```bash
# Application
APP_NAME=agent-gateway
ENVIRONMENT=development
LOG_LEVEL=INFO

# Google Cloud
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Agents (JSON array)
AGENTS='[
  {
    "agent_id": "abc123",
    "name": "customer_support",
    "display_name": "Customer Support Agent",
    "description": "Handles customer inquiries",
    "enabled": true
  }
]'

# Optional
CORS_ORIGINS=["http://localhost:3000"]
```

### Run
```bash
# Development
uvicorn app.main:app --reload --port 8000

# Production
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## API Endpoints

### Health
- `GET /api/v1/health` - Service health check

### Agents
- `GET /api/v1/agents` - List configured agents
- `POST /api/v1/agents/{agent_id}/query` - Query agent (non-streaming)
- `POST /api/v1/agents/{agent_id}/stream_query` - Query agent (SSE streaming)

### Sessions
- `POST /api/v1/agents/{agent_id}/users/{user_id}/sessions` - Create session
- `POST /api/v1/agents/{agent_id}/users/{user_id}/sessions/{session_id}` - Create with ID
- `GET /api/v1/agents/{agent_id}/users/{user_id}/sessions/{session_id}` - Get session
- `GET /api/v1/agents/{agent_id}/users/{user_id}/sessions` - List user sessions
- `PATCH /api/v1/agents/{agent_id}/users/{user_id}/sessions/{session_id}/state` - Update state
- `DELETE /api/v1/agents/{agent_id}/users/{user_id}/sessions/{session_id}` - Delete session

### Events
- `POST /api/v1/agents/{agent_id}/users/{user_id}/sessions/{session_id}/events` - Append event
- `GET /api/v1/agents/{agent_id}/users/{user_id}/sessions/{session_id}/events` - List events

## Usage Examples

### Query Agent
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/agents/abc123/query",
    json={
        "user_id": "user-456",
        "session_id": "session-789",
        "message": "What's the weather like?"
    }
)

print(response.json())
```

### Stream Query
```python
import requests

with requests.post(
    "http://localhost:8000/api/v1/agents/abc123/stream_query",
    json={
        "user_id": "user-456",
        "session_id": "session-789",
        "message": "Tell me a story"
    },
    stream=True
) as response:
    for line in response.iter_lines():
        if line:
            print(line.decode('utf-8'))
```

### Manage Sessions
```python
# Create session
response = requests.post(
    "http://localhost:8000/api/v1/agents/abc123/users/user-456/sessions",
    json={"initial_state": {"language": "en"}}
)
session = response.json()

# Update state
requests.patch(
    f"http://localhost:8000/api/v1/agents/abc123/users/user-456/sessions/{session['session_id']}/state",
    json={
        "user_id": "user-456",
        "state_delta": {"preference": "dark_mode"},
        "replace": False
    }
)
```

## Testing
```bash
# Run tests
pytest

# With coverage
pytest --cov=app tests/
```

## Deployment

### Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

### Cloud Run
```bash
gcloud run deploy agent-gateway \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

## License

MIT 