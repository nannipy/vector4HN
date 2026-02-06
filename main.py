import os
import sys
from dotenv import load_dotenv

# Load environment variables before importing other modules
load_dotenv()

import ollama
from src.tui import HNApp
from src.logger import setup_logging

def check_model(model_name):
    """Checks if the specified model is available in Ollama."""
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

def main():
    setup_logging()
    model = os.getenv("OLLAMA_MODEL", "llama3")
    
    # Ensure reports directory exists
    if not os.path.exists("reports"):
        os.makedirs("reports")
    
    # Check if model exists
    if not check_model(model):
        choice = input("Attempt to start anyway? (y/N): ")
        if choice.lower() != 'y':
            sys.exit(1)

    # Start the Textual App
    app = HNApp()
    app.run()

if __name__ == "__main__":
    main()