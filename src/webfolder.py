import os
import sys
from http.server import SimpleHTTPRequestHandler, HTTPServer

class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
    def list_directory(self, path):
        import urllib.request, urllib.parse, urllib.error
        import html
        import io
        
        try:
            list = os.listdir(path)
        except OSError:
            self.send_error(404, "No permission to list directory")
            return None
        list.sort(key=lambda a: a.lower())
        
        # Add parent directory link if not at root
        if os.path.dirname(path) != path:
            list.insert(0, '..')
        
        r = []
        displaypath = html.escape(urllib.parse.unquote(self.path))
        enc = sys.getfilesystemencoding()
        title = 'Directory listing for %s' % displaypath
        r.append('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" '
                 '"http://www.w3.org/TR/html4/strict.dtd">')
        r.append('<html>\n<head>')
        r.append('<meta http-equiv="Content-Type" '
                 'content="text/html; charset=%s">' % enc)
        r.append('<title>%s</title>\n</head>' % title)
        r.append('<body>\n<h1>%s</h1>' % title)
        r.append('<hr>\n<ul>')
        
        for name in list:
            fullname = os.path.join(path, name)
            displayname = linkname = name
            if name == '..':
                displayname = '[Parent Directory]'
            elif os.path.isdir(fullname):
                displayname = name + "/"
                linkname = name + "/"
            if os.path.islink(fullname):
                displayname = name + "@"
            r.append('<li><a href="%s">%s</a></li>'
                    % (urllib.parse.quote(linkname), html.escape(displayname)))
        r.append('</ul>\n<hr>\n</body>\n</html>\n')
        encoded = '\n'.join(r).encode(enc)
        f = io.BytesIO()
        f.write(encoded)
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=%s" % enc)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        return f

def serve_folder(folder, port=8000):
    os.chdir(folder)
    server = HTTPServer(('localhost', port), CustomHTTPRequestHandler)
    print(f"Serving {folder} at http://localhost:{port}")
    print("Press Ctrl+C to stop server...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()
        sys.exit(0)

folder = input("Enter folder path to serve (or press Enter for current folder): ")
if not folder:
    folder = os.getcwd()
serve_folder(folder)
