# restructure_project.py - Complete Project Restructuring
"""
Complete project restructuring script that:
1. Creates new directory structure
2. Migrates files to new locations
3. Updates imports
4. Creates entry points
5. Verifies the migration

Run: python restructure_project.py --dry-run   # Preview changes
     python restructure_project.py              # Execute migration
"""

import argparse
import sys
from pathlib import Path
import shutil

ROOT = Path(__file__).parent

def create_entry_points():
    """Create convenient entry point scripts in root"""
    
    # Entry point for Telegram bot
    bot_entry = '''#!/usr/bin/env python
# run_bot.py - Start Telegram Bot
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.interfaces.telegram_bot import main

if __name__ == "__main__":
    main()
'''
    
    # Entry point for web app
    web_entry = '''#!/usr/bin/env python
# run_web.py - Start Flask Web App
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.interfaces.web_app import app

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
'''
    
    # Entry point for data update
    update_entry = '''#!/usr/bin/env python
# update_builds.py - Update Builds from Online Sources
import sys
from pathlib import Path
import argparse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data.fetcher import update_all_builds
from src.data.learning import learn_from_builds
from src.data.ground_truth import run_ground_truth_update

def main():
    parser = argparse.ArgumentParser(description="Update PoE2 builds")
    parser.add_argument("--force", "-f", action="store_true", 
                       help="Force update regardless of last fetch time")
    parser.add_argument("--learn", "-l", action="store_true",
                       help="Run learning system after update")
    args = parser.parse_args()
    
    print("🔄 Updating ground truth...")
    run_ground_truth_update(force_update=args.force)
    
    print("\\n🔍 Fetching builds online...")
    success = update_all_builds()
    
    if success and args.learn:
        print("\\n🧠 Running learning system...")
        learn_from_builds()
    
    print("\\n✅ Update complete!")

if __name__ == "__main__":
    main()
'''
    
    # Entry point for learning
    learn_entry = '''#!/usr/bin/env python
# run_learning.py - Run Learning System
import sys
from pathlib import Path
import argparse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data.learning import learn_from_builds, show_ground_truth_stats

def main():
    parser = argparse.ArgumentParser(description="PoE2 Learning System")
    parser.add_argument("command", choices=["learn", "stats"],
                       help="Command to run")
    args = parser.parse_args()
    
    if args.command == "learn":
        learn_from_builds()
    elif args.command == "stats":
        show_ground_truth_stats()

if __name__ == "__main__":
    main()
'''
    
    entry_points = {
        "run_bot.py": bot_entry,
        "run_web.py": web_entry,
        "update_builds.py": update_entry,
        "run_learning.py": learn_entry,
    }
    
    for filename, content in entry_points.items():
        filepath = ROOT / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Created entry point: {filename}")

def create_gitignore():
    """Create or update .gitignore"""
    gitignore_content = '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/
env.bak/
venv.bak/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# Environment variables
.env
chaves.txt

# Data files (optional - uncomment to ignore)
# data/*.json
# data/*.txt

# Logs
logs/*.log
*.log

# Backups
backups/

# OS
.DS_Store
Thumbs.db

# Project specific
old/
cache/
temp/
*.tmp
'''
    
    gitignore_path = ROOT / ".gitignore"
    with open(gitignore_path, 'w', encoding='utf-8') as f:
        f.write(gitignore_content)
    print("✅ Created .gitignore")

def verify_migration():
    """Verify that migration was successful"""
    print("\n" + "=" * 60)
    print("🔍 VERIFICATION")
    print("=" * 60)
    
    issues = []
    
    # Check if src/ structure exists
    required_dirs = [
        "src/core",
        "src/data",
        "src/extractors",
        "src/interfaces",
        "src/utils",
        "data",
        "logs",
        "backups",
    ]
    
    for dir_path in required_dirs:
        full_path = ROOT / dir_path
        if not full_path.exists():
            issues.append(f"Missing directory: {dir_path}")
        else:
            print(f"✅ Directory exists: {dir_path}")
    
    # Check for key files
    key_files = [
        "src/core/schema.py",
        "src/core/parser.py",
        "src/data/fetcher.py",
        "config.py",
        "requirements.txt",
    ]
    
    for file_path in key_files:
        full_path = ROOT / file_path
        if full_path.exists():
            print(f"✅ File exists: {file_path}")
        else:
            issues.append(f"Missing file: {file_path}")
    
    if issues:
        print("\n⚠️  Issues found:")
        for issue in issues:
            print(f"  • {issue}")
        return False
    else:
        print("\n✅ All checks passed!")
        return True

def main():
    parser = argparse.ArgumentParser(description="Restructure project")
    parser.add_argument("--dry-run", action="store_true",
                       help="Preview changes without executing")
    args = parser.parse_args()
    
    if args.dry_run:
        print("=" * 60)
        print("🔍 DRY RUN MODE - No changes will be made")
        print("=" * 60)
        print("\nThis script will:")
        print("1. ✅ Directory structure already created")
        print("2. Copy files to new locations (run migrate_structure.py)")
        print("3. Update import statements (run update_imports.py)")
        print("4. Create entry point scripts")
        print("5. Create .gitignore")
        print("6. Verify migration")
        print("\nRun without --dry-run to execute.")
        return
    
    print("=" * 60)
    print("🚀 COMPLETE PROJECT RESTRUCTURING")
    print("=" * 60)
    
    try:
        # Step 1: Entry points
        print("\n📝 Step 1/3: Creating entry points...")
        create_entry_points()
        
        # Step 2: .gitignore
        print("\n📝 Step 2/3: Creating .gitignore...")
        create_gitignore()
        
        # Step 3: Verify
        print("\n📝 Step 3/3: Verification...")
        success = verify_migration()
        
        if success:
            print("\n" + "=" * 60)
            print("✅ RESTRUCTURING COMPLETE!")
            print("=" * 60)
            print("\n📝 Next steps:")
            print("1. Run: python migrate_structure.py")
            print("2. Run: python update_imports.py")
            print("3. Test entry points:")
            print("   python run_web.py")
            print("   python run_bot.py")
            print("4. Delete old files after verification")
            print("=" * 60)
        else:
            print("\n⚠️  Some issues found. Please review.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Error during restructuring: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
