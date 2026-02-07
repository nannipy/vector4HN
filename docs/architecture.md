# System Architecture

## Overview
Vector is built with a modular architecture that separates the user interface (TUI), data fetching (Hacker News API), and intelligence (AI Analysis).

```mermaid
graph TD
    User[User] --> TUI[Textual TUI (src/tui.py)]
    TUI --> HN[HN Client (src/hn.py)]
    TUI --> Cache[Local Cache / Reports]
    TUI --> Analyzer[AI Analyzer (src/analyze.py)]
    TUI --> Logger[Logger (src/logger.py)]
    
    HN --> HNAPI[Hacker News API]
    HN --> Trafilatura[Article Extractor]
    Trafilatura --> Website[External Website]
    
    Analyzer --> LLM[LLM Provider (Ollama/Gemini)]
    Analyzer --> Logger
    
    Logger --> LogFiles[Logs & Stats (logs/)]
    
    subgraph Core Components
        TUI
        HN
        Analyzer
        Logger
    end
```

## Component Breakdown

### 1. Textual TUI (`src/tui.py`)
- **Framework**: Built using [Textual](https://textual.textualize.io/), a TUI framework for Python.
- **Screens**:
    - `DashboardScreen`: Main list view of top stories.
    - `ProcessingScreen`: Interstitial loading state.
    - `ReportScreen`: Split display for Analysis and Chat.
    - `ArticleScreen`: Full-text article viewer.
    - `LibraryScreen`: List of saved articles and summaries.
    - `LibraryDetailScreen`: Split display for original article vs. summary report.
    - `SettingsScreen`: Interactive LLM configuration (Provider, Model, API Keys).
- **State Management**: Manages navigation stack and user input.

### 2. Hacker News Client (`src/hn.py`)
- **Asyncio**: Uses `httpx` for asynchronous HTTP requests.
- **BFS Traversal**: Fetches comments using a Breadth-First Search algorithm to prioritize top-level discussions while capturing depth up to a limit (100 comments).
- **Text Extraction**: Uses `trafilatura` to scrape and clean readable text from target URLs, filtering out PDFs and non-text binaries.

### 3. AI Analyzer (`src/analyze.py`)
- **Multi-Provider Support**: Supports local Ollama and cloud-based Google Gemini through a common `LLMProvider` interface.
- **Prompt Engineering**:
    - **Report Generation**: Uses a structured prompt to enforce Markdown headers (Summary, Pros/Cons, etc.).
    - **Contextual Chat**: Feeds the full article text and hierarchical comment tree into the context window for every query.
- **Usage Tracking**: Integrates with the Logger to record token usage and performance metrics.

### 4. Logger (`src/logger.py`)
- **Centralized Logging**: Manages application logs and usage statistics.
- **Usage Statistics**: Exports token usage, model info, and duration to `logs/stats/usage_stats.csv` for analysis.
