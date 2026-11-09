"""dmem_double: a TEST DOUBLE of the My Document Memory CLI/MCP contract (test infrastructure, not the product)."""
import os

__version__ = "0.0.0-double"


def mutation():
    """Name of the active deliberate defect (tests/README.md 'Mutations'), or ''."""
    return os.environ.get("DMEM_DOUBLE_MUTATION", "")
