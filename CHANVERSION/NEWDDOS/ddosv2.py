#!/usr/bin/env python3

import argparse
import asyncio
import logging
import signal
import statistics
import time
from collections import Counter
from dataclasses import dataclass

import aiohttp


DEFAULT_URL = "https://genggi.com/"
DEFAULT_STAGE_DURATION = 10
DEFAULT_RAMP = "10,25,50,100"
DEFAULT_CONCURRENCY = 500
DEFAULT_TIMEOUT = 10.0

# Controlled benchmark limits.
MAX_CONCURRENCY = 100
MAX_RPS = 100.0

MAX_429_RATE = 0.10
MAX_5XX_RATE = 0.20
MAX_TIMEOUT_RATE = 0.20

WINDOW_SIZE = 50
PROGRESS_INTERVAL = 1.0


@dataclass(slots=True)
class Result:
    status: int | None
    latency: float
    error: str | None = None


@dataclass(slots=True)
class StageStats:
    requests: int = 0
    successful: int = 0
    failed: int = 0
    timeouts: int = 0
    rate_limited: int = 0
    server_errors: int = 0


def percentile(
    values: list[float],
    percent: float,
) -> float:
    if not values:
        return 0.0

    ordered = sorted(values)

    position = (
        len(ordered) - 1
    ) * percent / 100.0

    lower = int(position)
    upper = min(
        lower + 1,
        len(ordered) - 1,
    )

    fraction = position - lower

    return (
        ordered[lower]
        + (
            ordered[upper]
            - ordered[lower]
        ) * fraction
    )


def calculate_metrics(
    results: list[Result],
    elapsed: float,
) -> dict:

    if not results:
        return {
            "requests": 0,
            "rps": 0.0,
            "p50": 0.0,
            "p95": 0.0,
            "p99": 0.0,
            "error_rate": 0.0,
            "429_rate": 0.0,
            "5xx_rate": 0.0,
            "timeout_rate": 0.0,
        }

    latencies = [
        result.latency
        for result in results
    ]

    total = len(results)

    errors = sum(
        result.status is None
        or result.status >= 400
        for result in results
    )

    rate_limited = sum(
        result.status == 429
        for result in results
    )

    server_errors = sum(
        result.status is not None
        and 500 <= result.status <= 599
        for result in results
    )

    timeouts = sum(
        result.error == "timeout"
        for result in results
    )

    return {
        "requests": total,
        "rps": total / max(elapsed, 0.001),
        "p50": percentile(latencies, 50),
        "p95": percentile(latencies, 95),
        "p99": percentile(latencies, 99),
        "error_rate": errors / total,
        "429_rate": rate_limited / total,
        "5xx_rate": server_errors / total,
        "timeout_rate": timeouts / total,
    }


def degradation_reason(
    results: list[Result],
) -> str | None:

    if len(results) < WINDOW_SIZE:
        return None

    recent = results[-WINDOW_SIZE:]
    total = len(recent)

    rate_429 = sum(
        r.status == 429
        for r in recent
    ) / total

    rate_5xx = sum(
        r.status is not None
        and 500 <= r.status <= 599
        for r in recent
    ) / total

    timeout_rate = sum(
        r.error == "timeout"
        for r in recent
    ) / total

    if rate_429 >= MAX_429_RATE:
        return (
            f"429 rate reached "
            f"{rate_429 * 100:.1f}%"
        )

    if rate_5xx >= MAX_5XX_RATE:
        return (
            f"5xx rate reached "
            f"{rate_5xx * 100:.1f}%"
        )

    if timeout_rate >= MAX_TIMEOUT_RATE:
        return (
            f"timeout rate reached "
            f"{timeout_rate * 100:.1f}%"
        )

    return None


async def worker(
    session: aiohttp.ClientSession,
    url: str,
    end_time: float,
    interval: float,
    results: list[Result],
    stop_event: asyncio.Event,
    worker_id: int,
) -> None:

    while (
        time.monotonic() < end_time
        and not stop_event.is_set()
    ):

        started = time.perf_counter()

        try:
            async with session.get(
                url,
                allow_redirects=True,
            ) as response:

                await response.read()

                latency = (
                    time.perf_counter()
                    - started
                )

                results.append(
                    Result(
                        status=response.status,
                        latency=latency,
                    )
                )

                logging.debug(
                    "worker=%d status=%d "
                    "latency=%.3fs",
                    worker_id,
                    response.status,
                    latency,
                )

        except asyncio.TimeoutError:

            results.append(
                Result(
                    status=None,
                    latency=(
                        time.perf_counter()
                        - started
                    ),
                    error="timeout",
                )
            )

        except aiohttp.ClientError as exc:

            results.append(
                Result(
                    status=None,
                    latency=(
                        time.perf_counter()
                        - started
                    ),
                    error=str(exc),
                )
            )

        await asyncio.sleep(interval)


async def progress_monitor(
    results: list[Result],
    stop_event: asyncio.Event,
    start_time: float,
) -> None:

    previous_count = 0

    while not stop_event.is_set():

        await asyncio.sleep(
            PROGRESS_INTERVAL
        )

        current = len(results)

        if current == previous_count:
            continue

        elapsed = (
            time.monotonic()
            - start_time
        )

        metrics = calculate_metrics(
            results,
            elapsed,
        )

        print(
            f"\r"
            f"Requests={metrics['requests']} | "
            f"RPS={metrics['rps']:.2f} | "
            f"p95={metrics['p95']:.3f}s | "
            f"p99={metrics['p99']:.3f}s | "
            f"Errors={metrics['error_rate'] * 100:.1f}%",
            end="",
            flush=True,
        )

        previous_count = current


async def run_stage(
    session: aiohttp.ClientSession,
    url: str,
    duration: int,
    concurrency: int,
    rps: float,
) -> tuple[list[Result], float, str | None]:

    results: list[Result] = []

    stop_event = asyncio.Event()

    start_time = time.monotonic()

    end_time = (
        start_time + duration
    )

    # Spread the configured request rate
    # across workers.
    interval = (
        concurrency / rps
    )

    workers = [
        asyncio.create_task(
            worker(
                session=session,
                url=url,
                end_time=end_time,
                interval=interval,
                results=results,
                stop_event=stop_event,
                worker_id=index,
            )
        )
        for index in range(concurrency)
    ]

    monitor = asyncio.create_task(
        progress_monitor(
            results,
            stop_event,
            start_time,
        )
    )

    reason = None

    try:
        while (
            time.monotonic() < end_time
            and not stop_event.is_set()
        ):

            reason = degradation_reason(
                results
            )

            if reason:
                stop_event.set()
                break

            await asyncio.sleep(0.25)

    finally:
        stop_event.set()

        await asyncio.gather(
            *workers,
            return_exceptions=True,
        )

        monitor.cancel()

        try:
            await monitor
        except asyncio.CancelledError:
            pass

    elapsed = (
        time.monotonic()
        - start_time
    )

    print()

    return results, elapsed, reason


def print_stage_report(
    stage: int,
    target_rps: float,
    results: list[Result],
    elapsed: float,
) -> None:

    metrics = calculate_metrics(
        results,
        elapsed,
    )

    statuses = Counter(
        result.status
        for result in results
        if result.status is not None
    )

    successful = sum(
        result.status is not None
        and 200 <= result.status < 400
        for result in results
    )

    print()
    print("=" * 64)
    print(f"STAGE {stage}")
    print("=" * 64)

    print(
        f"Target RPS       : "
        f"{target_rps:.2f}"
    )

    print(
        f"Actual RPS       : "
        f"{metrics['rps']:.2f}"
    )

    print(
        f"Requests         : "
        f"{metrics['requests']}"
    )

    print(
        f"Successful       : "
        f"{successful}"
    )

    print(
        f"p50 latency      : "
        f"{metrics['p50']:.3f}s"
    )

    print(
        f"p95 latency      : "
        f"{metrics['p95']:.3f}s"
    )

    print(
        f"p99 latency      : "
        f"{metrics['p99']:.3f}s"
    )

    print(
        f"Error rate       : "
        f"{metrics['error_rate'] * 100:.1f}%"
    )

    print(
        f"429 rate         : "
        f"{metrics['429_rate'] * 100:.1f}%"
    )

    print(
        f"5xx rate         : "
        f"{metrics['5xx_rate'] * 100:.1f}%"
    )

    print(
        f"Timeout rate     : "
        f"{metrics['timeout_rate'] * 100:.1f}%"
    )

    print("\nHTTP status codes:")

    if statuses:
        for status, count in sorted(
            statuses.items()
        ):
            print(
                f"  {status}: {count}"
            )
    else:
        print("  None")


def parse_ramp(
    value: str,
) -> list[float]:

    try:
        stages = [
            float(item.strip())
            for item in value.split(",")
            if item.strip()
        ]
    except ValueError as exc:
        raise SystemExit(
            "Invalid --ramp. "
            "Example: 10,25,50,100"
        ) from exc

    if not stages:
        raise SystemExit(
            "Ramp cannot be empty."
        )

    for rps in stages:
        if not 0 < rps <= MAX_RPS:
            raise SystemExit(
                f"Every RPS value must be "
                f"between 0 and {MAX_RPS}."
            )

    return stages


def parse_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser(
        description=(
            "Controlled HTTP performance "
            "benchmark for systems you control."
        )
    )

    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
    )

    parser.add_argument(
        "--ramp",
        default=DEFAULT_RAMP,
        help="RPS stages, e.g. 10,25,50,100",
    )

    parser.add_argument(
        "--stage-duration",
        type=int,
        default=DEFAULT_STAGE_DURATION,
    )

    parser.add_argument(
        "--concurrency",
        type=int,
        default=DEFAULT_CONCURRENCY,
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
    )

    return parser.parse_args()


async def main_async(
    args: argparse.Namespace,
) -> None:

    connector = aiohttp.TCPConnector(
        limit=args.concurrency,
        limit_per_host=args.concurrency,
        ttl_dns_cache=300,
        enable_cleanup_closed=True,
    )

    timeout = aiohttp.ClientTimeout(
        total=DEFAULT_TIMEOUT,
    )

    headers = {
        "User-Agent": (
            "Authorized-Performance-Benchmark/3.0"
        )
    }

    async with aiohttp.ClientSession(
        connector=connector,
        timeout=timeout,
        headers=headers,
    ) as session:

        stages = parse_ramp(
            args.ramp
        )

        for index, rps in enumerate(
            stages,
            start=1,
        ):

            print(
                f"\nStarting stage {index}: "
                f"{rps:.1f} RPS"
            )

            results, elapsed, reason = (
                await run_stage(
                    session=session,
                    url=args.url,
                    duration=args.stage_duration,
                    concurrency=args.concurrency,
                    rps=rps,
                )
            )

            print_stage_report(
                stage=index,
                target_rps=rps,
                results=results,
                elapsed=elapsed,
            )

            if reason:
                print(
                    f"\nSTOPPING RAMP: {reason}"
                )
                break

            print(
                "\nStage completed."
            )


def main() -> None:

    args = parse_args()

    if args.stage_duration <= 0:
        raise SystemExit(
            "Stage duration must be greater than 0."
        )

    if not (
        1
        <= args.concurrency
        <= MAX_CONCURRENCY
    ):
        raise SystemExit(
            f"Concurrency must be between "
            f"1 and {MAX_CONCURRENCY}."
        )

    logging.basicConfig(
        level=(
            logging.DEBUG
            if args.verbose
            else logging.WARNING
        ),
        format=(
            "%(asctime)s "
            "%(levelname)s "
            "%(message)s"
        ),
    )

    print(
        "CONTROLLED PERFORMANCE BENCHMARK"
    )
    print(
        f"Target      : {args.url}"
    )
    print(
        f"Ramp        : {args.ramp}"
    )
    print(
        f"Stage time  : "
        f"{args.stage_duration}s"
    )
    print(
        f"Concurrency : "
        f"{args.concurrency}"
    )

    try:
        asyncio.run(
            main_async(args)
        )
    except KeyboardInterrupt:
        print(
            "\n\nBenchmark stopped by user."
        )


if __name__ == "__main__":
    main()
