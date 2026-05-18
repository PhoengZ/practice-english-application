# Practice English Application - Project Structure

This file provides an overview of the project's architecture and folder structure to assist in development and code analysis.

## Directory Structure

```text
practice-english-application/
├── data/               # Persistent data and raw source files
│   ├── practice.db     # SQLite database (generated)
│   ├── backups/        # SQLite database backups
│   ├── chroma_db/      # Vector database (ChromaDB)
│   ├── oxford.txt      # Raw word list
│   └── ...             # Other PDF/txt source files
├── scripts/            # Utility and maintenance scripts
│   ├── clean_and_reset.py  # Cleans data and re-populates DB & VectorDB
│   ├── seed.py             # Seeds the database with initial data
│   ├── setup_startup.py    # Windows startup integration
│   └── ...                 # Other management scripts
├── src/                # Main Source Code
│   ├── core/           # Business Logic
│   │   ├── ingest.py       # Data ingestion pipeline (SQLite + VectorDB)
│   │   ├── ocr_pdf.py      # PDF processing logic
│   │   └── typhoon_utils.py # LLM API (Typhoon) wrappers
│   ├── database/       # Data Access Layer
│   │   ├── db_manager.py     # SQLite connection and schema
│   │   └── vector_manager.py # ChromaDB & Embedding logic
│   └── ui/             # Presentation Layer
│       ├── app.py          # Main CLI Quiz application (Semantic Search)
│       └── dashboard.py    # Streamlit stats dashboard
├── tests/              # Unit and integration tests
├── .gemini/            # Agent activity logs and memory
├── GEMINI.md           # This file (Project documentation)
├── README.md           # User-facing documentation
└── requirements.txt    # Python dependencies
```

## Core Components

### 1. Data Ingestion (`src/core/`)
- **`ingest.py`**: orchestrates reading cleaned text, calling translation services, and inserting into both **SQLite** and **ChromaDB**.
- **`typhoon_utils.py`**: provides utility functions to interact with the Typhoon LLM for OCR cleaning and word translation.

### 2. Storage Layer (`src/database/`)
- **`db_manager.py`**: centralizes relational database interactions. It defines the schema for `words` and `activity_log`.
- **`vector_manager.py`**: manages the **ChromaDB** vector store and the `sentence-transformers` model used for generating Thai embeddings.

### 3. User Interfaces (`src/ui/`)
- **`app.py`**: The interactive CLI quiz. It uses semantic similarity search via ChromaDB to generate intelligent distractors, making the quiz more educational.
- **`dashboard.py`**: A Streamlit-based dashboard providing visual insights into learning progress using Plotly charts.

## Development Workflow
- **Guidance**: When investigating code, refer to this `GEMINI.md` first to understand component responsibilities.
- **Testing**: New features should be tested manually via the UI scripts or by adding unit tests in a `tests/` directory (if created).
- **Environment**: Always ensure the `TYPHOON_API_KEY` is set in the `.env` file for core logic to function.
