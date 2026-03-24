# tests/test_parser.py - Unit Tests for Parser Module
import unittest
import json
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from poe2_parser import calculate_recommendation_score, is_build_valid

class TestParser(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.valid_build = {
            "build_name": "Test Earthquake Build",
            "class": "Warrior",
            "version": "0.3",
            "reputation": 75000,
            "skill_tree_leveling": [
                {
                    "level_range": "1-10",
                    "actions": [
                        {
                            "type": "Skill",
                            "name": "Earthquake",
                            "level": 1,
                            "passives": ["Resolute Technique"]
                        },
                        {
                            "type": "Skill",
                            "name": "Shield Charge",
                            "level": 4,
                            "passives": []
                        },
                        {
                            "type": "Skill",
                            "name": "Boneshatter",
                            "level": 8,
                            "passives": ["Iron Grip"]
                        }
                    ]
                }
            ]
        }
        
        self.invalid_build = {
            "build_name": "Invalid Build",
            "class": "Warrior",
            "version": "0.3",
            "reputation": 10000,
            "skill_tree_leveling": [
                {
                    "level_range": "1-10",
                    "actions": [
                        {
                            "type": "Skill",
                            "name": "UnknownSkill123",
                            "level": 1,
                            "passives": []
                        }
                    ]
                }
            ]
        }
    
    def test_recommendation_score_calculation(self):
        """Test recommendation score calculation"""
        confidence, rep_norm, score = calculate_recommendation_score(self.valid_build)
        
        # Check types
        self.assertIsInstance(confidence, float)
        self.assertIsInstance(rep_norm, float)
        self.assertIsInstance(score, float)
        
        # Check ranges
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
        self.assertGreaterEqual(rep_norm, 0.0)
        self.assertLessEqual(rep_norm, 1.0)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 100.0)
    
    def test_build_validation(self):
        """Test build validation logic"""
        # Note: This requires ground truth to be loaded
        # In production, you'd mock the ground truth data
        pass
    
    def test_score_components(self):
        """Test that score properly weights confidence and reputation"""
        confidence, rep_norm, score = calculate_recommendation_score(self.valid_build)
        
        # Calculate expected score
        expected = (confidence * 0.7 + rep_norm * 0.3) * 100
        
        # Allow small floating point differences
        self.assertAlmostEqual(score, expected, places=2)

class TestBuildStructure(unittest.TestCase):
    
    def test_required_fields(self):
        """Test that builds have required fields"""
        required_fields = ['build_name', 'class', 'version', 'reputation', 'skill_tree_leveling']
        
        build = {
            "build_name": "Test",
            "class": "Warrior",
            "version": "0.3",
            "reputation": 50000,
            "skill_tree_leveling": []
        }
        
        for field in required_fields:
            self.assertIn(field, build)
    
    def test_skill_tree_structure(self):
        """Test skill tree leveling structure"""
        skill_tree = [
            {
                "level_range": "1-10",
                "actions": [
                    {
                        "type": "Skill",
                        "name": "TestSkill",
                        "level": 1,
                        "passives": []
                    }
                ]
            }
        ]
        
        self.assertIsInstance(skill_tree, list)
        self.assertGreater(len(skill_tree), 0)
        
        step = skill_tree[0]
        self.assertIn('level_range', step)
        self.assertIn('actions', step)
        self.assertIsInstance(step['actions'], list)

if __name__ == '__main__':
    unittest.main()
