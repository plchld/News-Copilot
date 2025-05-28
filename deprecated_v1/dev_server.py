#!/usr/bin/env python3
"""
Development server that mirrors Vercel deployment structure
Runs both Next.js and Flask API together
"""

import os
import sys
import subprocess
import signal
import time
from threading import Thread

class DevServer:
    def __init__(self):
        self.processes = []
        
    def start_api(self):
        """Start Flask API server"""
        print("🚀 Starting API server on http://localhost:8080...")
        env = os.environ.copy()
        env['PYTHONPATH'] = os.getcwd()
        
        proc = subprocess.Popen(
            [sys.executable, 'api/index.py'],
            env=env
        )
        self.processes.append(proc)
        
    def start_web(self):
        """Start Next.js dev server"""
        print("🚀 Starting web app on http://localhost:3000...")
        
        # Check if node_modules exists
        if not os.path.exists('web/node_modules'):
            print("📦 Installing web dependencies...")
            subprocess.run(['npm', 'install'], cwd='web', check=True)
        
        proc = subprocess.Popen(
            ['npm', 'run', 'dev'],
            cwd='web'
        )
        self.processes.append(proc)
        
    def cleanup(self, signum, frame):
        """Clean up processes on exit"""
        print("\n🛑 Shutting down servers...")
        for proc in self.processes:
            proc.terminate()
        sys.exit(0)
        
    def run(self):
        """Run both servers"""
        # Set up signal handler
        signal.signal(signal.SIGINT, self.cleanup)
        
        # Start servers in threads
        api_thread = Thread(target=self.start_api)
        web_thread = Thread(target=self.start_web)
        
        api_thread.start()
        time.sleep(10)  # Give API time to start
        web_thread.start()
        
        print("\n✅ Development servers started!")
        print("📍 Web app: http://localhost:3000")
        print("📍 API: http://localhost:8080")
        print("\nPress Ctrl+C to stop\n")
        
        # Keep main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.cleanup(None, None)

if __name__ == "__main__":
    # Check prerequisites
    if not os.path.exists('.env'):
        print("⚠️  No .env file found. Creating one...")
        subprocess.run(['make', 'setup-env'])
        print("\n📝 Please add your API keys to .env file and run again.")
        sys.exit(1)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check for required API key
    if not os.getenv('XAI_API_KEY'):
        print("❌ XAI_API_KEY not found in .env file")
        print("Please add your Grok API key and try again.")
        sys.exit(1)
    
    # Run servers
    server = DevServer()
    server.run()