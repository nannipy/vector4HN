from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, DataTable, Button, Label, Markdown, Input, RichLog, LoadingIndicator, Static, TextArea
from textual.screen import Screen
from textual import on, work
from textual.binding import Binding
from rich.markup import escape
from rich.markdown import Markdown as RichMarkdown

import asyncio
import json
import os
import glob
import datetime
import logging
from src.hn import HNClient
from src.analyze import analyzer

class DashboardScreen(Screen):
    BINDINGS = [
        ("q", "quit", "Quit"), 
        ("r", "refresh", "Refresh"),
        ("n", "next_page", "Next Page"),
        ("p", "prev_page", "Prev Page")
    ]

    def __init__(self):
        super().__init__()
        self.page = 1
        self.limit = 50

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Label(f"🔥 Top {self.limit} Hacker News Stories (Page {self.page})", id="title"),
            DataTable(cursor_type="row"),
            id="dashboard-container"
        )
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Rank", "Score", "Title", "Comments", "ID")
        self.load_stories()

    def update_title(self):
        title_label = self.query_one("#title", Label)
        title_label.update(f"🔥 Top {self.limit} Hacker News Stories (Page {self.page})")

    def action_next_page(self):
        self.page += 1
        self.update_title()
        self.load_stories()

    def action_prev_page(self):
        if self.page > 1:
            self.page -= 1
            self.update_title()
            self.load_stories()

    def action_refresh(self):
        self.load_stories()

    def action_quit(self):
        self.app.exit()

    @work
    async def load_stories(self) -> None:
        table = self.query_one(DataTable)
        table.loading = True
        client = HNClient()
        stories = await client.fetch_top_stories(page=self.page, limit=self.limit)
        await client.close()
        
        table.clear()
        start_rank = (self.page - 1) * self.limit + 1
        for idx, story in enumerate(stories, start_rank):
            table.add_row(
                str(idx),
                str(story.get("score", 0)),
                story.get("title", "No Title"),
                str(story.get("descendants", 0)),
                str(story.get("id")),
                key=str(story.get("id"))
            )
        table.loading = False
        table.focus()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        story_id = event.row_key.value
        self.app.push_screen(ProcessingScreen(story_id))

class ProcessingScreen(Screen):
    def __init__(self, story_id: str):
        super().__init__()
        self.story_id = int(story_id)

    def compose(self) -> ComposeResult:
        yield Container(
            Vertical(
                Label("Fetcher & Analyzer Running...", id="status-label"),
                LoadingIndicator(),
                Label("", id="detail-label"),
                classes="center-content"
            )
        )

    def on_mount(self) -> None:
        self.process_story()

    @work
    async def process_story(self) -> None:
        await self._process_story_implementation()

    async def _process_story_implementation(self) -> None:
        status = self.query_one("#status-label", Label)
        detail = self.query_one("#detail-label", Label)
        logging.info(f"Processing story ID: {self.story_id}")
        
        # Check for existing report and context
        report_pattern = f"reports/hn_{self.story_id}_*.md"
        existing_reports = glob.glob(report_pattern)
        
        context_filename = f"reports/hn_{self.story_id}_context.json"
        
        story = {}
        article_text = ""
        comments = []
        report = ""
        filename = ""
        
        client = HNClient()

        if existing_reports and os.path.exists(context_filename):
            # Cache Hit: Load everything from disk
            status.update("Loading Cached Report...")
            filename = existing_reports[0] # Take the first matching report
            
            with open(filename, "r") as f:
                report = f.read()
                
            with open(context_filename, "r") as f:
                context = json.load(f)
                story = context.get("story", {})
                article_text = context.get("article_text", "")
                comments = context.get("comments", [])
                chat_history = context.get("chat_history", [])
                
            await client.close()
            
        else:
            # Cache Miss (or partial): Fetch and Analyze
            
            # 1. Fetch Story Details (if not loaded)
            if not story:
                status.update("Fetching Story Details...")
                story = await client.fetch_item(self.story_id)
            
            # 2. Fetch Article Text
            status.update("Fetching Article Content...")
            url = story.get("url", "")
            detail.update(f"Downloading {url}...")
            article_text = await client.fetch_article_text(url)
            
            # 3. Fetch Comments
            status.update("Fetching Top 100 Comments...")
            detail.update("Traversing comment tree...")
            comments = await client.fetch_comments(story.get("kids", []), limit=100)
            
            await client.close()
            
            # 4. Analyze (only if we don't have a report yet)
            if not existing_reports:
                status.update("🤖 Ollama is Analyzing...")
                detail.update("Generating summary report...")
                report = await analyzer.generate_report(story, article_text, comments)
                
                # Save to file
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"reports/hn_{self.story_id}_{timestamp}.md"
                with open(filename, "w") as f:
                    f.write(report)
            else:
                 # We have report but no context json? (Legacy case handling or deleted json)
                 # We fetched data, so let's load the existing report
                 filename = existing_reports[0]
                 with open(filename, "r") as f:
                    report = f.read()

            # Save Context JSON (always ensure it exists if we fetched data)
            with open(context_filename, "w") as f:
                json.dump({
                    "story": story,
                    "article_text": article_text,
                    "comments": comments,
                    "chat_history": []
                }, f, indent=2)
            
        # Transition
        self.app.pop_screen()
        self.app.push_screen(ReportScreen(story, article_text, comments, report, filename, context_filename, chat_history if 'chat_history' in locals() else []))

class ArticleScreen(Screen):
    BINDINGS = [
        ("escape", "back", "Back"),
    ]

    def __init__(self, content: str, title: str = "Article View"):
        super().__init__()
        self.content = content
        self.title_text = title

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Label(self.title_text, classes="header-label"),
            Markdown(self.content, id="article-view"),
            id="article-container"
        )
        yield Footer()

    def action_back(self):
        self.app.pop_screen()

class ReportScreen(Screen):
    BINDINGS = [
        ("escape", "back", "Back to List"),
        ("ctrl+c", "copy_last", "Copy Last Answer"),
        ("ctrl+a", "copy_all", "Copy All Chat"),
        ("ctrl+s", "toggle_select", "Toggle Select Mode"),
        ("o", "view_article", "View Original"),
    ]

    def __init__(self, story, article_text, comments, report_md, filename, context_filename, chat_history):
        super().__init__()
        self.story = story
        self.article_text = article_text
        self.comments = comments
        self.report_md = report_md
        self.filename = filename
        self.context_filename = context_filename
        self.chat_history = chat_history
        self.select_mode = False

    def action_view_article(self) -> None:
        title = self.story.get("title", "Article")
        self.app.push_screen(ArticleScreen(self.article_text, title))

    async def action_copy_last(self) -> None:
        # Check if we are in select mode and have a selection
        if self.select_mode:
            text_area = self.query_one("#chat-text-area", TextArea)
            if text_area.selection:
                # Textual TextArea handles ctrl+c natively for copy, 
                # but if we bound it to this action, we intercepted it.
                # We should manually copy the selection.
                selected_text = text_area.selected_text
                self.app.copy_to_clipboard(selected_text)
                self.notify("Selection copied!")
                return
        
        # Default behavior: Copy last assistant message
        for msg in reversed(self.chat_history):
            if msg.get('role') == 'assistant':
                content = msg.get('content', '')
                self.app.copy_to_clipboard(content)
                self.notify("Last response copied to clipboard!")
                return
        self.notify("No assistant response to copy.", severity="warning")

    def action_copy_all(self) -> None:
        full_log = ""
        for msg in self.chat_history:
            role = "You" if msg.get('role') == 'user' else "Ollama"
            content = msg.get('content', '')
            full_log += f"{role}: {content}\n\n"
        
        if full_log:
            self.app.copy_to_clipboard(full_log)
            self.notify("Full chat history copied to clipboard!")
        else:
             self.notify("Chat history is empty.", severity="warning")

    def action_toggle_select(self) -> None:
        self.select_mode = not self.select_mode
        rich_log = self.query_one("#chat-log", RichLog)
        text_area = self.query_one("#chat-text-area", TextArea)
        
        if self.select_mode:
            # Populate TextArea and show it
            full_log = ""
            for msg in self.chat_history:
                role = "You" if msg.get('role') == 'user' else "Ollama"
                content = msg.get('content', '')
                full_log += f"{role}:\n{content}\n\n"
            
            text_area.text = full_log
            rich_log.display = False
            text_area.display = True
            text_area.focus()
            self.notify("Select Mode: ON (Text is copyable)")
        else:
            # Show RichLog
            text_area.display = False
            rich_log.display = True
            self.query_one("#chat-input").focus()
            self.notify("Select Mode: OFF")

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Vertical(
                Label(f"📄 Report: {self.filename}", classes="header-label"),
                Markdown(self.report_md, id="markdown-view"),
                id="report-pane"
            ),
            Vertical(
                Label("💬 Deep Dive Chat", classes="header-label"),
                RichLog(id="chat-log", markup=True, wrap=True),
                TextArea(id="chat-text-area", read_only=True),
                Input(placeholder="Ask about specific arguments...", id="chat-input"),
                id="chat-pane"
            ),
            classes="split-view"
        )
        yield Footer()

    def on_mount(self) -> None:
        if self.chat_history:
            log = self.query_one(RichLog)
            for msg in self.chat_history:
                role = msg.get('role')
                content = msg.get('content')
                if role == 'user':
                    log.write(f"[bold green]You:[/bold green] {content}")
                elif role == 'assistant':
                    log.write(f"[bold blue]Ollama:[/bold blue]")
                    log.write(RichMarkdown(content))
                    log.write("-" * 20)

    @on(Input.Submitted)
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        question = event.value
        if not question.strip():
            return
            
        log = self.query_one(RichLog)
        input_widget = self.query_one(Input)
        
        log.write(f"[bold green]You:[/bold green] {question}")
        input_widget.value = ""
        input_widget.disabled = True
        
        self.run_chat_query(question)

    @work
    async def run_chat_query(self, question: str) -> None:
        await self._run_chat_query_implementation(question)

    async def _run_chat_query_implementation(self, question: str) -> None:
        log = self.query_one(RichLog)
        
        # Add a placeholder for the response
        log.write("[italic gray]Ollama is thinking...[/italic gray]")
        
        try:
            answer = await analyzer.chat_with_context(
                self.story, 
                self.article_text, 
                self.comments, 
                question, 
                self.chat_history
            )
            
            # Remove the "thinking" message by clearing if possible, 
            # but RichLog doesn't easily allow removing last line. 
            # We'll just append the answer.
            
            self.chat_history.append({'role': 'user', 'content': question})
            self.chat_history.append({'role': 'assistant', 'content': answer})
            
            log.write(f"[bold blue]Ollama:[/bold blue]")
            log.write(RichMarkdown(answer))
            log.write("-" * 20)
            
            # If in select mode, update it (though it might be jarring, so maybe wait for toggle)
            if self.select_mode:
                text_area = self.query_one("#chat-text-area", TextArea)
                text_area.text += f"\nYou:\n{question}\n\nOllama:\n{answer}\n\n"
            
            # Append to Report File
            try:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open(self.filename, "a") as f:
                    f.write(f"\n\n## Chat Log ({timestamp})\n")
                    f.write(f"**User**: {question}\n\n")
                    f.write(f"**Ollama**: {answer}\n")
            except Exception as e:
                log.write(f"[bold red]Error saving chat to report:[/bold red] {escape(str(e))}")

            # Save to Context JSON
            try:
                if os.path.exists(self.context_filename):
                    with open(self.context_filename, "r") as f:
                        data = json.load(f)
                    
                    data["chat_history"] = self.chat_history
                    
                    with open(self.context_filename, "w") as f:
                        json.dump(data, f, indent=2)
            except Exception as e:
                 log.write(f"[bold red]Error saving chat context:[/bold red] {escape(str(e))}")

        except Exception as e:
            log.write(f"[bold red]Error:[/bold red] {escape(str(e))}")
        finally:
            self.query_one(Input).disabled = False
            self.query_one(Input).focus()

    def action_back(self) -> None:
        self.app.pop_screen()

class HNApp(App):
    TITLE = "Vector"
    CSS = """
    #dashboard-container {
        height: 100%;
        align: center middle;
    }
    
    #title {
        text-align: center;
        margin: 1;
        text-style: bold;
    }
    
    .center-content {
        align: center middle;
        height: 100%;
    }
    
    #status-label, #detail-label {
        text-align: center;
        /* width: 100%;   Removed to prevent padding overflow */
    }
    
    .split-view {
        layout: horizontal;
        height: 100%;
    }
    
    #report-pane {
        width: 50%;
        height: 100%;
        border-right: solid green;
        overflow-y: auto;
        overflow-x: auto; /* Allow scroll only if needed */
    }
    
    #chat-pane {
        width: 50%;
        height: 100%;
        padding: 1;
    }
    
    #chat-log {
        height: 1fr;
        border: solid white;
        background: $surface;
    }

    #chat-text-area {
        height: 1fr;
        border: solid white;
        background: $surface;
        display: none;
    }
    
    #markdown-view {
        padding: 1;
    }
    
    .header-label {
        background: $accent;
        color: $text;
        padding: 1;
        text-align: center;
        /* width: 100%; Removed to prevent padding overflow */
    }

    #article-container {
        height: 100%;
        overflow-y: auto;
    }

    #article-view {
        padding: 1;
    }
    """

    def on_mount(self) -> None:
        self.push_screen(DashboardScreen())

if __name__ == "__main__":
    app = HNApp()
    app.run()





