from typing import Dict, List, Optional


def parse_csv_list(raw: str, default: Optional[List[str]] = None) -> Optional[List[str]]:
    """Parse a comma-separated string into a list of stripped, non-empty items.

    Returns ``default`` when ``raw`` is empty or contains only whitespace.
    """
    if not raw:
        return default
    return [item.strip() for item in raw.split(',') if item.strip()]


def build_function_record(
    name: str,
    inputs: List[str],
    outputs: List[str],
    expression: str,
) -> Dict[str, object]:
    """Build the canonical dict representation of a function."""
    return {
        "name": name,
        "inputs": inputs,
        "outputs": outputs,
        "expression": expression,
    }
