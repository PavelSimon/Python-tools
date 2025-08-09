from flask import Flask, render_template_string, request, redirect, url_for, flash
import subprocess
import os
from pathlib import Path

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

@app.route("/")
@app.route("/browse")
@app.route("/browse/<path:subpath>")
def file_list(subpath=""):
    try:
        # Get the base directory (where the Flask app is running)
        base_dir = os.getcwd()
        
        # Construct the current directory path
        if subpath:
            # Security: prevent path traversal attacks
            if '..' in subpath or subpath.startswith('/') or ':' in subpath:
                flash("Invalid path", "error")
                return redirect(url_for('file_list'))
            current_dir = os.path.join(base_dir, subpath)
        else:
            current_dir = base_dir
        
        # Check if directory exists
        if not os.path.exists(current_dir) or not os.path.isdir(current_dir):
            flash("Directory not found", "error")
            return redirect(url_for('file_list'))
        
        files = []
        for item in os.listdir(current_dir):
            item_path = os.path.join(current_dir, item)
            is_file = os.path.isfile(item_path)
            is_python = item.endswith('.py') if is_file else False
            files.append({
                'name': item,
                'is_file': is_file,
                'is_python': is_python,
                'size': os.path.getsize(item_path) if is_file else None
            })
        
        # Sort: directories first, then files
        files.sort(key=lambda x: (x['is_file'], x['name'].lower()))
        
        # Create breadcrumb navigation
        breadcrumbs = []
        if subpath:
            parts = subpath.split(os.sep)
            current_path = ""
            for part in parts:
                current_path = os.path.join(current_path, part) if current_path else part
                breadcrumbs.append({
                    'name': part,
                    'path': current_path.replace(os.sep, '/')
                })
        
        return render_template_string(HTML_TEMPLATE, files=files, current_dir=current_dir, 
                                    subpath=subpath, breadcrumbs=breadcrumbs, base_dir=base_dir)
    except Exception as e:
        return f"Error listing files: {e}"

@app.route("/run/<path:filepath>")
def run_script(filepath):
    try:
        # Security: only allow .py files and prevent path traversal
        if not filepath.endswith('.py') or '..' in filepath or filepath.startswith('/') or ':' in filepath:
            flash("Invalid file type or path", "error")
            return redirect(url_for('file_list'))
        
        # Construct full file path
        base_dir = os.getcwd()
        full_path = os.path.join(base_dir, filepath)
        
        if not os.path.exists(full_path) or not os.path.isfile(full_path):
            flash(f"File {filepath} not found", "error")
            return redirect(url_for('file_list'))
        
        # Get the directory containing the file to run the script from there
        script_dir = os.path.dirname(full_path)
        script_name = os.path.basename(full_path)
        
        # Open terminal and run the Python file with uv
        if os.name == 'nt':  # Windows
            subprocess.Popen(['cmd', '/c', 'start', 'cmd', '/k', f'cd /d "{script_dir}" && uv run {script_name}'], shell=True)
        else:  # Linux/Mac
            subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', f'cd "{script_dir}" && uv run {script_name}; read -p "Press Enter to continue..."'])
        
        flash(f"Opened terminal to run {filepath} with uv", "success")
            
    except Exception as e:
        flash(f"Error opening terminal for {filepath}: {e}", "error")
    
    # Redirect back to the current directory
    subpath = os.path.dirname(filepath).replace(os.sep, '/') if os.path.dirname(filepath) else ""
    if subpath:
        return redirect(url_for('file_list', subpath=subpath))
    else:
        return redirect(url_for('file_list'))

@app.route("/view/<path:filepath>")
def view_file(filepath):
    try:
        # Security: prevent path traversal
        if '..' in filepath or filepath.startswith('/') or ':' in filepath:
            flash("Invalid file path", "error")
            return redirect(url_for('file_list'))
        
        # Construct full file path
        base_dir = os.getcwd()
        full_path = os.path.join(base_dir, filepath)
        
        if not os.path.exists(full_path) or not os.path.isfile(full_path):
            flash(f"File {filepath} not found", "error")
            return redirect(url_for('file_list'))
        
        # Check if file is too large (limit to 1MB)
        if os.path.getsize(full_path) > 1024 * 1024:
            flash("File is too large to view (max 1MB)", "error")
            subpath = os.path.dirname(filepath).replace(os.sep, '/') if os.path.dirname(filepath) else ""
            if subpath:
                return redirect(url_for('file_list', subpath=subpath))
            else:
                return redirect(url_for('file_list'))
        
        # Try to read the file content
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with different encodings
            try:
                with open(full_path, 'r', encoding='latin1') as f:
                    content = f.read()
            except:
                flash("Cannot display binary file", "error")
                subpath = os.path.dirname(filepath).replace(os.sep, '/') if os.path.dirname(filepath) else ""
                if subpath:
                    return redirect(url_for('file_list', subpath=subpath))
                else:
                    return redirect(url_for('file_list'))
        
        # Determine file type for syntax highlighting
        file_ext = os.path.splitext(filepath)[1].lower()
        language = 'python' if file_ext == '.py' else 'text'
        
        # Create breadcrumb for the file location
        subpath = os.path.dirname(filepath).replace(os.sep, '/') if os.path.dirname(filepath) else ""
        breadcrumbs = []
        if subpath:
            parts = subpath.split('/')
            current_path = ""
            for part in parts:
                current_path = current_path + '/' + part if current_path else part
                breadcrumbs.append({
                    'name': part,
                    'path': current_path
                })
        
        return render_template_string(FILE_VIEW_TEMPLATE, 
                                    content=content, 
                                    filepath=filepath,
                                    filename=os.path.basename(filepath),
                                    language=language,
                                    subpath=subpath,
                                    breadcrumbs=breadcrumbs)
        
    except Exception as e:
        flash(f"Error viewing file {filepath}: {e}", "error")
        return redirect(url_for('file_list'))

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
