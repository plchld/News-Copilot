#!/usr/bin/env python3
"""
Simple HTTP server for serving the test frontend
Usage: python server.py [port]
"""
import http.server
import socketserver
import os
import sys
from pathlib import Path

def main():
    # Get port from command line argument or default to 3001
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3001
    
    # Change to the test-frontend directory
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)
    
    # Create the HTTP server
    handler = http.server.SimpleHTTPRequestHandler
    
    # Add CORS headers for API calls
    class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        def end_headers(self):
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
            super().end_headers()
    
    with socketserver.TCPServer(("", port), CORSHTTPRequestHandler) as httpd:
        print(f"🚀 Test frontend server running at http://localhost:{port}")
        print(f"📁 Serving files from: {script_dir}")
        print("📖 Open http://localhost:{} in your browser to test the agents".format(port))
        print("⏹️  Press Ctrl+C to stop the server")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")

if __name__ == "__main__":
    main() 