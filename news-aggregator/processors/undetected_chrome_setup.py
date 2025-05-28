"""
Undetected Chrome WebDriver setup for bypassing detection and macOS security
"""
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
import platform


def setup_undetected_chrome():
    """Setup undetected Chrome WebDriver that bypasses security issues"""
    options = uc.ChromeOptions()
    
    # Headless mode
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    # Additional options for stability
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--no-first-run")
    options.add_argument("--disable-default-apps")
    
    try:
        # Use undetected-chromedriver which handles macOS security better
        print("[Undetected Chrome] Setting up driver...")
        
        # For ARM64 Macs, use specific version
        if platform.system() == 'Darwin' and platform.machine() == 'arm64':
            driver = uc.Chrome(options=options, version_main=None)
        else:
            driver = uc.Chrome(options=options)
            
        print("[Undetected Chrome] Driver setup successful")
        return driver
        
    except Exception as e:
        print(f"[Undetected Chrome] Error: {e}")
        raise