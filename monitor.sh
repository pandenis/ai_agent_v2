#!/bin/bash

echo "╔════════════════════════════════════════╗"
echo "║   AI Agent System - Status Monitor    ║"
echo "╚════════════════════════════════════════╝"
echo

# Services
echo "📦 Services Status:"
echo "  AI Agent: $(systemctl is-active ai-agent)"
echo "  Ollama:   $(systemctl is-active ollama)"
echo "  Nginx:    $(systemctl is-active nginx)"
echo

# Models
echo "🤖 Available Models:"
ollama list | head -5
echo

# Resources
echo "💾 Disk Space:"
df -h /srv/ai_agent | tail -1
echo

echo "🧠 Memory:"
free -h | grep Mem | awk '{print "  Used: " $3 " / " $2 " (" int($3/$2*100) "%)"}'
echo

# Recent logs
echo "📝 Recent Logs (last 5 lines):"
tail -5 /srv/ai_agent/logs/app.log 2>/dev/null || echo "  (no logs yet)"
echo

# API Status
echo "🔍 API Health:"
curl -s http://localhost/api/v1/health | jq -r '"  Status: " + .status' 2>/dev/null || echo "  API not responding"
echo

# Network
SERVER_IP=$(ip -4 addr show | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | grep -v 127.0.0.1 | head -1)
echo "🌐 Access URLs:"
echo "  Internal: http://localhost/docs"
echo "  External: http://$SERVER_IP/docs"
