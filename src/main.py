import os
import sys
from dotenv import load_dotenv

# Load environment variables before importing other modules
load_dotenv()

import ollama
from src.tui import HNApp
from src.logger import setup_logging

def check_provider():
    """Checks if the configured LLM provider is ready."""
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    
    if provider == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("❌ Error: GEMINI_API_KEY environment variable is required when using Gemini.")
            return False
        # Optional: We could try to list models with the key to verify it works, 
        # but for now just existence of key is a basic check.
        try:
             # Basic import check
             from google import genai
             return True
        except ImportError:
             print("❌ Error: 'google-genai' package not installed. Run 'pip install google-genai'")
             return False

    elif provider == "ollama":
        model_name = os.getenv("OLLAMA_MODEL", "llama3")
        try:
            client = ollama.Client()
            response = client.list()
            
            available_models = []
            # Handle different response formats from ollama library versions
            if hasattr(response, 'models'):
                available_models = [m.model for m in response.models]
            elif isinstance(response, dict) and 'models' in response:
                available_models = [m.get('model') or m.get('name') for m in response['models']]
            
            if model_name not in available_models:
                print(f"⚠️  Warning: Model '{model_name}' not found in Ollama.")
                print(f"Please run: ollama pull {model_name}")
                return False
            return True
        except Exception as e:
            print(f"❌ Error connecting to Ollama: {e}")
            print("Make sure Ollama is running and accessible.")
            return False
            
    else:
        print(f"❌ Error: Unknown LLM_PROVIDER '{provider}'. Supported: 'ollama', 'gemini'.")
        return False

def main():
    # Detect project root (parent directory of this script's directory)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)

    if len(sys.argv) < 2 or sys.argv[1].lower() != "run":
        print("Usage: vector run")
        print("\nCommands:")
        print("  run    Start the Hacker News Deep Dive Assistant")
        sys.exit(0)

    setup_logging()
    # Check provider configuration
    if not check_provider():
        choice = input("Attempt to start anyway? (y/N): ")
        if choice.lower() != 'y':
            sys.exit(1)

    # Start the Textual App
    app = HNApp()
    app.run()

if __name__ == "__main__":
    main()