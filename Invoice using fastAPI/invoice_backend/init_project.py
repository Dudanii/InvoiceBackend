import os

folders = [
    "app",
    "app/core",
    "app/models",
    "app/schemas",
    "app/routers",
    "app/services",
    "app/repositories",
    "alembic"
]

files = {
    "app/__init__.py": "",
    "app/main.py": "",
    "app/core/config.py": "",
    "app/models/__init__.py": "",
    "app/schemas/__init__.py": "",
    "app/routers/__init__.py": "",
    "app/services/__init__.py": "",
    "app/repositories/__init__.py": "",
    ".env": "",
    "alembic.ini": "",
    "README.md": "# Invoice Backend"
}

for folder in folders:
    os.makedirs(folder, exist_ok=True)

for path, content in files.items():
    with open(path, "w") as f:
        f.write(content)

print("Project layout created!")
