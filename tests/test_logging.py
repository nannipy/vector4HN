import os
import csv
import logging
import sys
sys.path.append(os.getcwd())
from src.logger import setup_logging, log_usage, APP_LOG_DIR, STATS_FILE

def test_logging_system():
    print("🧪 Testing Logging System...")
    
    # 1. Setup
    setup_logging()
    
    # 2. Verify Directories
    assert os.path.exists(APP_LOG_DIR), "App log directory should exist"
    assert os.path.exists(os.path.dirname(STATS_FILE)), "Stats log directory should exist"
    assert os.path.exists(os.path.join(APP_LOG_DIR, "app.log")), "App log file should exist"
    assert os.path.exists(STATS_FILE), "Stats file should exist"
    
    print("✅ Directories and files created.")
    
    # 3. Test App Logging
    test_message = "Test log message"
    logging.info(test_message)
    
    with open(os.path.join(APP_LOG_DIR, "app.log"), "r") as f:
        content = f.read()
        assert test_message in content, "App log should contain test message"
        
    print("✅ App logging works.")
    
    # 4. Test Usage Logging
    log_usage(
        model="test-model",
        input_tokens=10,
        output_tokens=20,
        duration_s=1.5,
        operation_type="test"
    )
    
    with open(STATS_FILE, "r") as f:
        reader = csv.reader(f)
        rows = list(reader)
        # Header + at least one row
        assert len(rows) >= 2, "Stats file should have header and data"
        last_row = rows[-1]
        assert last_row[1] == "test-model"
        assert last_row[2] == "10"
        assert last_row[3] == "20"
        assert last_row[5] == "test"
        
    print("✅ Stats logging works.")
    print("✅ Verification Complete.")

if __name__ == "__main__":
    test_logging_system()
