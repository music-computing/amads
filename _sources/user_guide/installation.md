# Installation

## Prerequisites

- Python 3.8 or higher
- Git

## Installation Steps

1. Clone the repository:

   ```bash
   git clone https://github.com/music-computing/amads.git
   cd toolkit
   ```

2. Create and activate a virtual environment:

   ```bash
   # Create virtual environment
   python -m venv venv

   # Activate virtual environment
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. Install the package in editable mode:

   ```bash
   # Basic installation
   pip install -e .

   # If you plan to contribute to the codebase
   pip install -e ".[dev]"
   pre-commit install
   ```

Your installation is now complete! The package is installed in editable mode, which means any changes you make to the source code will be reflected immediately without needing to reinstall.

> Note: If you plan to build the documentation or contribute to development, use the second installation command with `[dev]` which includes additional dependencies like Sphinx and other documentation tools.
