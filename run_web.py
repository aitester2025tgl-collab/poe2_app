#!/usr/bin/env python
# run_web.py - Start Flask Web App
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.interfaces.web_app import app

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
