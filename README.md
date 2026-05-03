# English Practice CLI Application

## Purpose
This project is designed for tech-savvy individuals who spend their entire day at a computer but are too "lazy" (or busy!) to open a physical book to study. It aims to bridge the gap between daily work and language learning by integrating vocabulary practice directly into the computer's startup routine. With an interactive dashboard to measure progress, it turns a passive routine into an active learning session.

## Features
- **Auto-Startup Practice**: Automatically prompts a quick 10-word quiz when you start your computer for the first time each day (after 7:00 AM).
- **Type-Aware Translations**: Powered by Typhoon LLM, the system understands the difference between parts of speech (e.g., *act* as a verb vs. *act* as a noun).
- **Interactive Dashboard**: A beautiful Streamlit dashboard with Plotly graphs to track your accuracy and identify words that need more focus.
- **Global Shortcuts**: Launch practice or the dashboard from any terminal using `Practice` or `Dashboard` commands.

## Project Architecture

The application follows a modular architecture consisting of four main layers: **Data Ingestion**, **Storage**, **Application Logic**, and **Infrastructure**.

### High-Level Architecture Diagram
```mermaid
graph TD
    subgraph "Data Layer"
        RAW[oxford.txt] --> CLEANER[clean_and_reset.py]
        CLEANER -- "LLM Cleaning" --> TYPHOON[Typhoon LLM API]
        TYPHOON -- "Structured List" --> CLEANER
        CLEANER --> CLEAN[oxford_clean.txt]
    end

    subgraph "Storage Layer"
        CLEAN --> INGEST[ingest.py]
        INGEST -- "Type-Aware Translation" --> TYPHOON
        INGEST --> DB[(practice.db)]
    end

    subgraph "User Interface Layer"
        DB <--- "Word Data & Stats" ---> APP[app.py / Practice]
        DB <--- "Aggregated Data" ---> DASH[dashboard.py / Dashboard]
    end

    subgraph "Infrastructure Layer"
        SETUP[setup_startup.py] --> REG[Windows Registry]
        SETUP --> PATH[System PATH]
        REG -- "Auto-Run" --> APP
        PATH -- "Global Command" --> APP
        PATH -- "Global Command" --> DASH
    end
```

## Component Interaction

### 1. The Data Pipeline (One-time setup)
- **`clean_and_reset.py`**: The orchestrator. It reads the messy `oxford.txt`, sends chunks to **Typhoon LLM** via `typhoon_utils.py` to fix OCR errors, and saves a perfectly formatted `oxford_clean.txt`.
- **`ingest.py`**: Takes the cleaned text, identifies unique words, and requests **Type-Aware Translations** (e.g., distinguishing between *act* as a noun or verb) before populating the SQLite database.

### 2. Practice & Logic (Daily use)
- **`db_manager.py`**: The "Brain" of the project. It defines the database schema and calculates the **Logical Day** (resetting at 7:00 AM instead of midnight), ensuring you only get prompted once per day.
- **`app.py`**: The core interactive CLI. It fetches words from the DB based on your performance (prioritizing words you struggle with), handles the quiz logic, and updates your statistics in real-time.

### 3. Insights & Visualization
- **`dashboard.py`**: A **Streamlit** application that queries the database to generate interactive **Plotly** charts. It calculates accuracy trends over time and identifies the top 10 "trouble words" for you to focus on.

### 4. Integration & Convenience
- **`setup_startup.py`**: Connects the project to your operating system. It creates global batch file shortcuts (`Practice.bat`, `Dashboard.bat`) and ensures `app.py` is called by Windows every time you log in.

## Installation

### 1. Prerequisites
- Python 3.10 or higher.
- [Conda](https://docs.conda.io/en/latest/) (Recommended).
- A [Typhoon API Key](https://opentyphoon.ai/).

### 2. Setup Environment
```powershell
# Create and activate environment
conda create -n practice-english python=3.10
conda activate practice-english

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
Create a `.env` file in the root directory:
```env
TYPHOON_API_KEY=your_api_key_here
```

### 4. Ingest Vocabulary
Run the cleaning script to process the Oxford 3000 list and populate your database:
```powershell
python clean_and_reset.py
```

### 5. Setup Global Commands and Startup
Run the setup script to enable global commands and auto-startup (Restarting terminal required after this):
```powershell
python setup_startup.py
```

## Usage

### Daily Practice
Simply turn on your computer! If it's after 7 AM and you haven't practiced yet, the CLI will appear. To manually start or force a session from anywhere:
```powershell
Practice
```

### View Progress
To see your learning trends and word statistics:
```powershell
Dashboard
```

### List All Words
To see the full list of ingested vocabulary in the terminal:
```powershell
python list_words.py
```

## Project Structure
- `app.py`: The core CLI practice application.
- `dashboard.py`: Interactive Streamlit dashboard.
- `clean_and_reset.py`: Uses Typhoon LLM to clean raw OCR text and triggers ingestion.
- `db_manager.py`: Handles SQLite database operations and logical day tracking.
- `setup_startup.py`: Configures Windows startup registry and global PATH shortcuts.
- `typhoon_utils.py`: Contains API integration for translation and cleaning.
- `list_words.py`: Utility to view all words in the database.

---
*Happy Learning!*
