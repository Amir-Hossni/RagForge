<div align="center">

# RagLoom

**A modular Retrieval-Augmented Generation (RAG) backend built with FastAPI.**

Ingest documents and web pages, split them into chunks, store them, and (soon) answer questions grounded in your own data.

![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.141-009688?logo=fastapi&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-PyMongo%20Async-47A248?logo=mongodb&logoColor=white)
![Qdrant](https://img.shields.io/badge/Vector%20DB-Qdrant-DC244C)
![uv](https://img.shields.io/badge/Package%20Manager-uv-DE5FE9)
![Status](https://img.shields.io/badge/Status-Work%20in%20Progress-orange)

</div>

---

## Table of Contents

- [Overview](#overview)
- [Project Status](#project-status)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Supported Sources](#supported-sources)
- [Security](#security)
- [Roadmap](#roadmap)
- [License](#license)

---

## Overview

RagLoom is a backend service that prepares your data for Retrieval-Augmented Generation.
It is organized around **projects**: each project owns a set of **assets** (uploaded files or web URLs) that are
processed into **chunks** and stored in MongoDB, ready to be embedded into a vector database and used to answer questions.

The codebase is built around pluggable providers, so LLMs and vector databases can be swapped through configuration:

- **LLM providers** — OpenAI, Cohere, Google Gemini, NVIDIA NIM, Ollama (local) and Anthropic (generation only) behind a common async interface and factory.
- **Vector DB providers** — Qdrant behind a common interface and factory.
- **Loaders** — local files (TXT, Markdown, PDF, EPUB) and remote URLs (HTML, PDF, plain text) fetched in memory.

---

## Project Status

> **This project is under active development.** The ingestion pipeline is functional; retrieval and answer generation are next.

| Stage | Component | Status |
|:-----:|-----------|:------:|
| 1 | File upload & validation | ✅ Done |
| 2 | URL ingestion (in-memory, no download to disk) | ✅ Done |
| 3 | Text extraction & chunking | ✅ Done |
| 4 | Chunk storage in MongoDB | ✅ Done |
| 5 | LLM providers (OpenAI, Cohere, Google, NVIDIA, Ollama, Anthropic) | ✅ Implemented — not wired to endpoints yet |
| 6 | Vector DB provider (Qdrant) | ✅ Implemented — not wired to endpoints yet |
| 7 | Indexing chunks into the vector DB | 🚧 Planned |
| 8 | Semantic search endpoint | 🚧 Planned |
| 9 | RAG answer generation endpoint | 🚧 Planned |

---

## Architecture

```mermaid
flowchart LR
    subgraph Ingestion["Ingestion ✅"]
        A[Upload file] --> C[Assets<br/>MongoDB]
        B[Add URL] --> C
        C --> D{Loader}
        D -->|TXT / MD| E[load_text_file]
        D -->|PDF / EPUB| F[load_pymupdf_file]
        D -->|HTML / PDF / TXT URL| G[get_url_content<br/>in memory]
        E & F & G --> H[RecursiveCharacterTextSplitter]
        H --> I[(Chunks<br/>MongoDB)]
    end

    subgraph Retrieval["Retrieval & Generation 🚧"]
        I -.-> J[Embedding<br/>OpenAI / Cohere / Google / NVIDIA / Ollama]
        J -.-> K[(Qdrant)]
        Q[User question] -.-> K
        K -.-> L[LLM<br/>OpenAI / Cohere / Google / NVIDIA / Ollama / Anthropic]
        L -.-> R[Answer]
    end
```

The code follows a layered structure:

| Layer | Responsibility |
|-------|----------------|
| `routes/` | HTTP endpoints and request schemas |
| `controllers/` | Business logic: validation, file paths, loading and chunking |
| `models/` | MongoDB data access (projects, assets, chunks), schemas and enums |
| `stores/` | Pluggable providers: LLMs and vector databases (interface + factory + providers) |
| `helper/` | Application settings loaded from `.env` |

---

## Tech Stack

| Category | Technology |
|----------|------------|
| Web framework | FastAPI, Uvicorn |
| Database | MongoDB (PyMongo Async API) |
| Vector database | Qdrant (`qdrant-client`) |
| LLM / Embeddings | OpenAI, Cohere (V2 API), Google Gemini (`google-genai`), NVIDIA NIM, Ollama, Anthropic — all async |
| Document parsing | PyMuPDF |
| Web extraction | httpx, trafilatura |
| Chunking | `langchain-text-splitters` |
| Validation & settings | Pydantic v2, pydantic-settings |
| Package management | uv |

---

## Project Structure

```text
ragloom/
├── Docker/
│   ├── docker.compose.yaml        # MongoDB service
│   └── .env.example
├── src/rag_app/
│   ├── main.py                    # FastAPI app + lifespan (DB and LLM clients)
│   ├── helper/
│   │   └── config.py              # Settings (pydantic-settings)
│   ├── routes/
│   │   ├── base.py                # GET /api/v1/
│   │   ├── data.py                # upload / upload-url / process
│   │   └── schemes/data.py        # Request bodies
│   ├── controllers/
│   │   ├── DataController.py      # Upload validation, unique file paths
│   │   ├── ProjectController.py   # Project folders on disk
│   │   └── ProcessController.py   # File & URL loading (in memory, SSRF protected) + chunking
│   ├── models/
│   │   ├── ProjectModel.py | AssetModel.py | ChunkModel.py
│   │   ├── db_schemes/            # Pydantic schemas for MongoDB documents
│   │   └── enums/                 # Response signals, asset types, extensions, content types
│   ├── stores/
│   │   ├── llm/                   # LLM interface, factory, errors and 6 providers
│   │   └── vectorDB/              # Vector DB interface, factory, Qdrant provider
│   └── assets/                    # Uploaded files, local vector DB, Postman collection
├── .env.example
├── pyproject.toml
└── uv.lock
```

---

## Getting Started

### Prerequisites

- **Python 3.14**
- **[uv](https://docs.astral.sh/uv/)** package manager
- **Docker** (to run MongoDB), or any reachable MongoDB instance

### 1. Clone and install

```bash
git clone <repository-url>
cd ragloom

# creates .venv and installs all dependencies from uv.lock
uv sync
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Then edit `.env` and set your values (see [Configuration](#configuration)).

### 3. Start MongoDB

```bash
cd Docker
cp .env.example .env              # set MONGO_INITDB_ROOT_USERNAME / PASSWORD
docker compose -f docker.compose.yaml up -d
```

> If MongoDB authentication is enabled, include the credentials in `MONGODB_URI`, e.g. `mongodb://user:password@localhost:27017`.

### 4. Run the API server

From the project root (where `.env` lives):

```bash
uv run uvicorn rag_app.main:app --reload --host 0.0.0.0 --port 5000
```

Interactive API docs will be available at:

- Swagger UI — http://localhost:5000/docs
- ReDoc — http://localhost:5000/redoc

---

## Configuration

All settings are read from `.env` in the project root. Empty values are treated as unset.

### Application & files

| Variable | Description | Example |
|----------|-------------|---------|
| `APP_NAME` | Application name | `"RagLoom"` |
| `APP_VERSION` | Application version | `"0.1"` |
| `FILE_ALLOWED_TYPES` | Allowed upload MIME types | `["text/plain", "application/pdf", "text/markdown", "application/epub+zip"]` |
| `FILE_MAX_SIZE` | Max upload / URL content size in **MB** | `10` |
| `FILE_DEFAULT_CHUNK_SIZE` | Read buffer size when saving uploads (bytes) | `512000` |

### Database

| Variable | Description | Example |
|----------|-------------|---------|
| `MONGODB_URI` | MongoDB connection string | `"mongodb://localhost:27017"` |
| `MONGODB_DATABASE` | Database name | `"mini_rag"` |

### LLM providers

| Variable | Description | Example |
|----------|-------------|---------|
| `GENERATION_BACKEND` | Provider for text generation | `OPENAI`, `COHERE`, `GOOGLE`, `NVIDIA`, `OLLAMA` or `ANTHROPIC` |
| `EMBEDDING_BACKEND` | Provider for embeddings | `OPENAI`, `COHERE`, `GOOGLE`, `NVIDIA` or `OLLAMA` (Anthropic has no embeddings API) |
| `OPENAI_API_KEY` | OpenAI API key | |
| `OPENAI_API_URL` | Optional custom base URL (OpenAI-compatible servers) | |
| `COHERE_API_KEY` | Cohere API key | |
| `GOOGLE_API_KEY` | Google Gemini API key | |
| `ANTHROPIC_API_KEY` | Anthropic API key | |
| `NVIDIA_API_KEY` | NVIDIA NIM API key | |
| `NVIDIA_API_URL` | NVIDIA NIM endpoint | `https://integrate.api.nvidia.com/v1` |
| `OLLAMA_API_URL` | Local Ollama server (no API key needed) | `http://localhost:11434` |
| `GENERATION_MODEL_ID` | Generation model name | |
| `EMBEDDING_MODEL_ID` | Embedding model name | |
| `EMBEDDING_MODEL_SIZE` | Embedding vector dimension | `1024` |
| `INPUT_DEFAULT_MAX_CHARACTERS` | Max characters per text sent for **embedding** (generation prompts are never truncated) | `1024` |
| `GENERATION_DEFAULT_MAX_TOKENS` | Default max output tokens | `200` |
| `GENERATION_DEFAULT_TEMPERATURE` | Default temperature | `0.7` |

> **Provider notes**
> - The factory fails at **startup** with a clear error if the provider name is unknown or its API key is missing.
> - **Anthropic** has no embeddings API, so it can only be used as `GENERATION_BACKEND`. The current Anthropic SDK no longer exposes sampling parameters, so `GENERATION_DEFAULT_TEMPERATURE` is ignored for it.
> - **NVIDIA** and **Google** embedding models are asymmetric: documents and queries are embedded differently (handled automatically).
> - Embeddings are sent in batches within each vendor's limit (OpenAI 2048, Google 100, Cohere 96, NVIDIA 50 texts per request).

#### Adding a new LLM provider

All shared logic (model checks, defaults, chat history, batching, truncation, vector validation) lives in `LLMinterface`. A new provider only writes the vendor-specific parts:

1. Add the name to `LLMEnums` and a role enum (like `OpenAIEnums`) in `stores/llm/LLMEnums.py`.
2. Create `stores/llm/providers/<Name>Provider.py`, subclass `LLMinterface`, set `PROVIDER_NAME` and `ROLES`, create the SDK client in `__init__`, and implement:
   - `_generate_text(messages, max_output_tokens, temperature)` — call the vendor, return the text, raise `LLMProviderError` on failure.
   - `_embed_text(texts, document_type)` — embed one batch, return the vectors, raise `EmbeddingError` on failure.
3. Set `embedding_batch_size` if the vendor limits texts per request, and override `aclose()` if its client does not expose `close()`.
4. Export it in `providers/__init__.py`, add a branch in `LLMProviderFactory`, and add its settings to `helper/config.py` and `.env.example`.

### Vector database

| Variable | Description | Example |
|----------|-------------|---------|
| `VECTOR_DB_BACKEND` | Vector DB provider | `"QDRANT"` |
| `VECTOR_DB_PATH` | Local storage folder name (under `assets/db/`) | `"qdrant_db"` |
| `VECTOR_DB_DISTANCE_METRIC` | Similarity metric | `"cosine"` or `"dot"` |

### URL loader

| Variable | Description | Default |
|----------|-------------|---------|
| `URL_REQUEST_TIMEOUT` | Request timeout in seconds | `15` |
| `URL_MAX_REDIRECTS` | Max redirects to follow (each hop is validated) | `5` |

---

## API Reference

Base URL: `http://localhost:5000/api/v1`

Every response carries a `signal` field describing the outcome. `project_id` must be **alphanumeric**; a project is created automatically on first use.

### Health

```http
GET /api/v1/
```

```json
{ "app_name": "RagLoom", "app_version": "0.1" }
```

### Upload a file

```http
POST /api/v1/data/upload/{project_id}
Content-Type: multipart/form-data
```

```bash
curl -X POST "http://localhost:5000/api/v1/data/upload/project1" \
     -F "file=@./document.pdf"
```

```json
{ "signal": "file_upload_success", "file_id": "6ac2825eee10bcf8b9b9578a" }
```

### Add a URL

The URL is stored as an asset only. Its content is fetched **in memory** during processing and never written to disk.

```http
POST /api/v1/data/upload-url/{project_id}
Content-Type: application/json
```

```bash
curl -X POST "http://localhost:5000/api/v1/data/upload-url/project1" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://docs.python.org/3/tutorial/introduction.html"}'
```

```json
{ "signal": "url_added_success", "file_id": "6ac2825eee10bcf8b9b95795" }
```

### Process assets into chunks

```http
POST /api/v1/data/process/{project_id}
Content-Type: application/json
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `file_id` | string | `null` | Asset id (from upload) or asset name. Omit to process **all** project assets |
| `chunk_size` | int | `100` | Max characters per chunk (`> 0`) |
| `overlap_size` | int | `20` | Overlapping characters between chunks (`< chunk_size`) |
| `do_reset` | int | `0` | `1` deletes **all** of the project's chunks before processing |

```bash
curl -X POST "http://localhost:5000/api/v1/data/process/project1" \
     -H "Content-Type: application/json" \
     -d '{"chunk_size": 500, "overlap_size": 50, "do_reset": 1}'
```

```json
{ "signal": "processing_success", "inserted_chunks": 61, "processed_files": 3 }
```

**Processing behavior**

- **Idempotent re-processing** — processing an asset again **replaces** its previous chunks instead of duplicating them, so you can re-run with a different `chunk_size` without `do_reset`.
- **Safe on failure** — an asset's old chunks are removed only after its new chunks were generated successfully. If an asset fails, its previous chunks are kept.
- **Partial success** — assets that fail (unreachable URL, unsupported or corrupted file) are skipped and logged; the request fails only if **no** asset could be processed.
- **`do_reset=1`** clears the whole project first, so chunks of assets that fail in that run are not restored.

### Response signals

| Signal | Meaning |
|--------|---------|
| `file_upload_success` | File stored and registered as an asset |
| `file_type_not_supported` | MIME type not in `FILE_ALLOWED_TYPES` |
| `file_size_exceeded` | File larger than `FILE_MAX_SIZE` |
| `file_empty` | Uploaded file is empty |
| `file_uploaded_failed` | Error while writing the file |
| `url_added_success` | URL registered as an asset |
| `url_already_exists` | URL already registered in this project (existing id returned) |
| `url_not_allowed` | URL rejected (non-public address or unresolvable host) |
| `processing_success` | Chunks created and stored |
| `processing_failed` | No asset could be processed |
| `not_found_files` | Project has no assets |
| `no_file_found_with_this_id` | `file_id` does not exist in this project |
| `project_id_must_be_alphanumeric` | Invalid `project_id` |

A Postman collection is available at [`src/rag_app/assets/mini-rag-app.postman_collection.json`](src/rag_app/assets/mini-rag-app.postman_collection.json).

---

## Supported Sources

| Source | Formats | `ProcessController` method | Notes |
|--------|---------|--------|-------|
| Local file | `.txt`, `.md` | `load_text_file` | UTF-8. Extensions are case-insensitive (`.PDF` = `.pdf`) |
| Local file | `.pdf`, `.epub` | `load_pymupdf_file` (PyMuPDF) | One document per page with page metadata |
| URL | HTML pages | `load_html_content` (trafilatura) | Main content only (menus, footers and ads are removed); title, author, date and site name kept as metadata |
| URL | PDF | `load_pdf_content` (PyMuPDF) | Parsed from memory |
| URL | Plain text / Markdown | `load_text_content` | Decoded using the response charset |

> **Note:** some clients upload `.md` files as `application/octet-stream`. Add that MIME type to `FILE_ALLOWED_TYPES` if needed.
> Pages rendered entirely by JavaScript (SPAs) are not supported yet.

---

## Security

User-supplied URLs are a common **SSRF** (Server-Side Request Forgery) vector. `ProcessController.validate_public_url` and `fetch_url` apply these protections:

- Only `http` and `https` schemes are accepted.
- The hostname is resolved and **every** resolved IP must be public — loopback, private, link-local (including cloud metadata `169.254.169.254`) and reserved ranges are rejected, as well as tricks like decimal IPs (`http://2130706433`).
- Redirects are followed manually and **each hop is re-validated**.
- Response size is limited by `FILE_MAX_SIZE` while streaming, and requests are bounded by a timeout.

> Known limitation: the connection is not pinned to the validated IP, so a DNS-rebinding attack remains theoretically possible. Pinning the IP in the HTTP transport is on the roadmap.

---

## Roadmap

- [ ] Wire LLM and vector DB providers into the application lifespan
- [ ] Index chunks into Qdrant (`/nlp/index/push/{project_id}`)
- [ ] Semantic search endpoint (`/nlp/index/search/{project_id}`)
- [ ] RAG answer endpoint with prompt templates (`/nlp/index/answer/{project_id}`)
- [ ] Remove a project's vectors when `do_reset=1`
- [ ] More loaders: DOCX, CSV / JSON, YouTube transcripts, OCR for scanned PDFs
- [ ] Encoding auto-detection for non UTF-8 text files
- [ ] Pin URL connections to the validated IP (DNS-rebinding protection)
- [ ] Create MongoDB indexes once at startup (indexes are currently created only when a collection is first created)
- [ ] Automated tests and CI
- [ ] Dockerfile for the API service

---

## License

License to be defined.

> This project depends on **PyMuPDF**, which is licensed under **AGPL-3.0** (a commercial license is available from Artifex). Take this into account when choosing a license or deploying the service.

---

<div align="center">

Made by **Amir Hossni**

</div>
