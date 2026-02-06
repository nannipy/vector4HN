# Module Reference

## src.hn (Hacker News Client)

Handles all external interactions with the Hacker News API and target websites.

### `HNClient`
- `fetch_top_stories(page, limit)`: Retreives a slice of top stories.
- `fetch_item(item_id)`: Gets raw JSON data for a story or comment.
- `fetch_comments(item_ids, limit)`: Performs BFS to fetch a flat list of comments with `depth` attributes.
- `fetch_article_text(url)`: Scrapes the given URL.

## src.analyze (AI Logic)

Manages LLM interactions through a provider-agnostic interface.

### `Analyzer`
- `generate_report(story, article_text, comments)`: Produces the initial 1-page summary. Records usage via `src.logger`.
- `chat_with_context(...)`: Handles turn-based chat. Appends history to maintain conversational continuity.
- `set_provider(provider_type, **kwargs)`: Dynamically switches between Ollama and Gemini.

### `LLMProvider` (Abstract)
- `OllamaProvider`: Implementation for local Ollama.
- `GeminiProvider`: Implementation for Google Gemini.

## src.tui (User Interface)

The presentation layer built with Textual.

- **DashboardScreen**: List view with pagination and settings access (`S`).
- **ReportScreen**: Dual-pane display for reading reports and chatting with context.
- **SettingsScreen**: Form-based LLM configuration.
- **Caching Strategy**: Checks `reports/` for existing analysis before invoking the LLM.

## src.logger (Utilities)

Handles application-wide logging and metrics.

- `setup_logging()`: Initializes standard Python logging to `logs/app/app.log`.
- `log_usage(model, input_tokens, output_tokens, duration_s, operation_type)`: Appends usage statistics to `logs/stats/usage_stats.csv`.
