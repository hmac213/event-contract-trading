"""
Backend Tests Package

This package contains test scripts and utilities for the event contract trading platform.

Available test modules:
- test_platform_reader: Tests platform data reading functionality
- test_platform_grapher: Tests platform data visualization functionality

Usage:
    # Run individual tests from project root:
    python -m backend.tests.test_platform_reader
    python -m backend.tests.test_platform_grapher
    
    # Run with test mode:
    python -m backend.tests.test_platform_reader all  # Test all platforms
    python -m backend.tests.test_platform_grapher test  # Save to file instead of showing
"""

__all__ = ['test_platform_reader', 'test_platform_grapher', 'test_platform_order_book']
