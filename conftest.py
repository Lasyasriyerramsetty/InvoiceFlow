import os
import sys

# Ensure the repository root is on sys.path so that top-level packages
# (agents, backend, shared, ocr, rag, ml) are importable during tests.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))