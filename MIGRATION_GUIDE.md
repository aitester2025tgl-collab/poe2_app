# MIGRATION_GUIDE.md

## 🏗️ Project Structure Migration Guide

This guide walks you through reorganizing your project step-by-step.

---

## 📋 Current Structure (Before)

```
poe2_app/
├── poe2_schema.py
├── poe2_parser.py
├── poe2_assistente.py
├── poe2_fetcher.py
├── poe2_data_ref.py
├── poe2_ground_truth_manager.py
├── learning_system.py
├── llm_extractor_v2.py
├── batch_extractor.py
├── bot_paginated.py
├── poe2_web_editor.py
├── poe2_app_builder.py
├── update_builds_online.py
├── poe2_builds.json
├── poe2_ref_data.json
├── learning_stats.json
├── requirements.txt
├── old/ (unused files)
└── templates/
```

**Problems:**
- ❌ 15+ files in root directory
- ❌ Hard to navigate
- ❌ Unclear module relationships
- ❌ Data files mixed with code
- ❌ Inconsistent naming (poe2_ prefix everywhere)

---

## 🎯 New Structure (After)

```
poe2_app/
├── src/                          # All source code
│   ├── core/                     # Core business logic
│   │   ├── schema.py            # (was poe2_schema.py)
│   │   ├── parser.py            # (was poe2_parser.py)
│   │   ├── assistant.py         # (was poe2_assistente.py)
│   │   └── validator.py         # (was poe2_data_ref.py)
│   ├── data/                     # Data management
│   │   ├── fetcher.py           # (was poe2_fetcher.py)
│   │   ├── ground_truth.py      # (was poe2_ground_truth_manager.py)
│   │   └── learning.py          # (was learning_system.py)
│   ├── extractors/               # LLM extraction
│   │   ├── llm_extractor.py     # (was llm_extractor_v2.py)
│   │   └── batch_processor.py   # (was batch_extractor.py)
│   ├── interfaces/               # User interfaces
│   │   ├── telegram_bot.py      # (was bot_paginated.py)
│   │   ├── web_app.py           # (was poe2_web_editor.py)
│   │   └── desktop_gui.py       # (was poe2_app_builder.py)
│   └── utils/                    # Utilities
│       ├── backup.py
│       └── logging_config.py
├── data/                         # Data files (separated)
│   ├── poe2_builds.json
│   ├── poe2_ref_data.json
│   ├── learning_stats.json
│   └── last_fetch.txt
├── logs/                         # Log files
├── backups/                      # Automatic backups
├── templates/                    # Flask templates
├── tests/                        # Unit tests
├── config.py                     # Configuration
├── run_bot.py                    # Entry point: Telegram bot
├── run_web.py                    # Entry point: Web app
├── update_builds.py              # Entry point: Data update
├── run_learning.py               # Entry point: Learning system
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
└── archive/                      # Old files (move old/ here)
```

**Benefits:**
- ✅ Clear module organization
- ✅ Easy to find files
- ✅ Proper Python package structure
- ✅ Separated code from data
- ✅ Simple entry points
- ✅ Testable modules

---

## 🚀 Migration Steps

### Step 1: Preview Changes (Optional)

```bash
python restructure_project.py --dry-run
```

This shows what will happen without making changes.

### Step 2: Create Entry Points & .gitignore

```bash
python restructure_project.py
```

This creates:
- `run_bot.py` - Start Telegram bot
- `run_web.py` - Start web app
- `update_builds.py` - Update builds online
- `run_learning.py` - Run learning system
- `.gitignore` - Git ignore rules

### Step 3: Migrate Files

```bash
python migrate_structure.py
```

This copies files to new locations (keeps originals).

**What it does:**
- Copies all Python files to `src/` subdirectories
- Moves data files to `data/`
- Preserves original files (for safety)

### Step 4: Update Imports

```bash
python update_imports.py
```

This updates import statements in all migrated files.

**Example changes:**
```python
# Before
from poe2_schema import Poe2Build
from poe2_parser import load_builds

# After
from src.core.schema import Poe2Build
from src.core.parser import load_builds
```

### Step 5: Verify Everything Works

Test each entry point:

```bash
# Test web app
python run_web.py

# Test learning system
python run_learning.py stats

# Test build update (dry run)
python update_builds.py --help
```

### Step 6: Update External Scripts

Manually update `update_builds_online.py` if you still use it:

```python
# Old imports
from poe2_fetcher import update_all_builds
from learning_system import learn_from_builds

# New imports
from src.data.fetcher import update_all_builds
from src.data.learning import learn_from_builds
```

### Step 7: Clean Up

Once verified:

```bash
# Create archive directory
mkdir archive

# Move old files
move poe2_*.py archive/
move llm_extractor_v2.py archive/
move batch_extractor.py archive/
move bot_paginated.py archive/
move learning_system.py archive/
move update_builds_online.py archive/

# Move old/ directory
move old archive/old
```

**⚠️ IMPORTANT:** Only delete after confirming new structure works!

---

## 🔧 Updating Your Workflow

### Before Migration

```bash
# Run bot
python bot_paginated.py

# Update builds
python update_builds_online.py --force

# Run learning
python learning_system.py learn
```

### After Migration

```bash
# Run bot
python run_bot.py

# Update builds
python update_builds.py --force --learn

# Run learning
python run_learning.py learn

# Show stats
python run_learning.py stats
```

---

## 📦 Import Changes Reference

| Old Import | New Import |
|------------|------------|
| `from poe2_schema import Poe2Build` | `from src.core.schema import Poe2Build` |
| `from poe2_parser import load_builds` | `from src.core.parser import load_builds` |
| `from poe2_assistente import get_valid_builds_for_class` | `from src.core.assistant import get_valid_builds_for_class` |
| `from poe2_data_ref import load_reference_data` | `from src.core.validator import load_reference_data` |
| `from poe2_fetcher import update_all_builds` | `from src.data.fetcher import update_all_builds` |
| `from learning_system import learn_from_builds` | `from src.data.learning import learn_from_builds` |
| `from llm_extractor_v2 import extract_build_with_llm` | `from src.extractors.llm_extractor import extract_build_with_llm` |

---

## 🧪 Testing the Migration

Create a simple test script:

```python
# test_migration.py
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all imports work"""
    try:
        from src.core.schema import Poe2Build
        print("✅ src.core.schema imports OK")
        
        from src.core.parser import load_builds
        print("✅ src.core.parser imports OK")
        
        from src.data.fetcher import update_all_builds
        print("✅ src.data.fetcher imports OK")
        
        from src.interfaces.telegram_bot import format_build
        print("✅ src.interfaces.telegram_bot imports OK")
        
        print("\n✅ All imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

if __name__ == "__main__":
    test_imports()
```

Run: `python test_migration.py`

---

## 🔄 Rollback Plan

If something goes wrong:

1. **Original files are still in root** - Nothing was deleted
2. **New files are in src/** - Just delete src/ directory
3. **Data files were copied** - Originals still in root
4. **No git commits yet** - Can discard changes

To rollback:
```bash
# Windows PowerShell
Remove-Item -Recurse -Force src/
Remove-Item run_*.py
Remove-Item update_builds.py

# Your project is back to original state
```

---

## ⚠️ Common Issues & Solutions

### Issue 1: Import Errors After Migration

**Problem:** `ModuleNotFoundError: No module named 'src'`

**Solution:** Add src to Python path:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
```

### Issue 2: Can't Find Data Files

**Problem:** `FileNotFoundError: poe2_builds.json`

**Solution:** Update paths in config.py:
```python
# Old
BUILD_FILE = "poe2_builds.json"

# New
BUILD_FILE = Path(__file__).parent / "data" / "poe2_builds.json"
```

### Issue 3: Flask Templates Not Found

**Problem:** Flask can't find templates/

**Solution:** Update Flask app initialization:
```python
# In src/interfaces/web_app.py
from pathlib import Path
template_folder = Path(__file__).parent.parent.parent / "templates"
app = Flask(__name__, template_folder=template_folder)
```

---

## 📊 Before/After Comparison

### Import Complexity

**Before:**
```python
# Every file has poe2_ prefix - redundant
from poe2_parser import load_builds
from poe2_schema import Poe2Build
from poe2_data_ref import load_reference_data
```

**After:**
```python
# Clear module hierarchy
from src.core.parser import load_builds
from src.core.schema import Poe2Build
from src.core.validator import load_reference_data
```

### File Discovery

**Before:**
- "Where is the validation logic?" → Search through 15 files
- "Which file has the LLM code?" → Not obvious

**After:**
- "Where is the validation logic?" → `src/core/validator.py`
- "Which file has the LLM code?" → `src/extractors/llm_extractor.py`

---

## ✅ Migration Checklist

- [ ] Run `python restructure_project.py --dry-run`
- [ ] Run `python restructure_project.py`
- [ ] Run `python migrate_structure.py`
- [ ] Run `python update_imports.py`
- [ ] Test: `python run_web.py`
- [ ] Test: `python run_learning.py stats`
- [ ] Update any custom scripts
- [ ] Run full test suite (if exists)
- [ ] Create git commit: "Restructure project into packages"
- [ ] Move old files to archive/
- [ ] Update documentation

---

## 🎯 Next Steps After Migration

1. **Performance Improvements** - Add caching
2. **Testing** - Create comprehensive test suite
3. **Code Quality** - Add type hints, standardize naming
4. **Documentation** - Update docstrings

---

## 💡 Tips

- **Don't rush** - Verify each step
- **Keep backups** - Don't delete until confirmed working
- **Test thoroughly** - Run all features
- **Commit often** - Git commit after each major step
- **Ask for help** - If stuck, ask questions

---

**Good luck with the migration! Take it slow and verify at each step.** 🚀
