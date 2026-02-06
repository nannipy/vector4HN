import asyncio
import os
import shutil
import json
import glob
from unittest.mock import MagicMock, AsyncMock, patch, PropertyMock
import sys

# Add src to path
import pytest

# Add src to path
sys.path.append(os.getcwd())

from src.tui import ProcessingScreen, ReportScreen
HNBOT_TEST_MODE = True

# Mock the textual specific imports because we can't run App in this script easily
# We will just verify logic by instantiating the class and mocking the query_one method
# and the app attribute.

@pytest.mark.asyncio
async def test_caching_logic():
    print("🧪 Starting Caching Logic Test...")
    
    test_story_id = 999999
    
    # reliable clean up
    reports = glob.glob(f"reports/hn_{test_story_id}*")
    for r in reports:
        os.remove(r)
        
    # Mock Data
    mock_story = {"id": test_story_id, "title": "Test Story", "url": "http://example.com"}
    mock_article = "This is a test article content."
    mock_comments = [{"by": "tester", "text": "Great test!"}]
    mock_report = "# Test Report\n\nSummary..."
    
    # 1. Test Cache Miss (First Run)
    print("\n--- Test 1: Cache Miss (First Run) ---")
    
    screen = ProcessingScreen(str(test_story_id))
    screen.query_one = MagicMock() # Mock UI updates
    
    # Mocking external dependencies
    with patch("src.tui.HNClient") as MockHN, \
         patch("src.tui.analyzer", new_callable=AsyncMock) as mock_analyzer, \
         patch("src.tui.ProcessingScreen.app", new_callable=PropertyMock) as mock_app_prop:
        
        # Setup App Mock (The property returns this mock)
        mock_app = MagicMock()
        mock_app_prop.return_value = mock_app

        # Setup Mocks
        client_instance = AsyncMock()
        MockHN.return_value = client_instance
        client_instance.fetch_item.return_value = mock_story
        client_instance.fetch_article_text.return_value = mock_article
        client_instance.fetch_comments.return_value = mock_comments
        
        mock_analyzer.generate_report.return_value = mock_report
        
        # Run the method
        await screen._process_story_implementation()
        
        # Verify Mocks called
        assert client_instance.fetch_item.called, "Should have fetched item"
        assert mock_analyzer.generate_report.called, "Should have generated report"
        
        # Verify Files Created
        report_files = glob.glob(f"reports/hn_{test_story_id}_*.md")
        json_file = f"reports/hn_{test_story_id}_context.json"
        
        assert len(report_files) >= 1, "Report MD file should be created"
        assert os.path.exists(json_file), "Context JSON file should be created"
        
        print("✅ First run success: Files created.")
        
    # 2. Test Cache Hit (Second Run)
    print("\n--- Test 2: Cache Hit (Second Run) ---")
    
    screen_hit = ProcessingScreen(str(test_story_id))
    screen_hit.query_one = MagicMock()
    
    with patch("src.tui.HNClient") as MockHN, \
         patch("src.tui.analyzer", new_callable=AsyncMock) as mock_analyzer, \
         patch("src.tui.ProcessingScreen.app", new_callable=PropertyMock) as mock_app_prop:
         
        mock_app = MagicMock()
        mock_app_prop.return_value = mock_app

        client_instance = AsyncMock()
        MockHN.return_value = client_instance
        
        # Run the method
        await screen_hit._process_story_implementation()
        
        # Verify Mocks NOT called (or called minimally)
        # Check that we loaded from file instead of fetching
        # Depending on logic, client might be instantiated but fetch methods skipped?
        # Logic: checks file -> if exists -> load -> mocks shouldn't be called for fetching
        
        # Note: We create client = HNClient() early in the function, so constructor is called.
        # But fetch_item should NOT be called if cache hit.
        assert not client_instance.fetch_item.called, "Should NOT have fetched item on cache hit"
        assert not mock_analyzer.generate_report.called, "Should NOT have generated report on cache hit"
        
        print("✅ Second run success: Loaded from cache.")

    # 3. Test Chat Persistence
    print("\n--- Test 3: Chat Persistence ---")
    
    # Create a dummy report file to append to
    report_filename = f"reports/hn_{test_story_id}_unittest.md"
    context_filename = f"reports/hn_{test_story_id}_context.json"
    
    with open(report_filename, "w") as f:
        f.write("# Original Report")
    
    # Initialize context file
    with open(context_filename, "w") as f:
        json.dump({"story": {}, "article_text": "", "comments": [], "chat_history": []}, f)
        
    report_screen = ReportScreen(mock_story, mock_article, mock_comments, mock_report, report_filename, context_filename, [])
    report_screen.query_one = MagicMock()
    
    with patch("src.tui.analyzer", new_callable=AsyncMock) as mock_analyzer:
        mock_analyzer.chat_with_context.return_value = "This is the answer."
        
        await report_screen._run_chat_query_implementation("What is this?")
        
        # Verify call
        assert mock_analyzer.chat_with_context.called
        
        # Verify File Append (MD)
        with open(report_filename, "r") as f:
            content = f.read()
        assert "## Chat Log" in content
        
        # Verify JSON Persistence
        with open(context_filename, "r") as f:
            context = json.load(f)
            
        history = context.get("chat_history", [])
        assert len(history) == 2, "Should have 2 messages (user + assistant)"
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "What is this?"
        assert history[1]["role"] == "assistant"
        assert history[1]["content"] == "This is the answer."
        
        print("✅ Chat Persistence (MD + JSON) success.")

    # Cleanup
    for r in glob.glob(f"reports/hn_{test_story_id}*"):
        os.remove(r)
    print("\n✅ Verification Complete.")

if __name__ == "__main__":
    if not os.path.exists("reports"):
        os.makedirs("reports")
    asyncio.run(test_caching_logic())
