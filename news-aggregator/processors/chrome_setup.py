"""
Chrome WebDriver setup utilities
"""
import os
import platform
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import subprocess


def get_chrome_path():
    """Get Chrome executable path based on OS"""
    system = platform.system()
    
    if system == 'Darwin':  # macOS
        chrome_paths = [
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            '/Applications/Chromium.app/Contents/MacOS/Chromium',
        ]
        for path in chrome_paths:
            if os.path.exists(path):
                return path
    elif system == 'Linux':
        chrome_paths = [
            '/usr/bin/google-chrome',
            '/usr/bin/chromium',
            '/usr/bin/chromium-browser',
        ]
        for path in chrome_paths:
            if os.path.exists(path):
                return path
    elif system == 'Windows':
        chrome_paths = [
            r'C:\Program Files\Google\Chrome\Application\chrome.exe',
            r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
        ]
        for path in chrome_paths:
            if os.path.exists(path):
                return path
    
    return None


def setup_chrome_driver():
    """Setup Chrome WebDriver with proper configuration"""
    chrome_options = Options()
    
    # Basic options
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # User agent
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Set Chrome binary location if found
    chrome_path = get_chrome_path()
    if chrome_path:
        chrome_options.binary_location = chrome_path
        print(f"[Chrome Setup] Using Chrome at: {chrome_path}")
    
    try:
        # Try to install/update ChromeDriver
        print("[Chrome Setup] Installing/updating ChromeDriver...")
        driver_path = ChromeDriverManager().install()
        print(f"[Chrome Setup] ChromeDriver installed at: {driver_path}")
        
        # Create service
        service = Service(driver_path)
        
        # Create driver
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("[Chrome Setup] WebDriver created successfully")
        
        return driver
        
    except Exception as e:
        print(f"[Chrome Setup] Error setting up ChromeDriver: {e}")
        
        # Try alternative approach for M1/M2 Macs
        if platform.system() == 'Darwin' and platform.machine() == 'arm64':
            print("[Chrome Setup] Trying alternative setup for ARM64 Mac...")
            try:
                # Download ChromeDriver manually if needed
                result = subprocess.run(['which', 'chromedriver'], capture_output=True, text=True)
                if result.returncode == 0:
                    chromedriver_path = result.stdout.strip()
                    print(f"[Chrome Setup] Found system ChromeDriver at: {chromedriver_path}")
                    service = Service(chromedriver_path)
                    driver = webdriver.Chrome(service=service, options=chrome_options)
                    return driver
            except Exception as e2:
                print(f"[Chrome Setup] Alternative setup also failed: {e2}")
        
        raise Exception(f"Failed to setup ChromeDriver: {e}")