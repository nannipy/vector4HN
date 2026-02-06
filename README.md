# Vector - Hacker News Deep Dive Assistant

Vector is a terminal-based tool that allows you to browse Hacker News, analyze articles and discussions using local LLMs (via Ollama), and engage in deep-dive chats about the content.

## 🚀 Features

-   **Live Feed:** Fetches the top 30 stories from Hacker News.
-   **Automated Analysis:** Extracts article content and summarizes the top 100 comments.
-   **AI Reports:** Generates structured reports covering summaries, pros/cons, sentiment, and deep-dive hooks.
-   **Contextual Chat:** Ask follow-up questions about any article or discussion thread using a structured context-aware prompt.
-   **Comment Hierarchy:** Chat context includes nested comments (up to 100) to preserve conversation structure.
-   **Local AI:** Powered by Ollama for privacy and custom model selection.

## 🛠 Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd hnscratch
    ```

2.  **Set up a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Includes `httpx`, `beautifulsoup4`, `textual`, `ollama`, `python-dotenv`, `pytest`, `pytest-asyncio`)*

4.  **Configure Ollama:**
    Make sure [Ollama](https://ollama.ai/) is installed and running.
    The default model is `qwen3-coder:480b-cloud`. You can change this in the `.env` file.

    To pull the recommended model:
    ```bash
    ollama pull qwen3-coder:480b-cloud
    ```

5.  **Environment Variables:**
    Create a `.env` file (or copy `.env.example`):
    ```env
    OLLAMA_MODEL=qwen3-coder:480b-cloud
    OLLAMA_HOST=http://localhost:11434
    ```

## 📖 Usage

Run the application using the virtual environment's Python:

```bash
./venv/bin/python3 main.py
```

### Controls:
-   **Up/Down Arrows:** Navigate stories.
-   **Enter:** Select a story to analyze.
-   **R:** Refresh the story list.
-   **Q:** Quit the application.
-   **Esc:** Go back to the list from a report.
-   **Chat:** Type in the input box at the bottom of the report screen to ask questions.

## 🧪 Testing

Run the test suite to verify the Hacker News client:

```bash
./venv/bin/pytest tests/
```

## 📁 Project Structure

-   `main.py`: Entry point and configuration loader.
-   `src/hn.py`: Hacker News API client and web scraper with BFS comment traversal.
-   `src/analyze.py`: AI analysis logic using Ollama with structured prompts.
-   `src/tui.py`: Textual User Interface screens and logic.
-   `tests/`: Unit tests for core functionality.
-   `reports/`: Directory where generated reports are saved.

## 📝 License

MIT
