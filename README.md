# Python Development Tools Collection

A collection of useful Python utilities and tools for development and system administration.
Coppied from web changed by cladue code.

Use then on your risk (they are some quite dangerous), it was fun to do it.

## Quick Start

### Prerequisites
- Python 3.8+
- [uv](https://docs.astral.sh/uv/) package manager
- Modern web browser (for Flask tools)

### Installation
```bash
# Clone or download this repository
git clone <repository-url>
cd tools

# Install dependencies
uv sync
```

## Tools Overview

### Flasky - Web File Manager
**File**: `flasky.py`

A Flask-based web file manager with Python script execution capabilities.

**Features**:
- Browse directories and subdirectories
- View text files and Python files with syntax highlighting
- Execute Python scripts using `uv run` in terminal
- Breadcrumb navigation
- Secure file handling with path traversal protection

**Usage**:
```bash
uv run flasky.py
```
Then open http://localhost:5000 in your browser.

**Security Features**:
- File size limits (1MB for viewing)
- Path traversal protection
- File type validation
- Safe script execution in separate terminal

---

### Clip - Clipboard Manager
**File**: `clip.py`

Clipboard utility for copying and pasting text from command line.

---

### WebFolder - Web Directory Server
**File**: `webfolder.py`

Simple HTTP server for sharing directories over the network.

---

### Cron - Task Scheduler
**File**: `cron.py`

Task scheduling utility for automating Python scripts.

---

### Bat - Battery Monitor
**File**: `bat.py`

System battery monitoring and notification tool.

---

### WiFi - Network Manager
**File**: `wifi.py`

WiFi network management and monitoring utility.

## Development

### Project Structure
```
tools/
├── README.md           # This file
├── pyproject.toml      # Project configuration
├── uv.lock             # Lock file
├── .gitignore          # Git ignore rules
├── flasky.py           # Web file manager
├── clip.py             # Clipboard utility
├── webfolder.py        # Web directory server
├── cron.py             # Task scheduler
├── bat.py              # Battery monitor
└── wifi.py             # WiFi manager
```

### Running Individual Tools
Each tool can be run independently:
```bash
# Web file manager
uv run flasky.py

# Clipboard utility
uv run clip.py

# Other tools...
uv run <tool-name>.py
```

### Configuration
- Flask apps run on `localhost:5000` by default
- Debug mode is enabled for development
- File size limits and security settings can be modified in individual files

## Security Considerations

### Flasky Security Features
- **Path Traversal Protection**: Prevents access to parent directories
- **File Type Validation**: Only allows execution of `.py` files
- **File Size Limits**: 1MB limit for file viewing
- **Input Sanitization**: Validates all user inputs
- **Secure Script Execution**: Scripts run in separate terminal processes

### Important Security Notes
**WARNING**: These tools are designed for development and trusted environments only.

- Don't expose Flask apps to the internet without proper authentication
- Review and understand each tool before running
- Use strong secret keys for Flask applications in production
- Be cautious when executing scripts from untrusted sources

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is provided as-is for educational and development purposes.

## Support

For issues and questions:
1. Check the code comments for detailed explanations
2. Review security considerations before deployment
3. Test in safe environments first

---

# Tools

Minimal project scaffold.

## Development

- Install tooling: `pip install -U pip && pip install black isort ruff pytest`
- Enable pre-commit: `pip install pre-commit && pre-commit install`

## Testing

- Run tests: `pytest`

## Linting & Formatting

- Format: `black . && isort .`
- Lint: `ruff check .`

## Environment

- Copy `.env.example` to `.env` and set real values.

**Happy Coding!**
