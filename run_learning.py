#!/usr/bin/env python
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
