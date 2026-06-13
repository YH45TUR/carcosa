"""
Sistema Legal CO - Test Configuration
Configura TESTING=true para deshabilitar rate limiting durante tests.
"""
import os

os.environ["TESTING"] = "true"
