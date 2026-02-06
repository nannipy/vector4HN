import logging
import os
import csv
from datetime import datetime

# Define log directories
LOG_DIR = "logs"
APP_LOG_DIR = os.path.join(LOG_DIR, "app")
STATS_LOG_DIR = os.path.join(LOG_DIR, "stats")
STATS_FILE = os.path.join(STATS_LOG_DIR, "usage_stats.csv")

def setup_logging():
    """Configures the logging system."""
    
    # Create directories if they don't exist
    for directory in [APP_LOG_DIR, STATS_LOG_DIR]:
        if not os.path.exists(directory):
            os.makedirs(directory)
            
    # Configure root logger to write to file
    log_file = os.path.join(APP_LOG_DIR, "app.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            # We explicitly do NOT add StreamHandler here to avoid messing up the TUI
        ]
    )
    
    # Initialize stats file with header if it doesn't exist
    if not os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Model", "Input Tokens", "Output Tokens", "Duration (s)", "Type"])

    logging.info("Logging initialized.")

def log_usage(model: str, input_tokens: int, output_tokens: int, duration_s: float, operation_type: str = "generation"):
    """Logs token usage stats to CSV."""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(STATS_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, model, input_tokens, output_tokens, f"{duration_s:.2f}", operation_type])
    except Exception as e:
        logging.error(f"Failed to log usage stats: {e}")
