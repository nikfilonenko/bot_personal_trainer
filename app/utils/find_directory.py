from pathlib import Path


def find_directory_root(file_name: str) -> Path:
    directory = Path(__file__).resolve().parent.parent.parent / file_name
    if not directory.exists():
        raise FileNotFoundError("File does not exist")
    return directory