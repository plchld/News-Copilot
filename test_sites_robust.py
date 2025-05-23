#!/usr/bin/env python3
"""
Robust test script to validate all configured Greek news sites
This version won't hang and handles timeouts properly
"""

import json
import requests
import signal
import time
from contextlib import contextmanager

class TimeoutException(Exception):
    pass

@contextmanager
def timeout(duration):
    def timeout_handler(signum, frame):
        raise TimeoutException()
    
    # Set the signal handler and a alarm for the duration
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(duration)
    
    try:
        yield
    finally:
        # Reset the alarm and signal handler
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

def load_manifest():
    """Load the extension manifest to get configured sites"""
    with open('extension/manifest.json', 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    sites = []
    for script in manifest.get('content_scripts', []):
        for match in script.get('matches', []):
            # Extract domain from match pattern
            domain = match.replace('*://*.', '').replace('/*', '')
            if domain not in sites:
                sites.append(domain)
    
    return sorted(sites)

def test_site_quick(domain):
    """Quick test if a site is accessible with strict timeout"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'el-GR,el;q=0.9,en;q=0.8',
        'Connection': 'close'  # Important: close connection immediately
    }
    
    print(f"    🔍 Testing {domain}...", end=" ", flush=True)
    
    try:
        with timeout(5):  # Hard 5-second timeout using signals
            response = requests.get(
                f"https://{domain}", 
                timeout=4, 
                headers=headers, 
                stream=True,
                allow_redirects=True
            )
            
            # Read just a tiny bit to verify connection
            try:
                content_sample = response.raw.read(512)
                response.close()
                
                if response.status_code < 400:
                    return True, response.status_code
                else:
                    return False, f"HTTP {response.status_code}"
                    
            except:
                response.close()
                return False, "Content error"
                
    except TimeoutException:
        return False, "Timeout (5s)"
    except requests.exceptions.SSLError:
        # Try HTTP quickly if HTTPS fails
        try:
            with timeout(3):
                response = requests.get(
                    f"http://{domain}", 
                    timeout=2, 
                    headers=headers, 
                    stream=True,
                    allow_redirects=True
                )
                response.close()
                
                if response.status_code < 400:
                    return True, f"{response.status_code} (HTTP)"
                else:
                    return False, f"HTTP {response.status_code}"
        except:
            return False, "SSL Error"
    except requests.exceptions.Timeout:
        return False, "Request timeout"
    except requests.exceptions.ConnectionError:
        return False, "Connection failed"
    except Exception as e:
        return False, f"Error: {type(e).__name__}"

def run_robust_test():
    """Run robust tests that won't hang"""
    print("🧪 Robust News Copilot Site Testing")
    print("=" * 50)
    
    sites = load_manifest()
    print(f"📊 Total configured sites: {len(sites)}")
    print()
    
    # Test sites in batches to avoid hanging
    working_sites = []
    failed_sites = []
    
    for i, site in enumerate(sites, 1):
        print(f"  [{i}/{len(sites)}]", end=" ")
        
        try:
            accessible, status = test_site_quick(site)
            
            if accessible:
                print(f"✅ {site} - {status}")
                working_sites.append(site)
            else:
                print(f"❌ {site} - {status}")
                failed_sites.append(site)
                
        except KeyboardInterrupt:
            print(f"⏹️  Stopped by user at {site}")
            break
        except Exception as e:
            print(f"❌ {site} - Unexpected: {type(e).__name__}")
            failed_sites.append(site)
        
        # Small delay to be nice to servers
        time.sleep(0.2)
    
    # Results summary
    print("\n📈 Final Results:")
    print("=" * 30)
    print(f"✅ Working sites: {len(working_sites)}/{len(sites)}")
    print(f"❌ Failed sites: {len(failed_sites)}/{len(sites)}")
    print(f"🎯 Success rate: {len(working_sites)/len(sites)*100:.1f}%")
    
    if failed_sites:
        print(f"\n❌ Sites with issues:")
        for site in failed_sites:
            print(f"  - {site}")
    
    print(f"\n✅ Working sites include:")
    for site in working_sites[:10]:  # Show first 10
        print(f"  ✓ {site}")
    if len(working_sites) > 10:
        print(f"  ... and {len(working_sites) - 10} more")
    
    return {
        'working': working_sites,
        'failed': failed_sites,
        'success_rate': len(working_sites)/len(sites)*100
    }

if __name__ == "__main__":
    try:
        results = run_robust_test()
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}") 