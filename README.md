# Multi-AI Text Knowledge Mining & Knowledge Graph System

An academic project building a production-quality system for extracting structured knowledge from unstructured documents using multiple AI components: NER, LLM-based relationship extraction, embeddings, and knowledge graphs.

## Project Overview

This system ingests documents (PDF, DOCX, TXT) and produces:

1. **Extracted Entities** — Named Entity Recognition with confidence scores
2. **Relationships** — LLM-based relationship extraction with validation
3. **Embeddings** — Semantic embeddings stored in FAISS vector search
4. **Knowledge Graph** — Neo4j graph with entities and relationships
5. **Hybrid Retrieval** — Vector search + graph traversal for Q&A
6. **RAG Chatbot** — Answer questions with source citations
7. **Analytics Dashboard** — Entity/relationship distributions, model metrics

## Architecture

```
Document Upload → Parser → Chunking
       ↓
   ┌───┴─────────────┬─────────────┐
   ↓                 ↓             ↓
NER Model      LLM Relations   Embeddings
   ↓                 ↓             ↓
   └───────────────┬────────────────┘
                   ↓
         Knowledge Validation
                   ↓
           Neo4j + Vector DB
                   ↓
         Hybrid Retrieval + RAG
                   ↓
        React Dashboard / FastAPI
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Python 3.11+, FastAPI, Uvicorn |
| **NLP/ML** | spaCy, Transformers, Sentence-Transformers, scikit-learn |
| **LLM** | OpenAI (configurable; Ollama stub included) |
| **Knowledge Graph** | Neo4j 5.15+ |
| **Vector Store** | FAISS (swappable interface) |
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, React Flow |
| **Infra** | Docker, Docker Compose |

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for local frontend development)

### Option 1: Docker Compose (Recommended)

1. **Clone and configure:**
   ```bash
   cd /path/to/project
   cp .env.example .env
   # Edit .env and fill in OPENAI_API_KEY and other secrets
   ```

2. **Start services:**
   ```bash
   docker-compose up -d
   ```

   This starts:
   - Backend API: `http://localhost:8000`
   - Frontend: `http://localhost:3000`
   - Neo4j: `http://localhost:7474` (username: `neo4j`, password from `.env`)

3. **Verify:**
   ```bash
   curl http://localhost:8000/health
   # Expected: {"status": "healthy", "version": "0.1.0"}
   ```

4. **Access the dashboard:**
   Open `http://localhost:3000` in your browser.

5. **Stop services:**
   ```bash
   docker-compose down
   ```

### Option 2: Local Development

**Backend Setup:**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Create .env with required variables
cp ../.env.example .env

# Run backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend Setup:**

```bash
cd frontend
npm install
npm run dev
# Opens http://localhost:5173
```

**Neo4j Setup (local):**

```bash
docker run -d \
  --name neo4j \
  -p 7687:7687 \
  -p 7474:7474 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5.15-community

# Access at http://localhost:7474
```

## Project Roadmap & Implementation Status

### 🚀 Progress Summary

```
[Phase 1-3: Core Foundation & Ingestion]  ➔ COMPLETED  ✅
[Phase 4-6: AI & Entity Processing]       ➔ UPCOMING   ⏳
[Phase 7-10: Graph, Vectors & RAG]       ➔ UPCOMING   ⏳
```

### ✅ Completed Functionality (Phases 1–3 + Frontend Bridge)

- [x] **Phase 1: Foundation & Infrastructure**
  - FastAPI application structure with async lifespan management.
  - Asynchronous SQLite persistent database layer using SQLAlchemy and `aiosqlite`.
  - Mounted all 6 API routers: `/api/documents`, `/api/chunks`, `/api/knowledge`, `/api/search`, `/api/chat`, `/api/analytics`.
  - Architecture packages initialized: `app/ai/`, `app/graph/`, `app/vector/`, `app/pipelines/`.
  - Structured logging with automatic `logs/` directory creation.
- [x] **Phase 2: Document Ingestion & Extraction**
  - Binary signature (magic bytes) validation and file size limits (50 MB max).
  - Multi-format text extraction: PDF (`PyPDF2`), Word documents (`python-docx`), and plain text (`txt`).
  - Text cleaning: Unicode control character removal, whitespace normalization, and newline preservation.
  - Document metadata tracking (character counts, page counts, processing status).
- [x] **Phase 3: Text Chunking Engine & Quality Scoring**
  - **Fixed-size Chunking**: Configurable size and overlap with sentence-boundary detection (`.!?`).
  - **Semantic Sentence Chunking**: Groups complete sentences up to target token/character limits.
  - **Sliding Window Chunking**: Overlapping fixed-step text segmentation.
  - **Quality Scoring (0.0 to 1.0)**: Evaluates length balance, sentence completeness, and token distribution.
  - Chunk search API with text substring query and metadata filters.
- [x] **Frontend–Backend Integration**
  - Axios API client service layer ([`frontend/src/services/api.ts`](file:///d:/MultiAITextKnowledgeMining-main/MultiAITextKnowledgeMining-main/frontend/src/services/api.ts)) routed via Vite proxy.
  - Real-time React Context integration with local fallback support.
  - Document Intake page with HTML5 drag-and-drop, upload progress, live text extraction preview, and manual chunking actions.
- [x] **Test Suite & Reliability**
  - **178 unit tests passing** covering document CRUD, text cleaning, PDF/DOCX/TXT extraction, and chunking strategies.
  - **28 integration tests passing** covering chunk and document REST endpoints.

---

### ⏳ Remaining Functionality (Upcoming Phases)

- [ ] **Phase 4: Named Entity Recognition (NER)**
  - Implement spaCy pipeline (`en_core_web_sm`) in `app/ai/ner_service.py`.
  - Extract entity mentions (`PERSON`, `ORG`, `GPE`, `DATE`, `MONEY`, `PRODUCT`) with confidence scores and character offsets.
- [ ] **Phase 5: LLM Relationship Extraction**
  - OpenAI / Ollama client integration for relationship triplet extraction (`Subject ➔ Relation ➔ Object`).
  - Prompt engineering for entity linking and confidence estimation.
- [ ] **Phase 6: Knowledge Validation Layer**
  - Deduplication and entity resolution (merging synonymous mentions).
  - Relationship consistency validation against schemas.
- [ ] **Phase 7: Neo4j Knowledge Graph**
  - Connect `app/graph/` to Neo4j instance using Cypher queries.
  - Store entity nodes and labeled relationship edges.
  - Frontend interactive graph visualization using React Flow.
- [ ] **Phase 8: FAISS Vector Embeddings**
  - Generate sentence embeddings using `sentence-transformers/all-MiniLM-L6-v2`.
  - Build and persist FAISS index for chunk vector similarity search.
- [ ] **Phase 9: Hybrid Search & Retrieval**
  - Combine vector similarity search with Neo4j graph neighborhood traversal.
- [ ] **Phase 10: RAG Chatbot**
  - Conversational Q&A interface grounding answers in graph evidence and source chunk citations.
- [ ] **Phase 11–14: Hardening, Evaluation & Deployment**
  - Precision/recall metrics, containerized CI/CD, and production deployment scripts.

## API Endpoints

### Documents
- `GET /api/documents/` — List documents
- `POST /api/documents/upload` — Upload document
- `GET /api/documents/{id}` — Get document details
- `GET /api/documents/{id}/status` — Get processing status

### Knowledge Graph
- `GET /api/knowledge/entities` — List entities
- `GET /api/knowledge/entities/{id}` — Get entity
- `GET /api/knowledge/relationships` — List relationships
- `GET /api/knowledge/graph` — Get full graph
- `GET /api/knowledge/neighbors/{entity_id}` — Get entity neighbors
- `GET /api/knowledge/path` — Find paths

### Search
- `POST /api/search/semantic` — Semantic search
- `POST /api/search/hybrid` — Hybrid vector + graph search

### Chat
- `POST /api/chat/` — Ask question with RAG

### Analytics
- `GET /api/analytics/summary` — Overall metrics
- `GET /api/analytics/entities` — Entity distribution
- `GET /api/analytics/relationships` — Relationship distribution
- `GET /api/analytics/performance` — Model metrics

## Configuration

All configuration is in `.env`. Key variables:

```bash
# LLM Provider
LLM_PROVIDER=openai  # or "ollama"
LLM_MODEL=gpt-4
OPENAI_API_KEY=sk-...

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password

# Embeddings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Processing
CHUNK_SIZE=512
CHUNK_OVERLAP=50
CONFIDENCE_THRESHOLD=0.7
```

See `.env.example` for all options.

## Development

### Code Quality

```bash
# Backend
cd backend
black .
flake8 .
mypy .
pytest

# Frontend
cd frontend
npm run lint
npm run type-check
```

### Testing

```bash
# Backend unit tests (Phase 1 setup only)
cd backend
pytest tests/unit/ -v

# Backend integration tests (Phase 2+)
pytest tests/integration/ -v
```

## Security Notes

- **Never commit `.env` files** — use `.env.example` as template
- All file uploads are validated by content, not extension
- All database queries use parameterized statements (no SQL injection)
- No credentials logged anywhere
- Document processing treats all input as untrusted

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI entry
│   │   ├── core/
│   │   │   ├── config.py          # Settings
│   │   │   └── logging.py         # Structured logging
│   │   ├── api/routes/            # Endpoints (Phase 2+)
│   │   ├── models/                # Pydantic models (Phase 2+)
│   │   ├── services/              # Business logic (Phase 2+)
│   │   ├── ai/                    # ML/LLM components (Phase 4+)
│   │   ├── graph/                 # Neo4j client (Phase 7+)
│   │   ├── vector/                # Vector store (Phase 8+)
│   │   ├── pipelines/             # Orchestration (Phase 2+)
│   │   └── utils/                 # Helpers
│   ├── tests/
│   │   ├── unit/                  # Unit tests
│   │   └── integration/           # Integration tests
│   └── requirements.txt           # Python deps (pinned)
├── frontend/
│   ├── src/
│   │   ├── components/            # React components
│   │   ├── pages/                 # Page routes
│   │   ├── services/              # API clients
│   │   ├── hooks/                 # React hooks
│   │   ├── types/                 # TypeScript types
│   │   └── utils/                 # Helpers
│   ├── package.json              # npm deps (pinned)
│   └── tsconfig.json             # TypeScript config
├── docker/
│   ├── Dockerfile.backend        # Backend image
│   └── Dockerfile.frontend       # Frontend image
├── docker-compose.yml            # Service orchestration
├── .env.example                  # Config template
└── README.md                     # This file
```

## Contributing

1. Follow incremental, phase-based development
2. Write type hints (Python) and TypeScript for all code
3. Test incrementally — no phase proceeds until tests pass
4. Never fabricate metrics or test results
5. Pin all dependency versions
6. Document all major functions

## Phase 1 Status

✅ **Complete:**
- Project scaffolding with correct directory structure
- FastAPI backend skeleton with health check
- React + Vite + TypeScript frontend skeleton
- Docker & Docker Compose for all services
- `.env.example` with all configurable options
- `requirements.txt` with pinned versions
- README with setup instructions

**Next Phase:** Document upload & text extraction (Phase 2)

## License

Academic Project — 7th Semester

## Contact

For questions, refer to the specification document included with this project.

---

**Development Notes:**

- All code includes type hints and docstrings
- Async/await for I/O-bound operations
- Dependency injection for testability
- Parameterized queries for safety
- Structured logging (no secrets logged)
- Error handling without stack traces in responses
- CORS configured for frontend + APIs
- Health checks on all services
