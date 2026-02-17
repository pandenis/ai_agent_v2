#!/usr/bin/env bash
# AI Agent System — Cron Job Installer Helper
# Usage: ./scripts/install_cron.sh
# Prints cron entries to add via: crontab -e

echo "=== AI Agent Cron Jobs ==="
echo ""
echo "Add these to your crontab (crontab -e):"
echo ""
echo "# Daily backup at 3:00 AM"
echo "0 3 * * * cd /srv/ai_agent && ./scripts/backup.sh >> logs/backup.log 2>&1"
echo ""
echo "# Health check every 15 minutes"
echo "*/15 * * * * cd /srv/ai_agent && ./scripts/health_check.sh 8000 >> logs/health.log 2>&1"
echo ""
echo "# Alert check every hour"
echo "0 * * * * cd /srv/ai_agent && ./scripts/alert_check.sh >> logs/alerts.log 2>&1"
echo ""
echo "For DEV environment, replace /srv/ai_agent with /srv/ai_agent_dev_git and port 8000 with 8001"
