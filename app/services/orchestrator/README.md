# 🧠 Intelligent Orchestrator

Production-ready AI query orchestration system with fault tolerance, caching, and rate limiting.

## 📊 Overview

The Orchestrator coordinates multiple AI agents to process queries intelligently:
```
User Query → Analyze → Evaluate Memory → Decide Strategy → Generate Response
```

**Key Features:**
- 🎯 Smart routing (direct/enhanced/deep reasoning)
- 💾 Response caching (LRU with TTL)
- 🔄 Retry with exponential backoff
- ⚡ Circuit breaker for fault tolerance
- 🚦 Rate limiting per user
- 🛡️ Edge case handling

---

## 🏗️ Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                    IntelligentOrchestrator                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │QueryAnalyzer│→ │MemoryEval  │→ │DecisionEng │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│         │                                  │                    │
│         ▼                                  ▼                    │
│  ┌─────────────┐              ┌────────────────────┐           │
│  │EdgeCaseHndl │              │  Strategy Router   │           │
│  └─────────────┘              ├────────────────────┤           │
│                               │ direct → Memory    │           │
│  ┌─────────────┐              │ enhanced → AI      │           │
│  │ResponseCache│              │ deep → Reasoning   │           │
│  └─────────────┘              └────────────────────┘           │
│                                          │                      │
│  ┌─────────────┐  ┌─────────────┐       ▼                      │
│  │CircuitBreak │  │ RateLimiter │  ┌─────────────┐             │
│  └─────────────┘  └─────────────┘  │ResponseFmt  │             │
│                                     └─────────────┘             │
│  ┌─────────────┐                                                │
│  │RetryHandler │                                                │
│  └─────────────┘                                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📦 Components

### Core Components

| Component | Purpose | Coverage |
|-----------|---------|----------|
| `QueryAnalyzer` | Analyze query complexity & intent | 100% |
| `MemoryEvaluator` | Check memory coverage | 100% |
| `DecisionEngine` | Select response strategy | 100% |
| `ResponseFormatter` | Format final response | 100% |
| `ReasoningPlanner` | Multi-step reasoning plans | 100% |
| `SynthesisEngine` | Multi-source synthesis | 100% |

### Production Components

| Component | Purpose | Coverage |
|-----------|---------|----------|
| `ResponseCache` | LRU cache with TTL | 100% |
| `EdgeCaseHandler` | Handle ambiguity, conflicts, timeouts | 98.73% |
| `CircuitBreaker` | Fault tolerance | 100% |
| `RateLimiter` | Request rate control | 100% |
| `RetryHandler` | Retry with backoff | 100% |

---

## 🚀 Quick Start

### Basic Usage
```python
from app.services.orchestrator import (
    ResponseCache,
    CircuitBreaker,
    RateLimiter,
    RetryHandler,
)

# Initialize components
cache = ResponseCache(max_size=100, ttl_seconds=3600)
breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=30)
limiter = RateLimiter(max_requests=10, window_seconds=60)
retry = RetryHandler(max_retries=3, exponential_backoff=True)
```

---

## 📖 Component Reference

### ResponseCache

LRU cache for orchestrator responses with TTL expiration.
```python
cache = ResponseCache(max_size=100, ttl_seconds=3600)

# Store response
cache.set("What is my name?", {"answer": "Denis"}, context={"user_id": "123"})

# Retrieve (returns None if expired/missing)
result = cache.get("What is my name?", context={"user_id": "123"})

# Get statistics
stats = cache.get_stats()
# {"hits": 10, "misses": 2, "hit_rate": 0.83, "size": 50, "max_size": 100}

# Clear cache
cache.clear()
```

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_size` | int | 100 | Maximum cached items |
| `ttl_seconds` | int | 3600 | Time-to-live in seconds |

---

### CircuitBreaker

Prevents cascade failures using circuit breaker pattern.
```python
breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=30)

# Execute with circuit breaker
try:
    result = breaker.call(lambda: external_api_call())
except CircuitOpenError:
    # Circuit is open, use fallback
    result = fallback_response()

# Check state
breaker.check_state()  # Updates state based on timeout

# Get statistics
stats = breaker.get_stats()
# {"state": "closed", "failure_count": 2, "failure_threshold": 5}
```

**States:**
- `CLOSED` - Normal operation, requests pass through
- `OPEN` - Too many failures, requests blocked
- `HALF_OPEN` - Testing if service recovered

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `failure_threshold` | int | 5 | Failures before opening |
| `recovery_timeout` | float | 30.0 | Seconds before half-open |

---

### RateLimiter

Sliding window rate limiting per user/key.
```python
limiter = RateLimiter(max_requests=10, window_seconds=60)

# Check if allowed
if limiter.is_allowed("user_123"):
    process_request()
else:
    raise RateLimitExceeded()

# Get statistics
stats = limiter.get_stats("user_123")
# {"requests_count": 8, "max_requests": 10, "remaining": 2}
```

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_requests` | int | 10 | Max requests in window |
| `window_seconds` | float | 60.0 | Sliding window size |

---

### RetryHandler

Retry failed operations with optional exponential backoff.
```python
retry = RetryHandler(max_retries=3, base_delay=1.0, exponential_backoff=True)

# Execute with retry
result = retry.execute(lambda: unreliable_operation())

# Get statistics
stats = retry.get_stats()
# {"total_attempts": 2, "retries_used": 1, "max_retries": 3, "success": True}
```

**Backoff Delays (with exponential=True):**
- Attempt 1: 1.0s
- Attempt 2: 2.0s
- Attempt 3: 4.0s

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_retries` | int | 3 | Maximum retry attempts |
| `base_delay` | float | 1.0 | Base delay in seconds |
| `exponential_backoff` | bool | False | Double delay each retry |

---

### EdgeCaseHandler

Handles edge cases in query processing.
```python
handler = EdgeCaseHandler()

# Detect ambiguous queries
result = handler.detect_ambiguity("What about it?")
# AmbiguityResult(is_ambiguous=True, reason="Unclear reference: 'it'")

# Detect conflicting facts
facts = [
    {"text": "User lives in Moscow"},
    {"text": "User lives in Tokyo"},
]
result = handler.detect_conflicts(facts)
# ConflictResult(has_conflicts=True, conflicts=[...])

# Evaluate memory gaps
result = handler.evaluate_memory_gap("What is my color?", facts=[])
# MemoryGapResult(has_gap=True, suggestion="web_search")

# Create timeout response
result = handler.create_timeout_response(
    partial_response="Based on...",
    elapsed_time=15.5,
    timeout_limit=15.0
)
# TimeoutResult(is_timeout=True, message="Operation timeout...")
```

---

## 🎯 Response Strategies

### Strategy Selection Flow
```
Query Analysis
     │
     ▼
┌─────────────┐
│ Coverage ≥  │──Yes──▶ DIRECT (free, ~100ms)
│ 0.9 + simple│         └─ Answer from memory only
└─────────────┘
     │ No
     ▼
┌─────────────┐
│ Coverage ≥  │──Yes──▶ ENHANCED (~$0.0003, ~3s)
│ 0.7 + medium│         └─ Memory + AI agent
└─────────────┘
     │ No
     ▼
DEEP_REASONING (~$0.005, ~15s)
└─ Memory + Web Search + Premium AI
```

### Strategy Comparison

| Strategy | Cost | Time | Use Case |
|----------|------|------|----------|
| Direct | $0 | ~100ms | Simple facts in memory |
| Enhanced | ~$0.0003 | ~3s | Moderate complexity |
| Deep Reasoning | ~$0.005 | ~15s | Complex analysis |

---

## 📈 Metrics & Monitoring

### OrchestratorMetrics
```python
metrics = OrchestratorMetrics()

# Track query
metrics.track_query(
    strategy="enhanced",
    elapsed_time_ms=2500,
    cost_usd=0.0003
)

# Get statistics
stats = metrics.get_stats()
```

---

## 🧪 Testing
```bash
# Run all orchestrator tests
python -m pytest tests/services/orchestrator/ tests/unit/services/orchestrator/ -v

# Check coverage
python -m pytest tests/services/orchestrator/ tests/unit/services/orchestrator/ \
  --cov=app.services.orchestrator \
  --cov-report=term-missing

# Run specific component tests
python -m pytest tests/services/orchestrator/test_circuit_breaker.py -v
```

**Current Status:**
- Tests: 148 passing
- Coverage: 99%+
- Components at 100%: 10

---

## 📋 Configuration

### Environment Variables
```bash
# Cache settings
CACHE_MAX_SIZE=100
CACHE_TTL_SECONDS=3600

# Circuit breaker
CIRCUIT_FAILURE_THRESHOLD=5
CIRCUIT_RECOVERY_TIMEOUT=30

# Rate limiting
RATE_LIMIT_MAX_REQUESTS=10
RATE_LIMIT_WINDOW_SECONDS=60

# Retry settings
RETRY_MAX_ATTEMPTS=3
RETRY_BASE_DELAY=1.0
RETRY_EXPONENTIAL=true
```

---

## 🔗 Related Documentation

- [Architecture Overview](../../../docs/architecture.md)
- [API Reference](../../../docs/api.md)
- [Deployment Guide](../../../docs/deployment.md)

---

**Last Updated:** December 26, 2025  
**Version:** 2.0.0  
**Status:** Production Ready ✅