# config.py - Centralized Configuration Management
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Project Root
PROJECT_ROOT = Path(__file__).parent

# ===== API CREDENTIALS =====
GOOGLE_SEARCH_API_KEY = os.getenv('GOOGLE_SEARCH_API_KEY')
GOOGLE_SEARCH_ENGINE_ID = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# ===== LLM CONFIGURATION =====
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'mistral')
OLLAMA_TEMPERATURE = float(os.getenv('OLLAMA_TEMPERATURE', '0.1'))
OLLAMA_TIMEOUT = float(os.getenv('OLLAMA_TIMEOUT', '120.0'))

# ===== FILE PATHS =====
DATA_DIR = PROJECT_ROOT / 'data'
DATA_DIR.mkdir(exist_ok=True)

BUILD_FILE = str(DATA_DIR / 'poe2_builds.json')
GROUND_TRUTH_FILE = str(DATA_DIR / 'poe2_ref_data.json')
LEARNING_STATS_FILE = str(DATA_DIR / 'learning_stats.json')
LAST_FETCH_FILE = str(DATA_DIR / 'last_fetch.txt')

# For backward compatibility with old code still using strings
REFERENCE_FILE = GROUND_TRUTH_FILE
JSON_FILE = BUILD_FILE

# ===== GAME DATA =====
POE2_CLASSES = [
    "Warrior", "Monk", "Mercenary", "Sorceress", "Witch", 
    "Ranger", "Huntress", "Druid", "Duelist", "Marauder", 
    "Shadow", "Templar"
]

# Classes to skip during data collection
CLASSES_TO_SKIP = ["Druid", "Duelist", "Marauder", "Shadow", "Templar"]

# ===== LEVEL BUCKETS (Acts) =====
# When displaying builds in the web UI, we can group numeric ranges into Acts.
# This mapping is configurable: keys are act labels, values are (min_level, max_level)
USE_ACT_BUCKETS = True
ACT_LEVEL_BUCKETS = {
    "Act 1": (1, 10),
    "Act 2": (11, 20),
    "Act 3": (21, 30),
    "Act 4": (31, 40),
    "Act 5": (41, 50),
    "Act 6": (51, 60),
}

# ===== VALIDATION THRESHOLDS =====
MIN_CONFIDENCE_THRESHOLD = 0.40  # 40%
MIN_SKILLS_REQUIRED = 3
MAX_BUILDS_PER_CLASS = 10
LLM_PROCESSING_LIMIT = 3
MAX_RETRIES = 3

# ===== SCORING WEIGHTS =====
WEIGHT_CONFIDENCE = 0.7  # 70% data quality
WEIGHT_REPUTATION = 0.3  # 30% popularity
MAX_REPUTATION_VALUE = 100000

# ===== SCRAPING CONFIGURATION =====
SKILL_GEMS_URL = "https://poe2db.tw/us/Skill_Gems"
SUPPORT_GEMS_URL = "https://poe2db.tw/us/Support_Gems"

REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}
REQUEST_TIMEOUT = 30

# ===== LOGGING =====
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
