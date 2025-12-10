import yaml
from pathlib import Path
from .registry import ErrorRegistry


class ErrorConfig:
    def __init__(self, config_file: str):
        self.config_file = config_file
        self.errors = {}

    def load(self):
        path = Path(self.config_file)
        if not path.exists():
            raise FileNotFoundError(f"Error config not found: {path}")

        with open(path, "r") as f:
            data = yaml.safe_load(f)

        self.errors = data.get("errors", {})
        return self.errors


def load_registry() -> ErrorRegistry:
    """
    Returns a ready-to-use ErrorRegistry instance.
    """
    return ErrorRegistry()