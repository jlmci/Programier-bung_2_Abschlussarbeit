import os

def normalize_path_slashes(path_string: str) -> str:
    """
    Ersetzt alle Windows-Backslashes (\\) in einem Pfad-String
    durch Forward-Slashes (/).

    Args:
        path_string (str): Der ursprüngliche Dateipfad-String.

    Returns:
        str: Der Pfad-String mit Forward-Slashes.
    """
    if path_string is None:
        return None
    return path_string.replace('\\', '/')