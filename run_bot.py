#!/usr/bin/env python
# run_bot.py - Start Telegram Bot
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.interfaces.telegram_bot import main

if __name__ == "__main__":
    main()
