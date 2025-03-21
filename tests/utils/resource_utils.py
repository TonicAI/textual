from pathlib import Path


def get_relative_path(file_path):
    current_file = Path(__file__).resolve()
    return str(current_file.parent / file_path)


def get_resource_path(filename):
    """
    Get the absolute path to a resource file in the resources directory.

    Args:
        filename: Name of the file in the resources directory

    Returns:
        Absolute path to the resource file
    """
    # Get the current file's path
    current_file = Path(__file__).resolve()

    # Find the resources directory relative to the pytests root
    # By navigating up to the 'pytests' directory and then to resources
    test_root = current_file.parent
    max_depth = 15  # Maximum levels to traverse upward
    depth = 0

    while (
        test_root.name != "tests"
        and test_root.parent != test_root
        and depth < max_depth
    ):
        test_root = test_root.parent
        depth += 1

    if test_root.name != "tests":
        raise ValueError(
            f"Could not find 'tests' directory within {max_depth} levels"
        )

    # Construct the path to the resources directory
    resources_dir = test_root / "resources"

    # Return the full path to the specified file
    return str(resources_dir / filename)


def read_resource_file(filename, encoding="utf-8"):
    """
    Read the content of a resource file.

    Args:
        filename: Name of the file in the resources directory
        encoding: File encoding (default: utf-8)

    Returns:
        Content of the file as string
    """
    with open(get_resource_path(filename), "r", encoding=encoding) as f:
        return f.read()
