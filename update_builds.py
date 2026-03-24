#!/usr/bin/env python
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
    
    print("\n🔍 Fetching builds online...")
    success = update_all_builds()
    
    if success and args.learn:
        print("\n🧠 Running learning system...")
        learn_from_builds()
    
    print("\n✅ Update complete!")

if __name__ == "__main__":
    main()
