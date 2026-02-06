# Setup and Configuration

## Prerequisites
- **Python 3.12+** (Recommended)
- **Ollama**: For local LLM support. [Download Ollama](https://ollama.ai/).
- **Google Gemini API Key**: For cloud LLM support. [Get Key](https://aistudio.google.com/).

## Configuration (`.env`)

Create a `.env` file in the root directory to customize behavior.

| Variable | Default | Description |
| :--- | :--- | :--- |
| `LLM_PROVIDER` | `ollama` | Choose `ollama` or `gemini`. |
| `OLLAMA_HOST` | `http://localhost:11434` | URL of your local Ollama instance. |
| `OLLAMA_MODEL` | `llama3` | The LLM model to use with Ollama. |
| `GEMINI_API_KEY` | - | Required if provider is `gemini`. |
| `GEMINI_MODEL` | `gemini-3-flash-preview` | The Gemini model to use. |

## Runtime Settings
You can modify the `LLM_PROVIDER`, `MODEL`, and `API_KEY` while the application is running by pressing `S` on the Dashboard. Note that these changes are persistent during the session but will not overwrite your `.env` file.

## Logs and Statistics
Vector stores data in the `logs/` directory:
- `logs/app/app.log`: General application logs for troubleshooting.
- `logs/stats/usage_stats.csv`: CSV file tracking:
    - Timestamp
    - Model Name
    - Input Tokens
    - Output Tokens
    - Duration (seconds)
    - Operation Type (e.g., `report_generation`, `chat_query`)

## Running Tests
Vector includes a test suite using `pytest`. Ensure dependencies are installed with `pip install -r requirements.txt`.

```bash
# Run all tests
pytest tests/
```

Individual tests:
- `tests/test_hn.py`: HN Client and Scraping.
- `tests/test_caching_logic.py`: Caching and Persistence.
- `tests/test_logging.py`: Logging and Stats Tracking.
