from pathlib import Path
from .config import initialize_project_at

if __name__ == "__main__":
    initialize_project_at(Path("."))
    print("Project initialized. You can now run 'anna-agent'.")
