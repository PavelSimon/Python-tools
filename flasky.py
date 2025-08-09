from flask import Flask, render_template, request, redirect, url_for, flash
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
        
        return render_template('file_list.html', files=files, current_dir=current_dir,
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
        
        return render_template('file_view.html',
                               content=content,
                               filepath=filepath,
                               filename=os.path.basename(filepath),
                               language=language,
                               subpath=subpath,
                               breadcrumbs=breadcrumbs)
        
    except Exception as e:
        flash(f"Error viewing file {filepath}: {e}", "error")
        return redirect(url_for('file_list'))


if __name__ == '__main__':
    app.run(debug=True)
