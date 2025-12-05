# 🤖 AI Agent System v2.0

Production-ready multi-model intelligent AI agent system with advanced memory, semantic search, and modern React UI.

[![Tests](https://img.shields.io/badge/tests-173%20passing-success)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen)](tests/)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://python.org)
[![React](https://img.shields.io/badge/react-19.0-blue)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/typescript-5.0-blue)](https://typescriptlang.org)

---

## ✨ Features

### 🎨 Modern UI (Week 4 - NEW!)
- 💬 **Real-time Chat Interface** - Smooth, responsive chat with typing indicators
- 📝 **MemoryPanel** - Visual display of extracted facts with importance ratings ⭐
- 🔄 **Session Management** - Auto-refreshing session list
- ⚡ **Loading States** - Skeleton loaders and smooth transitions
- 🛡️ **Error Handling** - Toast notifications and error boundaries
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile

### 🧠 Backend Intelligence
- 🤖 **Multi-Model Support** - Groq, Mistral, Llama3, DeepSeek
- 🧩 **Smart Orchestration** - Automatic agent selection based on task type
- 💾 **Enhanced Memory** (Memorisator) - Automatic fact extraction with confidence scoring
- 📄 **Document Search** - Semantic search with ChromaDB embeddings
- 🌐 **Web Search** - Real-time web integration (DuckDuckGo)
- 🔐 **Security** - Input validation, sanitization, CORS protection

---

## 🛠️ Tech Stack

### Frontend
- **Framework**: Next.js 15 with App Router
- **UI Library**: React 19
- **Language**: TypeScript 5
- **Styling**: Tailwind CSS 3
- **Components**: Custom UI components
- **Notifications**: react-hot-toast
- **Date**: date-fns

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: SQLAlchemy 2.0 (async) + SQLite
- **Vector Store**: ChromaDB with sentence-transformers
- **AI Models**: Ollama + Groq Cloud API
- **Search**: DuckDuckGo Search API
- **Testing**: pytest with 85%+ coverage

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Ollama (optional, for local models)

### Backend Setup
```bash
# Clone repository
git clone https://github.com/pandenis/ai_agent_v2.git
cd ai_agent_v2

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
DATABASE_URL=sqlite+aiosqlite:///./data/agent.db
OLLAMA_HOST=http://localhost:11434
GROQ_API_KEY=your_groq_api_key_here
memorisator_enabled=true
max_memory_facts=10000
EOF

# Run backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend will be available at `http://localhost:8000`

### Frontend Setup
```bash
# Navigate to frontend directory
cd ui/ai-agent-ui

# Install dependencies
npm install

# Create .env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local

# Run development server
npm run dev
```

Frontend will be available at `http://localhost:3000`

---

## 📚 API Documentation

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/sessions` | Create new chat session |
| GET | `/api/v1/sessions` | List all sessions |
| GET | `/api/v1/sessions/{id}/messages` | Get session messages |
| GET | `/api/v1/sessions/{id}/facts` | **NEW!** Get extracted facts |
| POST | `/api/v1/chat/enhanced` | Intelligent multi-source chat |
| POST | `/api/v1/documents/upload` | Upload and index documents |
| POST | `/api/v1/documents/search` | Semantic document search |
| GET | `/api/v1/health` | Health check |

### Interactive Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 🎯 Key Features Explained

### 1. MemoryPanel (Week 4 ✨)

The MemoryPanel displays extracted facts from conversations with visual importance ratings:
```typescript
// Facts are displayed with:
⭐⭐⭐⭐⭐  High importance (0.9-1.0)
⭐⭐⭐⭐    Medium-high (0.7-0.9)
⭐⭐⭐      Medium (0.5-0.7)
```

**Features:**
- Real-time fact extraction
- Importance and confidence scoring
- Categorized by fact_type (personal, professional, preference)
- Tags for easy filtering
- Auto-updates on new messages

### 2. Enhanced Chat Service

Intelligent context retrieval with automatic source selection:
```python
# Triggers document search
"What did I write about FastAPI?"

# Triggers web search
"What's the latest news about AI?"

# Uses conversation memory
"Continue our previous discussion"
```

**Response includes source attribution:**
```json
{
  "response": "Based on your documents...",
  "sources_used": ["documents", "conversation_history", "user_facts"],
  "facts_extracted": 3
}
```

### 3. Smart Orchestration

Automatic agent selection based on task analysis:

| Task Type | Agent | Use Case |
|-----------|-------|----------|
| Code Analysis | Llama3 | Python, JavaScript, debugging |
| Medical Query | Medical AI | Health, symptoms, medicine |
| General Chat | Groq | Fast responses, general queries |
| Creative Writing | Mistral | Stories, poems, content |

### 4. UI Loading States

Professional UX with comprehensive loading indicators:

- **Skeleton Loaders** - Session list loads gracefully
- **Typing Indicator** - Animated dots show AI is responding
- **Button States** - Disabled states prevent double-clicks
- **Error Recovery** - Toast notifications with retry logic

---

## 🧪 Testing

### Run Tests
```bash
# Backend tests
pytest tests/unit/ -v --cov=app

# Frontend tests (if available)
cd ui/ai-agent-ui
npm test
```

### Test Coverage
```
Backend:  173 tests, 85%+ coverage
Frontend: Component tests passing
E2E:      Manual testing complete
```

---

## 📁 Project Structure
```
ai_agent_v2/
├── app/                          # Backend (FastAPI)
│   ├── api/                      # API routes
│   │   ├── routes.py            # All endpoints
│   │   └── deps.py              # Dependencies
│   ├── core/                    # Core functionality
│   │   ├── config.py           # Configuration
│   │   ├── database.py         # Database setup
│   │   └── security.py         # Security
│   ├── models/                  # SQLAlchemy models
│   │   ├── session.py          # Sessions
│   │   ├── memory.py           # Messages & Facts
│   │   └── __init__.py
│   ├── schemas/                 # Pydantic schemas
│   │   └── agent.py            # API schemas
│   └── services/                # Business logic
│       ├── agent_service.py         # Multi-model agents
│       ├── memory_service.py        # Memory management
│       ├── fact_extractor.py        # ✨ Fact extraction
│       ├── enhanced_chat_service.py # Multi-source intelligence
│       ├── document_service.py      # Document search
│       └── web_search_service.py    # Web search
│
├── ui/ai-agent-ui/              # Frontend (Next.js + React)
│   ├── src/
│   │   ├── app/                 # Next.js app router
│   │   │   ├── chat/           # Chat page
│   │   │   └── layout.tsx      # Root layout
│   │   ├── components/          # React components
│   │   │   ├── chat/           # Chat components
│   │   │   │   ├── ChatInterface.tsx
│   │   │   │   └── MessageList.tsx
│   │   │   ├── features/       # Feature components
│   │   │   │   ├── SessionList.tsx
│   │   │   │   ├── MemoryPanel.tsx  # ✨ NEW
│   │   │   │   ├── ChatInput.tsx
│   │   │   │   └── AgentSelector.tsx
│   │   │   ├── ui/             # UI primitives
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── SkeletonLoader.tsx  # ✨ NEW
│   │   │   │   └── TypingIndicator.tsx # ✨ NEW
│   │   │   ├── providers/      # Context providers
│   │   │   │   └── ToastProvider.tsx   # ✨ NEW
│   │   │   └── ErrorBoundary.tsx       # ✨ NEW
│   │   ├── lib/                # Utilities
│   │   │   └── api/           # API client
│   │   └── types/             # TypeScript types
│   └── public/                # Static assets
│
├── tests/                       # Tests
│   ├── unit/                   # Unit tests
│   └── integration/            # Integration tests
│
├── data/                       # Runtime data
│   ├── agent.db               # SQLite database
│   └── chroma/                # Vector store
│
├── docs/                       # Documentation
├── requirements.txt            # Python dependencies
├── package.json               # Node dependencies
└── README.md                  # This file
```

---

## 🔧 Configuration

### Backend (.env)
```bash
# Application
APP_NAME="AI Agent System"
DEBUG=true
LOG_LEVEL=INFO

# Database
DATABASE_URL=sqlite+aiosqlite:///./data/agent.db

# Ollama (local models)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=mistral:latest

# Groq (cloud API)
GROQ_API_KEY=your_api_key_here
GROQ_API_BASE=https://api.groq.com/openai/v1

# Memorisator (Enhanced Memory)
memorisator_enabled=true
max_memory_facts=10000
fact_importance_threshold=0.5
fact_confidence_threshold=0.7

# Security
SECRET_KEY=your_secret_key_here
```

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## 📈 Development Timeline

### Week 1-2: Backend Foundation ✅
- Database models and migrations
- SQLAlchemy async setup
- Memory service
- Agent integration
- **173 unit tests**

### Week 3: UI Components ✅
- Next.js setup
- Chat interface
- Session management
- Agent selector
- Production deployment

### Week 4: Polish & Enhancement ✅ (Current)
- ✨ **MemoryPanel** with fact visualization
- ✨ **Auto-refresh** for session list
- ✨ **Loading states** throughout UI
- ✨ **Error handling** with toast notifications
- ✨ **Retry logic** for API calls
- ✨ **Error boundaries** for graceful failures

**Progress: 54% Complete (Week 4: 50% done)**

### Upcoming: Week 5-6
- Advanced features
- Multi-agent testing
- Mobile optimization
- Performance tuning
- Production launch

---

## 🚀 Deployment

### Production Setup
```bash
# Backend (systemd service)
sudo systemctl start ai-agent.service
sudo systemctl enable ai-agent.service

# Frontend (systemd service)
sudo systemctl start ai-agent-ui.service
sudo systemctl enable ai-agent-ui.service

# Check status
sudo systemctl status ai-agent.service
sudo systemctl status ai-agent-ui.service
```

### Environment
- **Backend**: Port 8000
- **Frontend**: Port 3000
- **Database**: SQLite (upgradeable to PostgreSQL)
- **Ollama**: Port 11434 (local models)

---

## 🎨 UI Screenshots

### Chat Interface
Modern chat with real-time responses, agent selection, and source attribution.

### MemoryPanel
Visual fact display with star ratings showing importance levels.

### Session Management
Auto-refreshing list with message counts and timestamps.

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details

---

## 👨‍💻 Author

Built with ❤️ by **Denis** (QA Engineer specializing in medical software testing)

**Contact:**
- GitHub: [@pandenis](https://github.com/pandenis)
- Project: [ai_agent_v2](https://github.com/pandenis/ai_agent_v2)

---

## 🙏 Acknowledgments

- **FastAPI** - Modern Python web framework
- **Next.js** - React framework with amazing DX
- **ChromaDB** - Vector database for semantic search
- **Groq** - Fast AI inference
- **Ollama** - Local LLM hosting
- **Anthropic Claude** - Development assistance and pair programming

---

## 📊 Project Stats
```
Total Lines of Code:    15,000+
Backend Tests:          173 (passing)
Test Coverage:          85%+
Components:             20+
API Endpoints:          25+
Development Time:       4 weeks
Contributors:           1
Coffee Consumed:        ∞ ☕
```

---

## 🎯 Use Cases

### Personal Assistant
- Store and retrieve personal facts
- Context-aware conversations
- Document reference

### Research Tool
- Web search integration
- Document analysis
- Multi-source synthesis

### Development Helper
- Code analysis
- Technical documentation
- Problem solving

### Knowledge Base
- Semantic search
- Fact extraction
- Memory persistence

---

## 🔮 Roadmap

- [x] Backend API
- [x] Database & Memory
- [x] Document Search
- [x] Web Search
- [x] React UI
- [x] Session Management
- [x] MemoryPanel
- [x] Loading States
- [x] Error Handling
- [ ] Multi-agent Testing
- [ ] Mobile Optimization
- [ ] Analytics Dashboard
- [ ] User Authentication
- [ ] Cloud Deployment
- [ ] Docker Support

---

**Last Updated:** December 4, 2025  
**Version:** 2.0  
**Status:** Active Development (Week 4/6)

---

**⭐ Star this repo if you find it useful!**