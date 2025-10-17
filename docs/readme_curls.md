Here's a comprehensive set of testing curl commands based on your working query:

## 🎯 Agent Query Operations

### 1. **Basic Query (Non-Streaming)**
```bash
curl -X POST "http://localhost:8000/api/v1/agents/848422754410561536/query" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-001",
    "session_id": "7987811513182191616",
    "message": "Hello, what can you help me with?"
  }'
```

### 2. **Query with Metadata**
```bash
curl -X POST "http://localhost:8000/api/v1/agents/848422754410561536/query" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-001",
    "session_id": "7987811513182191616",
    "message": "What are your capabilities?",
    "metadata": {
      "source": "api_test",
      "timestamp": "2025-10-18"
    }
  }'
```

### 3. **Streaming Query (SSE)**
```bash
curl -X POST "http://localhost:8000/api/v1/agents/848422754410561536/stream_query" \
  -H "Content-Type: application/json" \
  -N \
  -d '{
    "user_id": "test-user-001",
    "session_id": "7987811513182191616",
    "message": "Tell me a short story about robots"
  }'
```

### 4. **Create New Session (Auto-Generated Session ID)**
```bash
curl -X POST "http://localhost:8000/api/v1/agents/848422754410561536/query" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-001",
    "message": "Start a new conversation"
  }'
```

---

## 📦 Session Management

### 5. **Create Session**
```bash
curl -X POST "http://localhost:8000/api/v1/agents/848422754410561536/users/test-user-001/sessions" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-001",
    "initial_state": {
      "language": "en",
      "context": "testing"
    }
  }'
```

### 6. **Get Session Details**
```bash
curl -X GET "http://localhost:8000/api/v1/agents/848422754410561536/users/test-user-001/sessions/7987811513182191616" \
  -H "Content-Type: application/json"
```

### 7. **List User Sessions**
```bash
curl -X GET "http://localhost:8000/api/v1/agents/848422754410561536/users/test-user-001/sessions" \
  -H "Content-Type: application/json"
```

### 8. **List All Sessions (All Users)**
```bash
curl -X GET "http://localhost:8000/api/v1/agents/848422754410561536/sessions?page_size=20" \
  -H "Content-Type: application/json"
```

### 9. **Update Session State**
```bash
curl -X PATCH "http://localhost:8000/api/v1/agents/848422754410561536/users/test-user-001/sessions/7987811513182191616/state" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-001",
    "state_delta": {
      "last_interaction": "2025-10-18T02:49:43Z",
      "interaction_count": 5,
      "user_preference": "verbose"
    },
    "replace": false
  }'
```

### 10. **Replace Session State (Clear & Set)**
```bash
curl -X PATCH "http://localhost:8000/api/v1/agents/848422754410561536/users/test-user-001/sessions/7987811513182191616/state" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-001",
    "state_delta": {
      "reset": true,
      "new_field": "new_value"
    },
    "replace": true
  }'
```

### 11. **Get Session Statistics**
```bash
curl -X GET "http://localhost:8000/api/v1/agents/848422754410561536/users/test-user-001/sessions/7987811513182191616/stats" \
  -H "Content-Type: application/json"
```

### 12. **Delete Session**
```bash
curl -X DELETE "http://localhost:8000/api/v1/agents/848422754410561536/users/test-user-001/sessions/7987811513182191616" \
  -H "Content-Type: application/json"
```

---

## 📝 Event Management

### 13. **List Session Events**
```bash
curl -X GET "http://localhost:8000/api/v1/agents/848422754410561536/users/test-user-001/sessions/7987811513182191616/events" \
  -H "Content-Type: application/json"
```

### 14. **List Events with Pagination**
```bash
curl -X GET "http://localhost:8000/api/v1/agents/848422754410561536/users/test-user-001/sessions/7987811513182191616/events?page_size=10&filter=author='user'" \
  -H "Content-Type: application/json"
```

### 15. **Append Event (User Message)**
```bash
curl -X POST "http://localhost:8000/api/v1/agents/848422754410561536/users/test-user-001/sessions/7987811513182191616/events" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-001",
    "author": "user",
    "invocation_id": "inv-'$(date +%s)'",
    "content_text": "This is a test message from the user",
    "content_role": "user"
  }'
```

### 16. **Append Event with State Update**
```bash
curl -X POST "http://localhost:8000/api/v1/agents/848422754410561536/users/test-user-001/sessions/7987811513182191616/events" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-001",
    "author": "system",
    "invocation_id": "inv-state-'$(date +%s)'",
    "content_text": "User completed onboarding",
    "content_role": "system",
    "state_delta": {
      "onboarding_complete": true,
      "completion_time": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
    }
  }'
```

### 17. **Get Conversation History**
```bash
curl -X GET "http://localhost:8000/api/v1/agents/848422754410561536/users/test-user-001/sessions/7987811513182191616/conversation?max_turns=10" \
  -H "Content-Type: application/json"
```

---

## 🔍 Discovery & Health

### 18. **List All Configured Agents**
```bash
curl -X GET "http://localhost:8000/api/v1/agents" \
  -H "Content-Type: application/json"
```

### 19. **Health Check**
```bash
curl -X GET "http://localhost:8000/api/v1/health" \
  -H "Content-Type: application/json"
```

### 20. **List All Users**
```bash
curl -X GET "http://localhost:8000/api/v1/agents/848422754410561536/users" \
  -H "Content-Type: application/json"
```

---

## 🧪 Advanced Testing Scenarios

### 21. **Multi-Turn Conversation**
```bash
# Turn 1
curl -X POST "http://localhost:8000/api/v1/agents/848422754410561536/query" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-001",
    "session_id": "7987811513182191616",
    "message": "My name is Alice"
  }'

# Turn 2
curl -X POST "http://localhost:8000/api/v1/agents/848422754410561536/query" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-001",
    "session_id": "7987811513182191616",
    "message": "What is my name?"
  }'
```

### 22. **Long Response Test**
```bash
curl -X POST "http://localhost:8000/api/v1/agents/848422754410561536/query" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-001",
    "session_id": "7987811513182191616",
    "message": "Explain quantum computing in detail"
  }'
```

### 23. **Streaming with Real-Time Display**
```bash
curl -X POST "http://localhost:8000/api/v1/agents/848422754410561536/stream_query" \
  -H "Content-Type: application/json" \
  -N --no-buffer \
  -d '{
    "user_id": "test-user-001",
    "session_id": "7987811513182191616",
    "message": "Count from 1 to 20 slowly"
  }'
```

---

## 📊 Batch Testing Script

Save this as `test_all.sh`:

```bash
#!/bin/bash

AGENT_ID="848422754410561536"
USER_ID="test-user-001"
SESSION_ID="7987811513182191616"
BASE_URL="http://localhost:8000/api/v1"

echo "=== Testing Vertex AI Agent Gateway ==="
echo ""

echo "1. Health Check..."
curl -s "${BASE_URL}/health" | jq .
echo ""

echo "2. List Agents..."
curl -s "${BASE_URL}/agents" | jq .
echo ""

echo "3. Query Agent..."
curl -s -X POST "${BASE_URL}/agents/${AGENT_ID}/query" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"${USER_ID}\",
    \"session_id\": \"${SESSION_ID}\",
    \"message\": \"Hello!\"
  }" | jq .
echo ""

echo "4. Get Session..."
curl -s "${BASE_URL}/agents/${AGENT_ID}/users/${USER_ID}/sessions/${SESSION_ID}" | jq .
echo ""

echo "5. List Events..."
curl -s "${BASE_URL}/agents/${AGENT_ID}/users/${USER_ID}/sessions/${SESSION_ID}/events" | jq .
echo ""

echo "6. Get Session Stats..."
curl -s "${BASE_URL}/agents/${AGENT_ID}/users/${USER_ID}/sessions/${SESSION_ID}/stats" | jq .
echo ""

echo "=== All Tests Complete ==="
```

Make it executable and run:
```bash
chmod +x test_all.sh
./test_all.sh
```

---

## 🎯 Quick Reference Variables

For easy copy-paste, set these variables in your terminal:

```bash
export AGENT_ID="848422754410561536"
export USER_ID="test-user-001"
export SESSION_ID="7987811513182191616"
export BASE_URL="http://localhost:8000/api/v1"

# Then use them:
curl -X POST "${BASE_URL}/agents/${AGENT_ID}/query" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"${USER_ID}\",
    \"session_id\": \"${SESSION_ID}\",
    \"message\": \"Test message\"
  }"
```

All commands are ready to use! Let me know which scenarios you'd like to test first. 🚀