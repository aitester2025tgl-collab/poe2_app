# migrate_structure.py - Safe File Migration Script
"""
This script reorganizes the project structure by copying files to new locations.
Original files are kept in place - you can delete them manually after verification.

New structure:
src/
├── core/          # Schema, parser, validator, assistant
├── data/          # Fetcher, ground truth, learning
├── extractors/    # LLM extractor, batch processor
├── interfaces/    # Bot, web app, GUI
└── utils/         # Backup, logging, helpers

Run: python migrate_structure.py
"""

import shutil
from pathlib import Path
import sys

# Project root
ROOT = Path(__file__).parent

# File mapping: {old_path: new_path}
FILE_MIGRATIONS = {
    # Core modules
    "poe2_schema.py": "src/core/schema.py",
    "poe2_parser.py": "src/core/parser.py",
    "poe2_assistente.py": "src/core/assistant.py",
    "poe2_data_ref.py": "src/core/validator.py",
    
    # Data management
    "poe2_fetcher.py": "src/data/fetcher.py",
    "poe2_ground_truth_manager.py": "src/data/ground_truth.py",
    "learning_system.py": "src/data/learning.py",
    
    # Extractors
    "llm_extractor_v2.py": "src/extractors/llm_extractor.py",
    "batch_extractor.py": "src/extractors/batch_processor.py",
    
    # Interfaces
    "bot_paginated.py": "src/interfaces/telegram_bot.py",
    "poe2_web_editor.py": "src/interfaces/web_app.py",
    "poe2_app_builder.py": "src/interfaces/desktop_gui.py",
    
    # Utils
    "utils/backup.py": "src/utils/backup.py",
    
    # Data files (move to data/)
    "poe2_builds.json": "data/poe2_builds.json",
    "poe2_ref_data.json": "data/poe2_ref_data.json",
    "learning_stats.json": "data/learning_stats.json",
    "extracted_passive_names.json": "data/extracted_passive_names.json",
    "extracted_skill_names.json": "data/extracted_skill_names.json",
    "last_fetch.txt": "data/last_fetch.txt",
}

def migrate_files():
    """Copy files to new structure"""
    print("=" * 60)
    print("🚀 PROJECT STRUCTURE MIGRATION")
    print("=" * 60)
    
    migrated = []
    skipped = []
    errors = []
    
    for old_path, new_path in FILE_MIGRATIONS.items():
        old_file = ROOT / old_path
        new_file = ROOT / new_path
        
        # Check if source exists
        if not old_file.exists():
            skipped.append(f"{old_path} (not found)")
            continue
        
        # Check if destination already exists
        if new_file.exists():
            print(f"⚠️  Skipping {new_path} (already exists)")
            skipped.append(f"{old_path} (destination exists)")
            continue
        
        try:
            # Copy file
            shutil.copy2(old_file, new_file)
            migrated.append(f"{old_path} → {new_path}")
            print(f"✅ Copied: {old_path} → {new_path}")
            
        except Exception as e:
            errors.append(f"{old_path}: {str(e)}")
            print(f"❌ Error copying {old_path}: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 MIGRATION SUMMARY")
    print("=" * 60)
    print(f"✅ Migrated: {len(migrated)} files")
    print(f"⚠️  Skipped: {len(skipped)} files")
    print(f"❌ Errors: {len(errors)} files")
    
    if migrated:
        print("\n✅ Migrated Files:")
        for item in migrated:
            print(f"  • {item}")
    
    if skipped:
        print("\n⚠️  Skipped Files:")
        for item in skipped:
            print(f"  • {item}")
    
    if errors:
        print("\n❌ Errors:")
        for item in errors:
            print(f"  • {item}")
    
    print("\n" + "=" * 60)
    print("📝 NEXT STEPS:")
    print("=" * 60)
    print("1. Verify new files work correctly")
    print("2. Update imports in your code (see update_imports.py)")
    print("3. Run tests to ensure nothing broke")
    print("4. Once verified, delete original files")
    print("5. Move old/ folder contents to archive/")
    print("=" * 60)
    
    return len(errors) == 0

if __name__ == "__main__":
    success = migrate_files()
    sys.exit(0 if success else 1)
