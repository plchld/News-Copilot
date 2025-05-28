#!/usr/bin/env python3
"""
Grok API Regional Endpoint Detector
Determines if you're connected to US East or US West region
"""

import asyncio
import time
import sys
import os
import json
import socket
import subprocess
from datetime import datetime
from typing import Dict, Any, List, Tuple

# Add api directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))

from api.grok_client import GrokClient
from api.config import API_URL, API_KEY, MODEL


def get_ip_geolocation(hostname: str) -> Dict[str, Any]:
    """Get IP and geolocation info for a hostname"""
    try:
        # Resolve hostname to IP
        ip = socket.gethostbyname(hostname)
        print(f"🌐 Resolved {hostname} -> {ip}")
        
        # Try to get more info using nslookup/dig if available
        try:
            result = subprocess.run(['nslookup', hostname], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"📋 DNS Info:\n{result.stdout}")
        except:
            pass
            
        return {"ip": ip, "hostname": hostname}
    except Exception as e:
        print(f"❌ Failed to resolve {hostname}: {e}")
        return {"error": str(e)}


def analyze_latency_patterns(response_times: List[float]) -> str:
    """Analyze latency patterns to guess region"""
    if not response_times:
        return "Unknown"
    
    avg_latency = sum(response_times) / len(response_times)
    min_latency = min(response_times)
    max_latency = max(response_times)
    
    print(f"📊 Latency Analysis:")
    print(f"   • Average: {avg_latency:.2f}s")
    print(f"   • Min: {min_latency:.2f}s") 
    print(f"   • Max: {max_latency:.2f}s")
    print(f"   • Variance: {max_latency - min_latency:.2f}s")
    
    # Rough heuristics based on typical latencies from different regions
    if avg_latency < 0.5:
        return "Likely US West (Low latency)"
    elif avg_latency < 1.0:
        return "Likely US East or Central (Medium latency)"
    else:
        return "Possibly International or High Load (High latency)"


async def test_regional_indicators():
    """Test various indicators to determine regional endpoint"""
    print("🌍 GROK API REGIONAL ENDPOINT DETECTION")
    print("="*80)
    
    # Parse the API URL
    from urllib.parse import urlparse
    parsed_url = urlparse(API_URL)
    hostname = parsed_url.hostname
    
    print(f"🎯 Target: {hostname}")
    print(f"🕐 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: DNS and IP Analysis
    print("\n" + "="*60)
    print("🔍 STEP 1: DNS & IP Analysis")
    print("="*60)
    
    ip_info = get_ip_geolocation(hostname)
    
    # Step 2: Response Header Analysis
    print("\n" + "="*60)
    print("🔍 STEP 2: Response Header Analysis")
    print("="*60)
    
    grok_client = GrokClient()
    
    try:
        response = await grok_client.async_client.chat.completions.create(
            model="grok-3-mini",
            messages=[{"role": "user", "content": "What time is it?"}],
            max_tokens=50
        )
        
        # Try to extract headers from the response
        if hasattr(response, '_raw_response'):
            headers = dict(response._raw_response.headers)
            print("📋 Response Headers:")
            for key, value in headers.items():
                print(f"   • {key}: {value}")
                
            # Look for regional indicators in headers
            regional_headers = ['cf-ray', 'server', 'x-served-by', 'x-cache', 'x-amz-cf-pop']
            for header in regional_headers:
                if header in headers:
                    print(f"🎯 Regional indicator found: {header} = {headers[header]}")
        else:
            print("⚠️ No raw response headers available")
            
    except Exception as e:
        print(f"❌ Header analysis failed: {e}")
    
    # Step 3: Latency Pattern Analysis
    print("\n" + "="*60)
    print("🔍 STEP 3: Latency Pattern Analysis")
    print("="*60)
    
    response_times = []
    
    print("🚀 Running 10 quick requests to analyze latency patterns...")
    for i in range(10):
        try:
            start_time = time.time()
            response = await grok_client.async_client.chat.completions.create(
                model="grok-3-mini",
                messages=[{"role": "user", "content": f"Test {i+1}"}],
                max_tokens=5
            )
            elapsed = time.time() - start_time
            response_times.append(elapsed)
            print(f"   Request {i+1:2d}: {elapsed:.3f}s")
            
            # Small delay to avoid rate limiting
            await asyncio.sleep(0.1)
            
        except Exception as e:
            print(f"   Request {i+1:2d}: FAILED - {str(e)[:50]}")
    
    # Analyze the patterns
    region_guess = analyze_latency_patterns(response_times)
    
    # Step 4: Time-based Analysis
    print("\n" + "="*60)
    print("🔍 STEP 4: Server Time Analysis")
    print("="*60)
    
    try:
        response = await grok_client.async_client.chat.completions.create(
            model="grok-3-mini",
            messages=[{"role": "user", "content": "What is the current UTC time? Please be precise."}],
            max_tokens=100
        )
        
        server_time_response = response.choices[0].message.content
        print(f"🕐 Server time response: {server_time_response}")
        
        # Compare with local time
        local_time = datetime.now()
        print(f"🏠 Local time: {local_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"❌ Time analysis failed: {e}")
    
    # Step 5: Traceroute Analysis (if available)
    print("\n" + "="*60)
    print("🔍 STEP 5: Network Route Analysis")
    print("="*60)
    
    try:
        # Try traceroute (macOS/Linux)
        result = subprocess.run(['traceroute', '-m', '10', hostname], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("🛣️ Traceroute results:")
            lines = result.stdout.split('\n')[:8]  # First 8 hops
            for line in lines:
                if line.strip():
                    print(f"   {line}")
        else:
            print("⚠️ Traceroute not available or failed")
    except Exception as e:
        print(f"⚠️ Traceroute analysis failed: {e}")
    
    return region_guess, response_times, ip_info


async def test_concurrent_load():
    """Test concurrent requests to see how the endpoint handles load"""
    print("\n" + "="*60)
    print("🔍 STEP 6: Concurrent Load Test")
    print("="*60)
    
    grok_client = GrokClient()
    
    # Test with 5 concurrent requests
    async def single_request(request_id: int):
        try:
            start_time = time.time()
            response = await grok_client.async_client.chat.completions.create(
                model="grok-3-mini",
                messages=[{"role": "user", "content": f"Concurrent test {request_id}"}],
                max_tokens=10
            )
            elapsed = time.time() - start_time
            return elapsed, True
        except Exception as e:
            return 0, False
    
    print("🚀 Running 5 concurrent requests...")
    start_time = time.time()
    
    tasks = [single_request(i) for i in range(5)]
    results = await asyncio.gather(*tasks)
    
    total_time = time.time() - start_time
    
    successful_times = [r[0] for r in results if r[1]]
    success_rate = len(successful_times) / len(results) * 100
    
    print(f"📊 Concurrent test results:")
    print(f"   • Total time: {total_time:.2f}s")
    print(f"   • Success rate: {success_rate:.1f}%")
    if successful_times:
        print(f"   • Average response time: {sum(successful_times)/len(successful_times):.2f}s")
        print(f"   • Fastest response: {min(successful_times):.2f}s")
        print(f"   • Slowest response: {max(successful_times):.2f}s")


def analyze_regional_conclusion(region_guess: str, response_times: List[float], ip_info: Dict[str, Any]):
    """Provide final analysis of regional endpoint"""
    print("\n" + "="*80)
    print("🎯 REGIONAL ENDPOINT ANALYSIS")
    print("="*80)
    
    print(f"🌍 Endpoint URL: {API_URL}")
    if 'ip' in ip_info:
        print(f"🌐 Resolved IP: {ip_info['ip']}")
    
    print(f"📊 Latency-based guess: {region_guess}")
    
    if response_times:
        avg_latency = sum(response_times) / len(response_times)
        
        print(f"\n🔍 DETAILED ANALYSIS:")
        print(f"   • Average latency: {avg_latency:.3f}s")
        
        # More detailed regional guessing
        if avg_latency < 0.3:
            print("   • 🎯 LIKELY: US West Coast (Very low latency)")
            print("   • 📍 Probable location: California, Oregon, Washington")
        elif avg_latency < 0.6:
            print("   • 🎯 LIKELY: US Central or East Coast (Low-medium latency)")
            print("   • 📍 Probable location: Texas, Illinois, Virginia, New York")
        elif avg_latency < 1.0:
            print("   • 🎯 POSSIBLE: US East Coast or International (Medium latency)")
            print("   • 📍 Probable location: Virginia, New York, or international")
        else:
            print("   • 🎯 LIKELY: International or high load (High latency)")
            print("   • 📍 Could be international routing or server load")
    
    print(f"\n💡 RECOMMENDATIONS:")
    print(f"   • Monitor latency during different times of day")
    print(f"   • Consider your geographic location relative to endpoints")
    print(f"   • Use grok-3-mini for faster responses")
    print(f"   • Implement retry logic for high-latency periods")


async def main():
    """Main regional detection function"""
    region_guess, response_times, ip_info = await test_regional_indicators()
    await test_concurrent_load()
    analyze_regional_conclusion(region_guess, response_times, ip_info)
    
    print("\n" + "="*80)
    print("🏁 REGIONAL ANALYSIS COMPLETE")
    print("="*80)


if __name__ == "__main__":
    if not os.getenv('XAI_API_KEY'):
        print("❌ Error: XAI_API_KEY environment variable not set")
        sys.exit(1)
    
    asyncio.run(main()) 