import sys
import os
import pytest

# Ensure we can import from src
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

def test_vector_manager_initialization():
    """Verifies that VectorManager can be initialized and its lazy loaders are present."""
    from src.database.vector_manager import vector_manager
    
    assert vector_manager is not None
    assert hasattr(vector_manager, '_get_collection')
    assert hasattr(vector_manager, '_get_model')
    
    # Verify initial state (lazy loaders shouldn't have run yet)
    assert vector_manager.client is None
    assert vector_manager.model is None

if __name__ == "__main__":
    pytest.main([__file__])
