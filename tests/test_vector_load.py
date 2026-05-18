import sys
import os

# Ensure we can import from src
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

try:
    from src.database.vector_manager import vector_manager
    print("SUCCESS: VectorManager initialized and model loading logic works.")
except Exception as e:
    print(f"FAILURE: {e}")
    sys.exit(1)
