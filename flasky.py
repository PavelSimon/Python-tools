import os
import subprocess
from configparser import ConfigParser
from pathlib import Path

from flask import Flask, flash, redirect, render_template_string, url_for

app = Flask(__name__)


def load_secret_key() -> str:
    """Load the Flask secret key from the environment or a config file."""
    key = os.environ.get("SECRET_KEY")
    if key:
        return key
    config_file = Path("config.ini")
    if config_file.exists():
        parser = ConfigParser()
        parser.read(config_file)
        if parser.has_option("flask", "SECRET_KEY"):
            return parser.get("flask", "SECRET_KEY")
    return "your-secret-key-here"


app.secret_key = load_secret_key()

BASE_DIR = Path.cwd().resolve()

@app.route("/")
@app.route("/browse")
@app.route("/browse/<path:subpath>")
def file_list(subpath: str = ""):
    try:
        base_dir = BASE_DIR

        # Construct the current directory path securely
        if subpath:
            current_dir = (base_dir / subpath).resolve()
            if not current_dir.is_relative_to(base_dir) or not current_dir.is_dir():
                flash("Invalid path", "error")
                return redirect(url_for("file_list"))
        else:
            current_dir = base_dir

        files = []
        for item in current_dir.iterdir():
            is_file = item.is_file()
            is_python = item.suffix == ".py" if is_file else False
            files.append(
                {
                    "name": item.name,
                    "is_file": is_file,
                    "is_python": is_python,
                    "size": item.stat().st_size if is_file else None,
                }
            )

        # Sort: directories first, then files
        files.sort(key=lambda x: (x["is_file"], x["name"].lower()))

        # Create breadcrumb navigation
        breadcrumbs = []
        if subpath:
            parts = subpath.split("/")
            current_path = ""
            for part in parts:
                current_path = f"{current_path}/{part}" if current_path else part
                breadcrumbs.append({"name": part, "path": current_path})

        return render_template_string(
            HTML_TEMPLATE,
            files=files,
            current_dir=str(current_dir),
            subpath=subpath,
            breadcrumbs=breadcrumbs,
            base_dir=str(base_dir),
        )
    except Exception as e:
        return f"Error listing files: {e}"

@app.route("/run/<path:filepath>")
def run_script(filepath: str):
    subpath = ""
    try:
        base_dir = BASE_DIR
        full_path = (base_dir / filepath).resolve()
        if not full_path.is_relative_to(base_dir) or full_path.suffix != ".py":
            flash("Invalid file type or path", "error")
            return redirect(url_for("file_list"))

        if not full_path.exists() or not full_path.is_file():
            flash(f"File {filepath} not found", "error")
            return redirect(url_for("file_list"))

        script_dir = full_path.parent
        script_name = full_path.name

        if os.name == "nt":  # Windows
            subprocess.Popen(
                ["cmd", "/c", "start", "cmd", "/k", f'cd /d "{script_dir}" && uv run {script_name}'],
                shell=True,
            )
        else:  # Linux/Mac
            subprocess.Popen(
                [
                    "gnome-terminal",
                    "--",
                    "bash",
                    "-c",
                    f'cd "{script_dir}" && uv run {script_name}; read -p "Press Enter to continue..."',
                ]
            )

        flash(f"Opened terminal to run {filepath} with uv", "success")
        subpath = (
            script_dir.relative_to(base_dir).as_posix() if script_dir != base_dir else ""
        )
    except Exception as e:
        flash(f"Error opening terminal for {filepath}: {e}", "error")
        subpath = Path(filepath).parent.as_posix()

    if subpath:
        return redirect(url_for("file_list", subpath=subpath))
    return redirect(url_for("file_list"))

@app.route("/view/<path:filepath>")
def view_file(filepath: str):
    try:
        base_dir = BASE_DIR
        full_path = (base_dir / filepath).resolve()
        if not full_path.is_relative_to(base_dir):
            flash("Invalid file path", "error")
            return redirect(url_for("file_list"))

        if not full_path.exists() or not full_path.is_file():
            flash(f"File {filepath} not found", "error")
            return redirect(url_for("file_list"))

        # Check if file is too large (limit to 1MB)
        if full_path.stat().st_size > 1024 * 1024:
            flash("File is too large to view (max 1MB)", "error")
            subpath = (
                full_path.parent.relative_to(base_dir).as_posix()
                if full_path.parent != base_dir
                else ""
            )
            if subpath:
                return redirect(url_for("file_list", subpath=subpath))
            return redirect(url_for("file_list"))

        # Try to read the file content
        try:
            content = full_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                content = full_path.read_text(encoding="latin1")
            except Exception:
                flash("Cannot display binary file", "error")
                subpath = (
                    full_path.parent.relative_to(base_dir).as_posix()
                    if full_path.parent != base_dir
                    else ""
                )
                if subpath:
                    return redirect(url_for("file_list", subpath=subpath))
                return redirect(url_for("file_list"))

        # Determine file type for syntax highlighting
        language = "python" if full_path.suffix.lower() == ".py" else "text"

        # Create breadcrumb for the file location
        subpath = (
            full_path.parent.relative_to(base_dir).as_posix()
            if full_path.parent != base_dir
            else ""
        )
        breadcrumbs = []
        if subpath:
            parts = subpath.split("/")
            current_path = ""
            for part in parts:
                current_path = f"{current_path}/{part}" if current_path else part
                breadcrumbs.append({"name": part, "path": current_path})

        return render_template_string(
            FILE_VIEW_TEMPLATE,
            content=content,
            filepath=filepath,
            filename=full_path.name,
            language=language,
            subpath=subpath,
            breadcrumbs=breadcrumbs,
        )

    except Exception as e:
        flash(f"Error viewing file {filepath}: {e}", "error")
        return redirect(url_for("file_list"))

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>File Manager</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .file-list { list-style: none; padding: 0; }
        .file-item { 
            display: flex; 
            align-items: center; 
            padding: 8px; 
            border-bottom: 1px solid #eee; 
        }
        .file-name { 
            flex: 1; 
            margin-right: 10px; 
        }
        .directory { font-weight: bold; color: #0066cc; }
        .python-file { color: #ff6600; }
        .run-btn { 
            background: #28a745; 
            color: white; 
            border: none; 
            padding: 5px 10px; 
            border-radius: 3px; 
            cursor: pointer; 
            margin-left: 5px; 
        }
        .run-btn:hover { background: #218838; }
        .view-btn { 
            background: #007bff; 
            color: white; 
            border: none; 
            padding: 5px 10px; 
            border-radius: 3px; 
            cursor: pointer; 
            margin-left: 5px; 
        }
        .view-btn:hover { background: #0056b3; }
        .action-buttons { display: flex; gap: 5px; }
        .flash-messages { margin-bottom: 20px; }
        .flash-success { color: green; background: #d4edda; padding: 10px; border-radius: 3px; margin: 5px 0; }
        .flash-error { color: red; background: #f8d7da; padding: 10px; border-radius: 3px; margin: 5px 0; }
        .flash-info { color: blue; background: #d1ecf1; padding: 10px; border-radius: 3px; margin: 5px 0; }
        .current-dir { color: #666; margin-bottom: 20px; }
        .breadcrumb { 
            margin-bottom: 15px; 
            padding: 10px; 
            background: #f8f9fa; 
            border-radius: 3px; 
        }
        .breadcrumb a { 
            color: #007bff; 
            text-decoration: none; 
            margin-right: 5px; 
        }
        .breadcrumb a:hover { text-decoration: underline; }
        .folder-link { 
            text-decoration: none; 
            color: #0066cc; 
            cursor: pointer; 
        }
        .folder-link:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <h1>File Manager</h1>
    <div class="current-dir">Current Directory: {{ current_dir }}</div>
    
    <!-- Breadcrumb Navigation -->
    <div class="breadcrumb">
        <a href="{{ url_for('file_list') }}">🏠 Home</a>
        {% for crumb in breadcrumbs %}
            / <a href="{{ url_for('file_list', subpath=crumb.path) }}">{{ crumb.name }}</a>
        {% endfor %}
    </div>
    
    <div class="flash-messages">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="flash-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
    </div>
    
    <ul class="file-list">
        {% for file in files %}
            <li class="file-item">
                {% if not file.is_file %}
                    <a href="{{ url_for('file_list', subpath=(subpath + '/' + file.name) if subpath else file.name) }}" class="folder-link">
                        <span class="file-name directory">
                            📁 {{ file.name }}
                        </span>
                    </a>
                {% else %}
                    <span class="file-name {% if file.is_python %}python-file{% endif %}">
                        📄 {{ file.name }}
                        {% if file.size %}({{ "%.1f"|format(file.size/1024) }} KB){% endif %}
                    </span>
                    <div class="action-buttons">
                        {% set file_ext = file.name.split('.')[-1].lower() %}
                        {% if file.is_python or file_ext in ['txt', 'md', 'json', 'xml', 'html', 'css', 'js', 'ts', 'yml', 'yaml', 'toml', 'ini', 'cfg', 'log'] %}
                            <a href="{{ url_for('view_file', filepath=(subpath + '/' + file.name) if subpath else file.name) }}">
                                <button class="view-btn">👁 View</button>
                            </a>
                        {% endif %}
                        {% if file.is_python %}
                            <a href="{{ url_for('run_script', filepath=(subpath + '/' + file.name) if subpath else file.name) }}">
                                <button class="run-btn">▶ Run</button>
                            </a>
                        {% endif %}
                    </div>
                {% endif %}
            </li>
        {% endfor %}
    </ul>
</body>
</html>
'''

FILE_VIEW_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>{{ filename }} - File Viewer</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 20px; 
            background-color: #f8f9fa; 
        }
        .header { 
            background: white; 
            padding: 20px; 
            border-radius: 5px; 
            margin-bottom: 20px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
        }
        .breadcrumb { 
            margin-bottom: 15px; 
            padding: 10px; 
            background: #e9ecef; 
            border-radius: 3px; 
        }
        .breadcrumb a { 
            color: #007bff; 
            text-decoration: none; 
            margin-right: 5px; 
        }
        .breadcrumb a:hover { text-decoration: underline; }
        .back-btn { 
            background: #6c757d; 
            color: white; 
            border: none; 
            padding: 8px 16px; 
            border-radius: 3px; 
            cursor: pointer; 
            text-decoration: none; 
            display: inline-block; 
            margin-right: 10px; 
        }
        .back-btn:hover { background: #545b62; }
        .file-content { 
            background: white; 
            padding: 20px; 
            border-radius: 5px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
            overflow: auto; 
        }
        .code-content { 
            font-family: 'Courier New', monospace; 
            font-size: 14px; 
            line-height: 1.4; 
            background: #f8f9fa; 
            padding: 15px; 
            border-radius: 3px; 
            border: 1px solid #dee2e6; 
            white-space: pre-wrap; 
            word-wrap: break-word; 
            max-height: 80vh; 
            overflow-y: auto; 
        }
        .file-info { 
            color: #666; 
            font-size: 14px; 
            margin-bottom: 15px; 
        }
        .python-syntax { color: #0000ff; }
        .line-numbers { 
            display: table; 
            width: 100%; 
        }
        .line { 
            display: table-row; 
        }
        .line-number { 
            display: table-cell; 
            text-align: right; 
            padding-right: 10px; 
            color: #999; 
            border-right: 1px solid #ddd; 
            min-width: 50px; 
            user-select: none; 
        }
        .line-content { 
            display: table-cell; 
            padding-left: 10px; 
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="breadcrumb">
            <a href="{{ url_for('file_list') }}">🏠 Home</a>
            {% for crumb in breadcrumbs %}
                / <a href="{{ url_for('file_list', subpath=crumb.path) }}">{{ crumb.name }}</a>
            {% endfor %}
            {% if breadcrumbs %}
                / {{ filename }}
            {% else %}
                / {{ filename }}
            {% endif %}
        </div>
        
        {% if subpath %}
            <a href="{{ url_for('file_list', subpath=subpath) }}" class="back-btn">← Back to Directory</a>
        {% else %}
            <a href="{{ url_for('file_list') }}" class="back-btn">← Back to Directory</a>
        {% endif %}
        
        <h1>📄 {{ filename }}</h1>
        <div class="file-info">
            File: {{ filepath }} | Size: {{ content|length }} characters
        </div>
    </div>
    
    <div class="file-content">
        <div class="code-content line-numbers">
            {% set lines = content.split('\n') %}
            {% for line in lines %}
                <div class="line">
                    <div class="line-number">{{ loop.index }}</div>
                    <div class="line-content">{{ line if line else ' ' }}</div>
                </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(debug=True)
