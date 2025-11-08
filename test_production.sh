#!/bin/bash

echo "🧪 Testing AI Agent Production System"
echo "======================================"
echo

# Get server IP
SERVER_IP=$(ip -4 addr show | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | grep -v 127.0.0.1 | head -1)
echo "🌐 Server IP: $SERVER_IP"
echo

# Test 1: Health check
echo "1️⃣ Health Check..."
curl -s http://localhost/api/v1/health | jq
echo

# Test 2: Agent status
echo "2️⃣ Agent Status..."
curl -s http://localhost/api/v1/agents/status | jq '{
  default_agent,
  total_agents,
  enabled_agents,
  available_agents,
  agents: .agents | keys
}'
echo

# Test 3: Create session
echo "3️⃣ Creating Session..."
SESSION_ID=$(curl -s -X POST http://localhost/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "mistral"}' | jq -r '.session_id')
echo "   Session ID: $SESSION_ID"
echo

# Test 4: Chat with Mistral
echo "4️⃣ Chat with Mistral..."
curl -s -X POST http://localhost/api/v1/chat/enhanced \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"message\": \"Say hello in one word\",
    \"agent_name\": \"mistral\",
    \"include_memory\": true
  }" | jq '{response: .response, agent_used: .agent_used}'
echo

# Test 5: Agent selection
echo "5️⃣ Agent Selection (code task)..."
curl -s -X POST http://localhost/api/v1/agents/select \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Write Python code", "task_type": "code_analysis"}' | jq
echo

echo "✅ Production Test Complete!"
echo
echo "📄 Access Swagger UI: http://$SERVER_IP/docs"
echo "🔍 Health endpoint: http://$SERVER_IP/api/v1/health"
echo "📊 Agent status: http://$SERVER_IP/api/v1/agents/status"
