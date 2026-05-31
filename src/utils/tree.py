def tree_str(data: dict[str, list[str]], indent: str = "") -> str:
    result = ""
    items = list(data.items())
    for i, (key, values) in enumerate(items):
        is_last = i == len(items) - 1
        prefix = "└── " if is_last else "├── "
        result += f"{indent}{prefix}{key} ({len(values)})\n"

        if values:
            next_indent = indent + ("    " if is_last else "│   ")
            for j, val in enumerate(values):
                val_last = j == len(values) - 1
                val_prefix = "└── " if val_last else "├── "
                result += f"{next_indent}{val_prefix}{val}\n"

    return result[:-1]
