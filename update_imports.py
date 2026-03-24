# update_imports.py - Update Import Statements After Migration
"""
This script helps update import statements to match the new structure.

After running migrate_structure.py, run this to update imports.

Example changes:
  from poe2_schema import Poe2Build
  → from src.core.schema import Poe2Build

  from poe2_parser import load_builds
  → from src.core.parser import load_builds
"""

from pathlib import Path
import re

ROOT = Path(__file__).parent

# Import mapping: {old_module: new_module}
IMPORT_MAPPING = {
    "poe2_schema": "src.core.schema",
    "poe2_parser": "src.core.parser",
    "poe2_assistente": "src.core.assistant",
    "poe2_data_ref": "src.core.validator",
    "poe2_fetcher": "src.data.fetcher",
    "poe2_ground_truth_manager": "src.data.ground_truth",
    "learning_system": "src.data.learning",
    "llm_extractor_v2": "src.extractors.llm_extractor",
    "batch_extractor": "src.extractors.batch_processor",
    "bot_paginated": "src.interfaces.telegram_bot",
    "poe2_web_editor": "src.interfaces.web_app",
    "poe2_app_builder": "src.interfaces.desktop_gui",
}

def update_imports_in_file(file_path: Path) -> bool:
    """Update imports in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = []
        
        # Update each import
        for old_module, new_module in IMPORT_MAPPING.items():
            # Pattern 1: from X import Y
            pattern1 = rf'from {re.escape(old_module)} import'
            replacement1 = f'from {new_module} import'
            if re.search(pattern1, content):
                content = re.sub(pattern1, replacement1, content)
                changes_made.append(f"from {old_module} → from {new_module}")
            
            # Pattern 2: import X
            pattern2 = rf'^import {re.escape(old_module)}$'
            replacement2 = f'import {new_module}'
            if re.search(pattern2, content, re.MULTILINE):
                content = re.sub(pattern2, replacement2, content, flags=re.MULTILINE)
                changes_made.append(f"import {old_module} → import {new_module}")
        
        # Only write if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Updated: {file_path.relative_to(ROOT)}")
            for change in changes_made:
                print(f"   • {change}")
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ Error updating {file_path}: {e}")
        return False

def update_all_imports():
    """Update imports in all Python files in src/"""
    print("=" * 60)
    print("🔄 UPDATING IMPORT STATEMENTS")
    print("=" * 60)
    
    src_dir = ROOT / "src"
    python_files = list(src_dir.rglob("*.py"))
    
    updated_count = 0
    
    for py_file in python_files:
        if py_file.name == "__init__.py":
            continue
        
        if update_imports_in_file(py_file):
            updated_count += 1
    
    print("\n" + "=" * 60)
    print(f"✅ Updated {updated_count} / {len(python_files)} files")
    print("=" * 60)
    print("\n📝 Manual steps still needed:")
    print("1. Update update_builds_online.py imports")
    print("2. Check for any relative imports (from . import)")
    print("3. Update sys.path.insert() calls if any")
    print("4. Test all modules to ensure imports work")
    print("=" * 60)

if __name__ == "__main__":
    update_all_imports()
