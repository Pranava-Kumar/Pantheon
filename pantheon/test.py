import os

def print_tree(start_path, exclude_dirs=None, prefix=""):
    if exclude_dirs is None:
        exclude_dirs = []

    items = sorted(os.listdir(start_path))
    for i, item in enumerate(items):
        path = os.path.join(start_path, item)

        if item in exclude_dirs:
            continue

        connector = "└── " if i == len(items) - 1 else "├── "
        print(prefix + connector + item)

        if os.path.isdir(path):
            extension = "    " if i == len(items) - 1 else "│   "
            print_tree(path, exclude_dirs, prefix + extension)

print_tree(".", exclude_dirs=[".venv"])