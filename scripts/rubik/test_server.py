#!/usr/bin/env python3
"""
Simple HTTP server for testing the Cube Generator

Run this server, then open test_cube_generator.html in a browser.
The HTML will send requests to /api/generate to render cubes.

Usage:
    python test_server.py
    
Then open: http://localhost:8080
"""

import json
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler

# Import cube generator (same directory)
try:
    from gen_rubik_guide import render_svg_exploded, string_to_state, apply_algorithm
    print("[STARTUP] Successfully imported gen_rubik_guide", file=sys.stderr)
except ImportError as e:
    print(f"[ERROR] Could not import gen_rubik_guide: {e}", file=sys.stderr)
    sys.exit(1)


class CubeGeneratorHandler(SimpleHTTPRequestHandler):
    """HTTP handler for cube generation API"""
    
    def do_POST(self):
        """Handle POST requests to /api/generate"""
        if self.path == '/api/generate':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length).decode('utf-8')
                data = json.loads(body)
                
                state_str = data.get('state', '')
                moves_str = data.get('moves', '')
                
                # Validate state
                if len(state_str) != 54:
                    self.send_response(400)
                    self.send_header('Content-Type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(f"Error: State must be 54 characters, got {len(state_str)}".encode())
                    return
                
                # Generate cube state
                try:
                    state = string_to_state(state_str)
                    if moves_str.strip():
                        state = apply_algorithm(state, moves_str)
                except Exception as e:
                    self.send_response(400)
                    self.send_header('Content-Type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(f"Error: {str(e)}".encode())
                    return
                
                # Render SVG
                try:
                    svg = render_svg_exploded(state, size=500)
                except Exception as e:
                    self.send_response(500)
                    self.send_header('Content-Type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(f"Error rendering SVG: {str(e)}".encode())
                    return
                
                # Return SVG
                self.send_response(200)
                self.send_header('Content-Type', 'image/svg+xml')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(svg.encode('utf-8'))
                
            except json.JSONDecodeError as e:
                self.send_response(400)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(f"Invalid JSON: {str(e)}".encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(f"Server error: {str(e)}".encode())
        else:
            # Serve static files (HTML, CSS, JS, etc.)
            super().do_GET()
    
    def do_GET(self):
        """Handle GET requests (serve static files)"""
        if self.path == '/' or self.path == '':
            self.path = '/test_cube_generator.html'
        super().do_GET()
    
    def log_message(self, format, *args):
        """Custom logging"""
        print(f"[{self.log_date_time_string()}] {format % args}", file=sys.stderr)


def run_server(host='localhost', port=8080):
    """Start the test server"""
    server_address = (host, port)
    httpd = HTTPServer(server_address, CubeGeneratorHandler)
    
    # Print with flush to ensure output appears immediately
    print("", flush=True)
    print("╔════════════════════════════════════════════════════════════╗", flush=True)
    print("║  Rubik's Cube Generator - Test Server                      ║", flush=True)
    print("╠════════════════════════════════════════════════════════════╣", flush=True)
    print(f"║  Server running at: http://{host}:{port}", flush=True)
    print(f"║  Open in browser: http://{host}:{port}", flush=True)
    print("║                                                            ║", flush=True)
    print("║  Press Ctrl+C to stop                                      ║", flush=True)
    print("╚════════════════════════════════════════════════════════════╝", flush=True)
    print("", flush=True)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped", flush=True)
        sys.exit(0)


if __name__ == '__main__':
    # Serve from scripts/rubik/ directory so test_cube_generator.html is found
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Parse command line arguments
    host = 'localhost'
    port = 8080
    
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Error: Port must be an integer, got '{sys.argv[1]}'")
            sys.exit(1)
    
    if len(sys.argv) > 2:
        host = sys.argv[2]
    
    run_server(host, port)
