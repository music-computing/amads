#!/usr/bin/env python3
"""
Check that all Python modules in amads/ are documented in docs/reference/
and that all documentation files are listed in mkdocs.yml.
"""

import re
from pathlib import Path
from typing import Dict, List, Set

import yaml


def find_python_modules(base_dir: str = "amads"):
    """
    Find all .py files in amads/ and convert to Python module names.

    Returns
    -------
    Tuple of (modules, package_only_modules)
    - modules: Set of module names like 'amads.core.basics'
    - package_only_modules: Set of packages that only contain __init__.py
    """
    modules = set()
    package_only_modules = set()
    amads_path = Path(base_dir)

    # Track all packages and their contents
    package_contents = {}  # package_path -> list of .py files

    for py_file in amads_path.rglob("*.py"):
        # Skip __pycache__ and other special directories
        if "__pycache__" in py_file.parts:
            continue

        # Skip symlinks (e.g., Emacs lock files like .#key_cc.py)
        if py_file.is_symlink():
            continue

        # Convert path to module name
        relative_path = py_file.relative_to(amads_path.parent)

        # Remove .py extension
        module_parts = list(relative_path.parts)
        module_parts[-1] = module_parts[-1].replace(".py", "")

        # Track package contents
        if len(module_parts) > 1:
            package_path = ".".join(module_parts[:-1])
            if package_path not in package_contents:
                package_contents[package_path] = []
            package_contents[package_path].append(module_parts[-1])

        # Skip __init__ files (the package itself is the module)
        if module_parts[-1] == "__init__":
            # If it's just amads/__init__.py, use 'amads'
            if len(module_parts) == 2:
                modules.add(module_parts[0])
            else:
                # For deeper __init__.py, use the package path
                modules.add(".".join(module_parts[:-1]))
        else:
            modules.add(".".join(module_parts))

    # Identify packages that only contain __init__.py
    for package, contents in package_contents.items():
        if contents == ["__init__"] and package in modules:
            package_only_modules.add(package)

    return modules, package_only_modules


def find_documented_modules(docs_dir: str = "docs/reference"):
    """
    Find all module references in .md files in docs/reference/.

    Returns
    -------
    Tuple of (documented, modules_with_members_true)
    - documented: Dict mapping markdown files to lists of modules they document
    - modules_with_members_true: Set of modules that have 'members: true' option
    """
    docs_path = Path(docs_dir)
    documented = {}
    modules_with_members_true = set()

    # Pattern to match ::: amads.module.name
    pattern = re.compile(r":::\s+(amads(?:\.[a-zA-Z_][a-zA-Z0-9_]*)+)")

    for md_file in docs_path.rglob("*.md"):
        relative_path = md_file.relative_to(docs_path)
        modules_in_file = []

        try:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")

                i = 0
                while i < len(lines):
                    line = lines[i]
                    match = pattern.match(line.strip())
                    if match:
                        module = match.group(1)
                        modules_in_file.append(module)

                        # Check if this module has 'members: true' in its options block
                        # Look ahead until we hit a blank line or another ::: directive
                        j = i + 1
                        has_members_true = False
                        while j < len(lines):
                            next_line = lines[j].strip()
                            # Stop at blank line or next directive
                            if not next_line or next_line.startswith(":::"):
                                break
                            if "members:" in next_line and "true" in next_line:
                                has_members_true = True
                                break
                            j += 1

                        if has_members_true:
                            modules_with_members_true.add(module)

                    i += 1

        except Exception as e:
            print(f"Warning: Could not read {md_file}: {e}")
            continue

        if modules_in_file:
            documented[str(relative_path)] = modules_in_file

    return documented, modules_with_members_true


def get_all_documented_modules(documented: Dict[str, List[str]]) -> Set[str]:
    """Get a flat set of all documented modules."""
    all_modules = set()
    for modules in documented.values():
        all_modules.update(modules)
    return all_modules


def find_md_files_in_mkdocs(mkdocs_path: str = "mkdocs.yml") -> Set[str]:
    """
    Parse mkdocs.yml and extract all markdown file references.

    Returns
    -------
    Set of markdown file paths referenced in mkdocs.yml
    """
    try:
        with open(mkdocs_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"Error reading {mkdocs_path}: {e}")
        return set()

    md_files = set()

    def extract_md_files(obj):
        """Recursively extract .md file references from nav structure."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str) and value.endswith(".md"):
                    # Extract just the relative path from reference/ onward
                    if value.startswith("reference/"):
                        # Keep it as is (e.g., 'reference/algorithms/complexity.md')
                        md_files.add(value)
                    elif not value.startswith(
                        (
                            "index.md",
                            "paper.md",
                            "user_guide/",
                            "developer_notes/",
                        )
                    ):
                        # Other docs not under reference/
                        pass
                extract_md_files(value)
        elif isinstance(obj, list):
            for item in obj:
                # Handle both dict items (label: path) and string items (just path)
                if isinstance(item, str) and item.endswith(".md"):
                    if item.startswith("reference/"):
                        md_files.add(item)
                extract_md_files(item)

    if "nav" in config:
        extract_md_files(config["nav"])

    return md_files


def main():
    print("=" * 70)
    print("Checking Python module documentation coverage")
    print("=" * 70)
    print()

    # Step 1: Find all Python modules
    print("Step 1: Finding all Python modules in amads/...")
    python_modules, package_only_modules = find_python_modules()
    print(f"Found {len(python_modules)} Python modules")
    print(
        f"Found {len(package_only_modules)} package-only modules (only __init__.py)"
    )
    print()

    # Step 2: Find documented modules
    print("Step 2: Finding documented modules in docs/reference/...")
    documented, modules_with_members_true = find_documented_modules()
    all_documented = get_all_documented_modules(documented)

    # For modules with 'members: true', add all their submodules from python_modules
    for module_with_members in modules_with_members_true:
        for py_module in python_modules:
            if py_module.startswith(module_with_members + "."):
                all_documented.add(py_module)

    # Consider a module documented if any of its submodules/functions/classes are documented
    # E.g., if amads.algorithms.entropy.entropy is documented, then amads.algorithms.entropy is too
    effectively_documented = set(all_documented)
    for doc_module in all_documented:
        parts = doc_module.split(".")
        # Add all parent modules
        for i in range(1, len(parts)):
            parent = ".".join(parts[:i])
            effectively_documented.add(parent)

    print(
        f"Found {len(all_documented)} documented modules in {len(documented)} .md files"
    )
    print(
        f"Found {len(modules_with_members_true)} modules with 'members: true' option"
    )
    print(
        f"(Including parent modules: {len(effectively_documented)} effectively documented)"
    )
    print()

    # Step 3: Find .md files in mkdocs.yml
    print("Step 3: Checking mkdocs.yml for documentation file references...")
    mkdocs_md_files = find_md_files_in_mkdocs()
    actual_md_files = set(documented.keys())
    print(f"Found {len(mkdocs_md_files)} .md files referenced in mkdocs.yml")
    # Debug: show what was found
    if False:  # Set to True to debug
        print("Files in mkdocs.yml:")
        for f in sorted(mkdocs_md_files):
            print(f"  - {f}")
        print("Actual files:")
        for f in sorted(actual_md_files):
            print(f"  - reference/{f}")
    print()

    # Analysis 1: Modules without documentation
    print("=" * 70)
    print("ANALYSIS: Modules without documentation")
    print("=" * 70)
    # Exclude package-only modules and intentionally ignored files from undocumented check
    ignored_modules = {"amads.ci", "amads.all"}  # Files to intentionally ignore
    undocumented = (
        python_modules
        - effectively_documented
        - package_only_modules
        - ignored_modules
    )
    if undocumented:
        print(f"Found {len(undocumented)} undocumented modules:")
        for module in sorted(undocumented):
            print(f"  - {module}")
    else:
        print("✓ All Python modules are documented!")

    if package_only_modules:
        print()
        print(
            f"Note: {len(package_only_modules)} package-only modules (only __init__.py) excluded from check:"
        )
        for module in sorted(package_only_modules):
            print(f"  - {module}")
    print()

    # Analysis 2: Documentation files not in mkdocs.yml
    print("=" * 70)
    print("ANALYSIS: Documentation files not listed in mkdocs.yml")
    print("=" * 70)
    # Convert paths to the same format for comparison
    # mkdocs_md_files has 'reference/...' format
    # actual_md_files has '...' format relative to docs/reference/
    actual_md_files_with_reference = {
        "reference/" + doc for doc in actual_md_files
    }
    unlisted_docs = actual_md_files_with_reference - mkdocs_md_files
    if unlisted_docs:
        print(f"Found {len(unlisted_docs)} .md files not in mkdocs.yml:")
        for doc in sorted(unlisted_docs):
            print(f"  - {doc}")
    else:
        print("✓ All documentation files are listed in mkdocs.yml!")
    print()

    # Analysis 3: Files in mkdocs.yml that don't exist
    print("=" * 70)
    print("ANALYSIS: Files in mkdocs.yml that don't exist")
    print("=" * 70)
    missing_files = mkdocs_md_files - actual_md_files_with_reference
    if missing_files:
        print(f"Found {len(missing_files)} referenced files that don't exist:")
        for doc in sorted(missing_files):
            print(f"  - {doc}")
    else:
        print("✓ All files in mkdocs.yml exist!")
    print()

    # Analysis 4: Summary by documentation file
    print("=" * 70)
    print("SUMMARY: Documentation files and their modules")
    print("=" * 70)
    for doc_file in sorted(documented.keys()):
        modules = documented[doc_file]
        in_mkdocs = "✓" if doc_file in mkdocs_md_files else "✗"
        print(f"{in_mkdocs} reference/{doc_file} ({len(modules)} modules)")
        for module in sorted(modules):
            print(f"    - {module}")
    print()

    # Final summary
    print("=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    print(f"Total Python modules: {len(python_modules)}")
    print(f"Documented modules: {len(all_documented)}")
    print(f"Undocumented modules: {len(undocumented)}")
    print(f"Documentation files: {len(actual_md_files)}")
    print(f"Files in mkdocs.yml: {len(mkdocs_md_files)}")
    print(f"Files not in mkdocs.yml: {len(unlisted_docs)}")
    print()

    if undocumented or unlisted_docs or missing_files:
        print("❌ Issues found! Please review the analysis above.")
        return 1
    else:
        print("✅ All checks passed!")
        return 0


if __name__ == "__main__":
    exit(main())
