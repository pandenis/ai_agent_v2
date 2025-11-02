# 🤖 AI Agent System v2.0

Production-ready multi-source intelligent AI agent system with semantic search and web integration.

## ✨ Features

- 🧠 **Enhanced Chat** - Intelligent multi-source context retrieval
- 📄 **Document Search** - Semantic search with ChromaDB embeddings  
- 🌐 **Web Search** - Real-time web search integration (DuckDuckGo)
- 💾 **Persistent Memory** - Conversation history and user facts
- 🔒 **Security** - Input validation and sanitization
- 📊 **REST API** - FastAPI with automatic OpenAPI documentation
- ✅ **Tested** - 17 unit tests with 100% pass rate

## 🛠️ Tech Stack

- **Backend:** FastAPI, Python 3.11
- **Database:** SQLAlchemy 2.0 (async) + SQLite
- **Vector Store:** ChromaDB with sentence-transformers
- **Search:** DuckDuckGo Search API
- **Testing:** pytest with async support

## 🚀 Quick Start
```bash
# Clone repository
git clone https://github.com/pandenis/ai_agent_v2.git
cd ai_agent_v2

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app.main:app --reload
```

Open http://localhost:8000/docs for interactive API documentation.

## 📚 API Documentation

### Main Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/sessions` | Create chat session |
| POST | `/api/v1/chat/enhanced` | 🔥 Intelligent multi-source chat |
| POST | `/api/v1/documents/upload` | Upload and index documents |
| POST | `/api/v1/documents/search` | Semantic document search |
| POST | `/api/v1/search/web` | Web search |
| GET | `/api/v1/health` | Health check |

### Example Usage

#### 1. Create Session
```bash
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "mistral"}'
```

#### 2. Upload Document
```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "Content-Type: application/json" \
  -d '{
    "text": "FastAPI is a modern web framework for Python...",
    "filename": "fastapi_notes.txt"
  }'
```

#### 3. Enhanced Chat (with auto document/web search!)
```bash
curl -X POST http://localhost:8000/api/v1/chat/enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "YOUR_SESSION_ID",
    "message": "What did I write about FastAPI?",
    "include_memory": true
  }'
```

Response includes sources used:
```json
{
  "response": "According to your documents...\n\n[Sources: documents, conversation_history]"
}
```

## 🧪 Testing
```bash
# Run all tests
pytest tests/unit/ -v

# With coverage
pytest tests/unit/ --cov=app --cov-report=term-missing

# Specific test file
pytest tests/unit/test_enhanced_chat.py -v
```

## 📁 Project Structure
```
ai_agent_v2/
├── app/
│   ├── api/              # API routes and dependencies
│   │   ├── routes.py     # All endpoints
│   │   └── deps.py       # Dependency injection
│   ├── core/             # Core functionality
│   │   ├── config.py     # Configuration
│   │   ├── database.py   # Database setup
│   │   └── security.py   # Security validation
│   ├── models/           # SQLAlchemy models
│   │   ├── session.py    # Session model
│   │   └── memory.py     # Memory models
│   ├── schemas/          # Pydantic schemas
│   │   └── agent.py      # Request/response schemas
│   └── services/         # Business logic
│       ├── agent_service.py          # AI agent integration
│       ├── memory_service.py         # Memory management
│       ├── document_service.py       # Document search
│       ├── web_search_service.py     # Web search
│       └── enhanced_chat_service.py  # 🔥 Multi-source intelligence
├── tests/
│   └── unit/             # Unit tests
├── data/                 # Database and vector store
├── .env                  # Environment variables
├── requirements.txt      # Dependencies
└── pytest.ini           # Test configuration
```

## 🎯 How It Works

The **Enhanced Chat Service** intelligently determines what sources to use:

1. 🔍 **Document Search** triggers on keywords: `"document"`, `"wrote"`, `"file"`, `"писал"`, `"документ"`
2. 🌐 **Web Search** triggers on: `"latest"`, `"current"`, `"news"`, `"2025"`, `"последние"`
3. 💾 **Memory** always includes conversation history and user facts
4. 📊 **Source Citation** automatically added to responses

## 🔧 Configuration

Create `.env` file:
```env
# Application
APP_NAME="AI Agent System"
DEBUG=true

# Database
DATABASE_URL=sqlite+aiosqlite:///./data/agent.db

# Ollama (optional - uses mock mode if not available)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=mistral:latest
```

## 🌟 Key Features

### Intelligent Context Retrieval
- Automatic keyword detection
- Multi-source data fusion
- Relevance scoring

### Semantic Search
- ChromaDB vector database
- Sentence transformers embeddings
- Fast similarity search

### Production Ready
- Async/await throughout
- Type hints with Pydantic
- Comprehensive error handling
- Security validation
- Health monitoring

## 📈 Development Timeline

- **Week 1**: Database models + Tests
- **Week 2**: Services + REST API
- **Week 3**: Document & Web Search
- **Week 4**: Enhanced Chat Intelligence ✨

**Total**: 800+ lines of code, 17 tests, 100% passing

## 📝 License

MIT

## 👨‍💻 Author

Built with ❤️ by **pandenis**

## 🙏 Acknowledgments

- FastAPI for the amazing framework
- ChromaDB for vector search capabilities
- Anthropic Claude for development assistance
