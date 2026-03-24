# utils/exceptions.py - Custom Exception Classes

class PoE2Error(Exception):
    """Base exception for PoE2 application"""
    pass

class DataFetchError(PoE2Error):
    """Raised when data fetching fails"""
    pass

class LLMExtractionError(PoE2Error):
    """Raised when LLM extraction fails"""
    pass

class ValidationError(PoE2Error):
    """Raised when build validation fails"""
    pass

class GroundTruthError(PoE2Error):
    """Raised when ground truth operations fail"""
    pass

class ConfigurationError(PoE2Error):
    """Raised when configuration is invalid"""
    pass

class DataStorageError(PoE2Error):
    """Raised when data storage operations fail"""
    pass
