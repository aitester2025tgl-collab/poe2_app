# CODE_QUALITY_IMPROVEMENTS.md

## Code Quality & Best Practices Recommendations

### 1. **Type Hints Consistency**

#### Current State:
Some files have type hints, others don't

#### Recommendation:
Add comprehensive type hints everywhere

```python
# Before
def get_builds(cls):
    return load_builds().get(cls, [])

# After
from typing import List, Dict, Any

def get_builds(cls: str) -> List[Dict[str, Any]]:
    """
    Get builds for a specific class.
    
    Args:
        cls: The class name to fetch builds for
        
    Returns:
        List of build dictionaries
    """
    return load_builds().get(cls, [])
```

**Tools**: Use `mypy` for static type checking
```bash
pip install mypy
mypy poe2_app/
```

---

### 2. **Logging Standardization**

#### Current Issues:
- Mixed logging levels
- Inconsistent message formats
- Portuguese/English mixed

#### Recommended Standard:

```python
# utils/logging_config.py
import logging
import sys
from pathlib import Path

def setup_logging(
    name: str,
    level: str = "INFO",
    log_file: Path = None
) -> logging.Logger:
    """
    Configure standardized logging.
    
    Format: [TIMESTAMP] [LEVEL] [MODULE] Message
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        logger.addHandler(file_handler)
    
    # Formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    return logger

# Usage in all modules:
logger = setup_logging(__name__, log_file=Path("logs/app.log"))
```

---

### 3. **Environment Variable Validation**

#### Current Issue:
Variables checked at runtime, causing late failures

#### Solution:

```python
# config.py
from typing import Optional
import os

class ConfigError(Exception):
    pass

class Config:
    """Validated configuration management"""
    
    @staticmethod
    def get_required(key: str) -> str:
        """Get required environment variable or raise error"""
        value = os.getenv(key)
        if not value:
            raise ConfigError(
                f"Required environment variable '{key}' not set. "
                f"Please check your .env file."
            )
        return value
    
    @staticmethod
    def get_optional(key: str, default: str = None) -> Optional[str]:
        """Get optional environment variable with default"""
        return os.getenv(key, default)
    
    @staticmethod
    def get_int(key: str, default: int = None) -> int:
        """Get integer environment variable"""
        value = os.getenv(key, str(default))
        try:
            return int(value)
        except ValueError:
            raise ConfigError(f"'{key}' must be an integer, got '{value}'")

# Validate on startup
def validate_config():
    """Validate all required configuration on app startup"""
    required_vars = {
        'TELEGRAM_BOT_TOKEN': Config.get_required,
        'OLLAMA_MODEL': lambda: Config.get_optional('OLLAMA_MODEL', 'mistral')
    }
    
    errors = []
    for var, getter in required_vars.items():
        try:
            getter()
        except ConfigError as e:
            errors.append(str(e))
    
    if errors:
        raise ConfigError("\n".join(errors))
```

---

### 4. **Input Validation & Sanitization**

#### Current Issue:
LLM outputs not properly validated

#### Solution:

```python
# validators.py
from pydantic import BaseModel, validator, ValidationError
from typing import List

class SkillAction(BaseModel):
    type: str
    name: str
    level: int
    passives: List[str]
    
    @validator('type')
    def validate_type(cls, v):
        if v not in ['Skill', 'Passive', 'Item']:
            raise ValueError(f'Invalid type: {v}')
        return v
    
    @validator('level')
    def validate_level(cls, v):
        if not 1 <= v <= 100:
            raise ValueError(f'Level must be 1-100, got {v}')
        return v
    
    @validator('name')
    def validate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Skill name too short')
        return v.strip()

# Usage:
try:
    skill = SkillAction(**llm_output)
except ValidationError as e:
    logger.error(f"LLM output validation failed: {e}")
```

---

### 5. **Code Documentation**

#### Add Docstrings Everywhere:

```python
def calculate_recommendation_score(build: Dict[str, Any]) -> Tuple[float, float, float]:
    """
    Calculate confidence and recommendation scores for a build.
    
    The recommendation score combines:
    - Data quality (confidence): 70%
    - Community popularity (reputation): 30%
    
    Args:
        build: Build dictionary with keys:
            - reputation (int): Raw popularity score
            - skill_tree_leveling (list): Build progression data
    
    Returns:
        Tuple of (confidence, reputation_normalized, recommendation_score)
        - confidence: 0.0-1.0, percentage of known skills/passives
        - reputation_normalized: 0.0-1.0, reputation scaled to max
        - recommendation_score: 0.0-100.0, weighted final score
    
    Example:
        >>> build = {"reputation": 75000, "skill_tree_leveling": [...]}
        >>> conf, rep, score = calculate_recommendation_score(build)
        >>> print(f"Score: {score:.2f}/100")
        Score: 67.50/100
    
    Raises:
        KeyError: If build missing required fields
    """
```

---

### 6. **Error Messages Improvement**

#### Current:
```python
logger.error("❌ Erro ao carregar builds")
```

#### Better:
```python
logger.error(
    "Failed to load builds from %s: %s",
    file_path,
    str(e),
    exc_info=True  # Include stack trace
)
```

#### Best:
```python
class BuildLoader:
    def load(self, file_path: Path) -> Dict:
        """Load builds with comprehensive error reporting"""
        try:
            return self._load_json(file_path)
        except FileNotFoundError:
            logger.error(
                "Build file not found: %s\n"
                "Expected location: %s\n"
                "Please run: python update_builds_online.py",
                file_path,
                file_path.absolute()
            )
            raise
        except json.JSONDecodeError as e:
            logger.error(
                "Invalid JSON in build file: %s\n"
                "Error at line %d, column %d: %s\n"
                "Suggestion: Restore from backup or regenerate",
                file_path,
                e.lineno,
                e.colno,
                e.msg
            )
            raise
```

---

### 7. **Constants Management**

#### Current Issue:
Magic numbers and strings scattered throughout

#### Solution:

```python
# constants.py
from enum import Enum

class BuildType(Enum):
    SKILL = "Skill"
    PASSIVE = "Passive"
    ITEM = "Item"

class LevelRange(Enum):
    EARLY = "1-10"
    MID = "11-30"
    LATE = "31-50"
    ENDGAME = "51+"

# Validation thresholds
class ValidationThresholds:
    MIN_CONFIDENCE = 0.40
    MIN_SKILLS = 3
    MIN_LEVEL = 1
    MAX_LEVEL = 100
    
# Scoring weights
class ScoringWeights:
    CONFIDENCE = 0.7
    REPUTATION = 0.3
    MAX_REPUTATION = 100_000

# Usage:
if confidence < ValidationThresholds.MIN_CONFIDENCE:
    logger.warning("Build below confidence threshold")
```

---

### 8. **Dependency Injection**

#### Current Issue:
Hard-coded dependencies

#### Better Approach:

```python
# Before
def fetch_build():
    client = Client()  # Hard-coded
    return client.fetch()

# After
class BuildFetcher:
    def __init__(self, http_client, llm_client, cache):
        self.http = http_client
        self.llm = llm_client
        self.cache = cache
    
    def fetch(self, url: str) -> Dict:
        """Fetch with injected dependencies"""
        if cached := self.cache.get(url):
            return cached
        
        html = self.http.get(url)
        data = self.llm.extract(html)
        self.cache.set(url, data)
        return data

# Usage
fetcher = BuildFetcher(
    http_client=HttpClient(),
    llm_client=OllamaClient(),
    cache=RedisCache()
)
```

**Benefits**:
- Easy to test (mock dependencies)
- Flexible configuration
- Clear dependencies

---

### 9. **Test Coverage**

#### Add Comprehensive Tests:

```python
# tests/test_validation.py
import pytest
from poe2_parser import is_build_valid

class TestBuildValidation:
    
    @pytest.fixture
    def valid_build(self):
        return {
            "build_name": "Test",
            "class": "Warrior",
            "skill_tree_leveling": [...]
        }
    
    def test_valid_build_passes(self, valid_build):
        assert is_build_valid(valid_build) is True
    
    def test_insufficient_skills_fails(self):
        build = {"skill_tree_leveling": []}
        assert is_build_valid(build) is False
    
    @pytest.mark.parametrize("confidence,expected", [
        (0.5, True),
        (0.3, False),
        (1.0, True),
    ])
    def test_confidence_thresholds(self, confidence, expected):
        # Mock confidence calculation
        pass
```

**Run tests:**
```bash
pip install pytest pytest-cov
pytest tests/ --cov=poe2_app --cov-report=html
```

---

### 10. **Code Formatting**

#### Use Automated Formatters:

```bash
# Install tools
pip install black isort flake8

# Format code
black poe2_app/
isort poe2_app/

# Check style
flake8 poe2_app/
```

#### Pre-commit Hook:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.0
    hooks:
      - id: black
  
  - repo: https://github.com/PyCQA/isort
    rev: 5.13.2
    hooks:
      - id: isort
  
  - repo: https://github.com/PyCQA/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
```

---

## Implementation Checklist

- [ ] Add type hints to all functions
- [ ] Standardize logging across modules
- [ ] Validate environment variables on startup
- [ ] Add comprehensive docstrings
- [ ] Create unit tests (>70% coverage)
- [ ] Set up pre-commit hooks
- [ ] Add input validation with Pydantic
- [ ] Improve error messages with context
- [ ] Extract magic numbers to constants
- [ ] Implement dependency injection
- [ ] Add code formatting (Black)
- [ ] Set up CI/CD pipeline
- [ ] Create developer documentation
- [ ] Add performance profiling

---

## Tools to Install

```bash
# Development tools
pip install black isort flake8 mypy pytest pytest-cov pre-commit

# Type checking
pip install types-requests types-Flask

# Linting
pip install pylint bandit  # Security linter
```
