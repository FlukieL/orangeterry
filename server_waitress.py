#!/usr/bin/env python3
"""
Stable Local Development Server using Waitress
A more robust alternative to the basic HTTP server with better error handling and debugging.

Usage:
    python server_waitress.py [port]
    
Requirements:
    pip install waitress
"""

import webbrowser
import sys
import os
import traceback
import time
from pathlib import Path
from waitress import serve
from wsgiref.simple_server import make_server
from wsgiref.util import FileWrapper
import mimetypes

# Default port
DEFAULT_PORT = 8000

def create_static_file_app(directory):
    """
    Create a WSGI application for serving static files.
    
    Args:
        directory: Directory to serve files from
        
    Returns:
        WSGI application function
    """
    abs_directory = os.path.abspath(directory)
    
    def application(environ, start_response):
        """WSGI application for serving static files."""
        try:
            # Get the requested path
            path = environ.get('PATH_INFO', '/')
            
            # Remove leading slash and resolve path
            if path == '/':
                path = 'index.html'
            else:
                path = path.lstrip('/')
            
            # Build full file path
            file_path = os.path.join(abs_directory, path)
            
            # Security: prevent directory traversal
            file_path = os.path.normpath(file_path)
            if not file_path.startswith(abs_directory):
                # Path outside of served directory
                status = '403 Forbidden'
                headers = [('Content-Type', 'text/plain')]
                start_response(status, headers)
                return [b'403 Forbidden: Access denied']
            
            # Check if file exists
            if not os.path.exists(file_path) or not os.path.isfile(file_path):
                status = '404 Not Found'
                headers = [('Content-Type', 'text/plain')]
                start_response(status, headers)
                return [f'404 Not Found: {path}'.encode()]
            
            # Determine content type
            content_type, _ = mimetypes.guess_type(file_path)
            if content_type is None:
                content_type = 'application/octet-stream'
            
            # Read and serve file
            try:
                with open(file_path, 'rb') as f:
                    file_data = f.read()
                
                # Set headers
                headers = [
                    ('Content-Type', content_type),
                    ('Content-Length', str(len(file_data))),
                    ('Access-Control-Allow-Origin', '*'),
                    ('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'),
                    ('Access-Control-Allow-Headers', '*'),
                    ('Cache-Control', 'no-cache, no-store, must-revalidate'),
                ]
                
                status = '200 OK'
                start_response(status, headers)
                return [file_data]
                
            except IOError as e:
                print(f"[ERROR] Error reading file {file_path}: {e}")
                status = '500 Internal Server Error'
                headers = [('Content-Type', 'text/plain')]
                start_response(status, headers)
                return [b'500 Internal Server Error: Could not read file']
                
        except Exception as e:
            # Log the error for debugging
            print(f"[ERROR] Unexpected error in WSGI application: {type(e).__name__}: {e}")
            traceback.print_exc()
            status = '500 Internal Server Error'
            headers = [('Content-Type', 'text/plain')]
            start_response(status, headers)
            return [f'500 Internal Server Error: {str(e)}'.encode()]
    
    return application

def start_server(port=DEFAULT_PORT):
    """
    Starts a Waitress HTTP server and opens the site in a browser.
    
    Args:
        port: Port number to run the server on (default: 8000)
    """
    try:
        # Change to the script's directory (project root)
        script_dir = Path(__file__).parent.resolve()
        print(f"[INFO] Changing to directory: {script_dir}")
        os.chdir(script_dir)
        print(f"[INFO] Current working directory: {os.getcwd()}")
        
        # Verify the directory exists and contains index.html
        if not script_dir.exists():
            print(f"[ERROR] Directory does not exist: {script_dir}")
            sys.exit(1)
        
        index_path = script_dir / "index.html"
        if not index_path.exists():
            print(f"[WARNING] index.html not found in {script_dir}")
            print(f"[WARNING] Server will still start, but root requests may fail")
        else:
            print(f"[INFO] Verified index.html exists at {index_path}")
        
        # Create WSGI application
        app = create_static_file_app(str(script_dir))
        
        url = f"http://localhost:{port}"
        
        print("=" * 60)
        print(f"Starting Waitress server on port {port}")
        print(f"Server will be accessible at: {url}")
        print(f"Also accessible at: http://127.0.0.1:{port}")
        print(f"Serving directory: {script_dir}")
        print("=" * 60)
        print("Press Ctrl+C to stop the server")
        print()
        
        # Flush output to ensure messages are displayed
        sys.stdout.flush()
        sys.stderr.flush()
        
        # Open browser after a short delay
        def open_browser():
            time.sleep(0.5)  # Give server a moment to start
            try:
                webbrowser.open(url)
                print(f"[INFO] Browser opened at {url}")
            except Exception as browser_error:
                print(f"[WARNING] Could not open browser automatically: {browser_error}")
                print(f"[WARNING] Please manually open: {url}")
        
        import threading
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
        # Start Waitress server
        # Waitress has excellent error handling and is production-ready
        print("[INFO] Server is running and ready to accept connections...")
        print("[INFO] Waitress provides better stability and error recovery than http.server")
        sys.stdout.flush()
        
        try:
            # Serve with Waitress - this blocks until interrupted
            serve(
                app,
                host='0.0.0.0',
                port=port,
                threads=4,  # Use multiple threads for better concurrency
                channel_timeout=120,  # Timeout for connections
                cleanup_interval=30,  # Cleanup interval
                asyncore_use_poll=True,  # Better for Windows
                _quiet=False,  # Show request logs
            )
        except KeyboardInterrupt:
            print("\n[INFO] Received shutdown signal (Ctrl+C)")
            print("[INFO] Shutting down server...")
            print("[INFO] Server stopped.")
            sys.exit(0)
        except Exception as serve_error:
            print(f"\n[ERROR] Server error: {type(serve_error).__name__}: {serve_error}")
            print(f"[ERROR] Full traceback:")
            traceback.print_exc()
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n[INFO] Received interrupt signal before server started")
        sys.exit(0)
    except OSError as e:
        error_msg = str(e)
        print(f"[ERROR] Operating system error occurred!")
        print(f"[ERROR] Error type: {type(e).__name__}")
        print(f"[ERROR] Error message: {error_msg}")
        if "Address already in use" in error_msg or "address is already in use" in error_msg.lower():
            print(f"[ERROR] Port {port} is already in use.")
            print(f"[ERROR] Please use a different port or stop the process using port {port}.")
        else:
            print(f"[ERROR] Full traceback:")
            traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Unexpected error occurred!")
        print(f"[ERROR] Error type: {type(e).__name__}")
        print(f"[ERROR] Error message: {e}")
        print(f"[ERROR] Full traceback:")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    try:
        # Check if waitress is installed
        try:
            import waitress
        except ImportError:
            print("[ERROR] Waitress is not installed.")
            print("[ERROR] Please install it with: pip install waitress")
            sys.exit(1)
        
        # Parse port from command line if provided
        port = DEFAULT_PORT
        if len(sys.argv) > 1:
            try:
                port = int(sys.argv[1])
                if port < 1 or port > 65535:
                    print(f"[ERROR] Invalid port number: {port}")
                    print(f"[ERROR] Port must be between 1 and 65535")
                    sys.exit(1)
            except ValueError:
                print(f"[ERROR] Invalid port number '{sys.argv[1]}'")
                print(f"[ERROR] Port must be a number")
                print(f"Usage: python server_waitress.py [port]")
                sys.exit(1)
        
        print(f"[INFO] Starting Waitress server on port {port}...")
        start_server(port)
        
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted before starting")
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] Fatal error in main: {e}")
        traceback.print_exc()
        sys.exit(1)

