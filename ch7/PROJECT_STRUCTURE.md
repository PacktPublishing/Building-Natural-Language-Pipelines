# Recommended Project Structure

```
ch7/
├── pyproject.toml                    # Project dependencies
├── uv.lock                          # Lockfile
├── README.md
├── .env.example                     # Environment template
├── .env                            # Local environment (gitignored)
├── docker-compose.yml              # Full stack with Qdrant storage
├── docker-compose.local.yml        # Local dev configuration
├── Dockerfile                      # Application container
├── scripts/
│   ├── setup_local.sh             # Local setup script
│   ├── run_indexing.sh            # Standalone indexing
│   └── run_api.sh                 # Standalone API
├── src/                           # Main application code
│   ├── __init__.py
│   ├── app.py                     # FastAPI application
│   ├── config.py                  # Configuration management
│   └── rag/
│       ├── __init__.py
│       ├── indexing.py           # Indexing pipeline
│       ├── hybridrag.py          # RAG component
│       ├── naiverag.py
│       └── pretty_print.py
├── tests/
│   ├── __init__.py
│   ├── test_api.py               # API tests
│   └── test_rag.py               # RAG tests
└── docs/
    ├── local_setup.md
    └── docker_setup.md
```
