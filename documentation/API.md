# 🔌 AI Agent System - API Documentation

Complete API reference for the AI Agent System v2.0

**Base URL:** `http://localhost:8000/api/v1`  
**Interactive Docs:** `http://localhost:8000/docs` (Swagger UI)

---

## 📋 Table of Contents

- [Authentication](#authentication)
- [Sessions API](#sessions-api)
- [Chat API](#chat-api)
- [Memory API](#memory-api)
- [Documents API](#documents-api)
- [Web Search API](#web-search-api)
- [Health Check](#health-check)
- [Error Codes](#error-codes)

---

## 🔐 Authentication

Currently, the API does not require authentication. This will be added in future versions.

**Planned:** Bearer token authentication

---

## 📝 Sessions API

### Create Session

**Endpoint:** `POST /api/v1/sessions`

**Request:**
```json
{
  "agent_name": "groq"
}
```

**Response:** `201 Created`
```json
{
  "session_id": "f7e9d0bc-1234-5678-90ab-cdef12345678",
  "agent_name": "groq",
  "created_at": "2025-12-09T10:30:00Z",
  "message_count": 0
}
```

**Available Agents:**
- `groq` - Llama 3.3 (70B) - Ultra-fast cloud AI
- `gpt-oss` - GPT-OSS (20B) - Advanced reasoning & memory
- `mixtral` - Mixtral (8x7B) - Premium quality MoE model
- `llama3.1` - Llama 3.1 (8B) - Long context (128k tokens)
- `mistral` - Mistral (7B) - Balanced performance
- `deepseek` - DeepSeek Coder - Code analysis specialist
- `medical` - Medical AI - Health knowledge (educational)

---

### List Sessions

**Endpoint:** `GET /api/v1/sessions`

**Response:** `200 OK`
```json
[
  {
    "session_id": "f7e9d0bc-...",
    "agent_name": "groq",
    "created_at": "2025-12-09T10:30:00Z",
    "updated_at": "2025-12-09T10:35:00Z",
    "message_count": 5
  }
]
```

---

### Get Session Messages

**Endpoint:** `GET /api/v1/sessions/{session_id}/messages`

**Response:** `200 OK`
```json
{
  "messages": [
    {
      "id": 1,
      "role": "user",
      "content": "Hello!",
      "timestamp": "2025-12-09T10:30:00Z"
    },
    {
      "id": 2,
      "role": "assistant",
      "content": "Hi! How can I help you today?",
      "timestamp": "2025-12-09T10:30:05Z"
    }
  ]
}
```

---

### Get Session Facts (NEW! ✨)

**Endpoint:** `GET /api/v1/sessions/{session_id}/facts`

**Query Parameters:**
- `limit` (optional, default: 20) - Max facts to return
- `min_importance` (optional, default: 0.0) - Minimum importance score

**Response:** `200 OK`
```json
{
  "facts": [
    {
      "id": 1,
      "session_id": "f7e9d0bc-...",
      "fact_type": "personal",
      "text": "User's name is Denis",
      "importance": 0.95,
      "confidence": 0.92,
      "tags": ["name", "personal"],
      "extracted_at": "2025-12-09T10:31:00Z"
    },
    {
      "id": 2,
      "fact_type": "professional",
      "text": "User works as a QA Engineer",
      "importance": 0.88,
      "confidence": 0.85,
      "tags": ["occupation", "professional"],
      "extracted_at": "2025-12-09T10:32:00Z"
    }
  ],
  "total": 2
}
```

---

## 💬 Chat API

### Enhanced Chat (Recommended)

**Endpoint:** `POST /api/v1/chat/enhanced`

Multi-source intelligent chat with automatic context retrieval.

**Request:**
```json
{
  "message": "What programming languages should I learn?",
  "session_id": "f7e9d0bc-...",
  "agent_name": "groq",
  "include_memory": true,
  "search_documents": false,
  "search_web": false
}
```

**Response:** `200 OK`
```json
{
  "response": "Based on your profile as a QA Engineer who loves Python...",
  "sources_used": ["conversation_history", "user_facts"],
  "facts_extracted": 2,
  "timestamp": "2025-12-09T10:35:00Z",
  "model": "groq",
  "facts": [
    {
      "text": "User is interested in learning new languages",
      "importance": 0.75
    }
  ]
}
```

**Source Types:**
- `conversation_history` - Previous messages in session
- `user_facts` - Extracted facts from memory
- `documents` - Uploaded documents (if search_documents=true)
- `web_search` - Web search results (if search_web=true)

---

### Basic Chat

**Endpoint:** `POST /api/v1/chat`

Simple chat without enhanced context.

**Request:**
```json
{
  "message": "Hello!",
  "session_id": "f7e9d0bc-...",
  "agent_name": "groq"
}
```

**Response:** `200 OK`
```json
{
  "response": "Hello! How can I help you today?",
  "timestamp": "2025-12-09T10:35:00Z"
}
```

---

## 🧠 Memory API

### Get Memory Stats

**Endpoint:** `GET /api/v1/memory/stats`

**Query Parameters:**
- `session_id` (optional) - Stats for specific session

**Response:** `200 OK`
```json
{
  "total_facts": 127,
  "by_type": {
    "personal": 45,
    "professional": 38,
    "preference": 28,
    "other": 16
  },
  "by_importance": {
    "high": 35,
    "medium": 62,
    "low": 30
  },
  "avg_confidence": 0.82,
  "oldest_fact": "2025-11-20T14:00:00Z",
  "newest_fact": "2025-12-09T10:35:00Z"
}
```

---

### Search Facts

**Endpoint:** `GET /api/v1/memory/search`

**Query Parameters:**
- `query` (required) - Search query
- `session_id` (optional) - Search within session
- `limit` (optional, default: 10)
- `min_confidence` (optional, default: 0.5)

**Response:** `200 OK`
```json
{
  "results": [
    {
      "fact": {
        "id": 1,
        "text": "User's name is Denis",
        "importance": 0.95,
        "confidence": 0.92
      },
      "similarity_score": 0.87
    }
  ],
  "total": 1
}
```

---

## 📄 Documents API

### Upload Document

**Endpoint:** `POST /api/v1/documents/upload`

**Request:** `multipart/form-data`
```
file: <file_data>
session_id: "f7e9d0bc-..."
```

**Supported Formats:**
- PDF (.pdf)
- Text (.txt)
- Markdown (.md)
- Word (.docx)

**Response:** `201 Created`
```json
{
  "document_id": "doc_123",
  "filename": "report.pdf",
  "pages": 15,
  "chunks_created": 47,
  "upload_time": "2025-12-09T10:40:00Z"
}
```

---

### Search Documents

**Endpoint:** `POST /api/v1/documents/search`

**Request:**
```json
{
  "query": "What is the revenue forecast?",
  "session_id": "f7e9d0bc-...",
  "top_k": 5
}
```

**Response:** `200 OK`
```json
{
  "results": [
    {
      "document_id": "doc_123",
      "chunk_id": "chunk_5",
      "text": "The Q4 revenue forecast is $2.5M...",
      "similarity_score": 0.91,
      "metadata": {
        "page": 3,
        "filename": "report.pdf"
      }
    }
  ]
}
```

---

## 🌐 Web Search API

### Search Web

**Endpoint:** `GET /api/v1/search/web`

**Query Parameters:**
- `query` (required) - Search query
- `max_results` (optional, default: 5)

**Response:** `200 OK`
```json
{
  "results": [
    {
      "title": "AI Trends 2025",
      "url": "https://example.com/ai-trends",
      "snippet": "The latest developments in AI...",
      "source": "DuckDuckGo"
    }
  ],
  "query": "AI trends 2025",
  "total_results": 5
}
```

---

## 🏥 Health Check

### Check Health

**Endpoint:** `GET /api/v1/health`

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "version": "2.0",
  "database": "connected",
  "ollama": "connected",
  "models": ["groq", "mistral", "llama3.1"],
  "uptime_seconds": 86400
}
```

---

## ❌ Error Codes

### Standard HTTP Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Request completed |
| 201 | Created | Session/Document created |
| 400 | Bad Request | Invalid parameters |
| 404 | Not Found | Session not found |
| 422 | Validation Error | Invalid JSON schema |
| 500 | Server Error | Internal error |
| 503 | Service Unavailable | Ollama not running |

### Error Response Format
```json
{
  "detail": "Session not found",
  "error_code": "SESSION_NOT_FOUND",
  "timestamp": "2025-12-09T10:45:00Z"
}
```

---

## 📊 Rate Limiting

Currently not implemented. Future versions will include:
- 100 requests/minute per IP
- 1000 requests/hour per IP

---

## 🔮 Upcoming API Features

- [ ] Authentication (Bearer tokens)
- [ ] Webhooks for async operations
- [ ] Streaming responses (SSE)
- [ ] Batch operations
- [ ] Rate limiting
- [ ] API versioning

---

**Last Updated:** December 9, 2025  
**API Version:** v1  
**Interactive Docs:** http://localhost:8000/docs