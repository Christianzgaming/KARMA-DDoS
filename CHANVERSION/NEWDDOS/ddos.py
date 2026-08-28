#!/usr/bin/env python3

import argparse
import asyncio
import logging
import statistics
import time
from dataclasses import dataclass

import aiohttp


DEFAULT_URL = "https://christianzgaming.github.io/website/"
DEFAULT_DURATION = 60
DEFAULT_CONCURRENCY = 5
DEFAULT_DELAY = 1.0


@dataclass
class Result:
    status: int | None
    latency: float
    error: str | None = None


async def worker(
    session: aiohttp.ClientSession,
    url: str,
    end_time: float,
    delay: float,
    results: list[Result],
    worker_id: int,
) -> None:
    while time.monotonic() < end_time:
        started = time.perf_counter()

        try:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=15),
                allow_redirects=True,
            ) as response:
                await response.read()
                latency = time.perf_counter() - started

                results.append(
                    Result(
                        status=response.status,
                        latency=latency,
                    )
                )

                logging.info(
                    "worker=%d status=%d latency=%.3fs",
                    worker_id,
                    response.status,
                    latency,
                )

        except asyncio.TimeoutError:
            results.append(
                Result(
                    status=None,
                    latency=time.perf_counter() - started,
                    error="timeout",
                )
            )
            logging.warning("worker=%d timeout", worker_id)

        except aiohttp.ClientError as exc:
            results.append(
                Result(
                    status=None,
                    latency=time.perf_counter() - started,
                    error=str(exc),
                )
            )
            logging.warning("worker=%d error=%s", worker_id, exc)

        await asyncio.sleep(delay)


async def run_test(
    url: str,
    duration: int,
    concurrency: int,
    delay: float,
) -> list[Result]:

    results: list[Result] = []

    connector = aiohttp.TCPConnector(
        limit=concurrency,
        limit_per_host=concurrency,
    )

    headers = {
        "User-Agent": "PersonalSite-HealthTest/1.0"
    }

    async with aiohttp.ClientSession(
        connector=connector,
        headers=headers,
    ) as session:

        end_time = time.monotonic() + duration

        workers = [
            asyncio.create_task(
                worker(
                    session,
                    url,
                    end_time,
                    delay,
                    results,
                    worker_id,
                )
            )
            for worker_id in range(concurrency)
        ]

        await asyncio.gather(*workers)

    return results


def print_report(results: list[Result], duration: int) -> None:
    if not results:
        print("\nNo requests completed.")
        return

    successful = [
        r for r in results
        if r.status is not None and 200 <= r.status < 400
    ]

    failed = [
        r for r in results
        if r.status is None or r.status >= 400
    ]

    latencies = [r.latency for r in results]

    print("\n" + "=" * 50)
    print("LOAD TEST REPORT")
    print("=" * 50)

    print(f"Requests completed : {len(results)}")
    print(f"Successful         : {len(successful)}")
    print(f"Failed             : {len(failed)}")
    print(f"Average RPS        : {len(results) / duration:.2f}")
    print(f"Average latency    : {statistics.mean(latencies):.3f}s")
    print(f"Minimum latency    : {min(latencies):.3f}s")
    print(f"Maximum latency    : {max(latencies):.3f}s")

    if len(latencies) >= 2:
        print(
            f"Median latency     : "
            f"{statistics.median(latencies):.3f}s"
        )

    status_counts = {}

    for result in results:
        if result.status is not None:
            status_counts[result.status] = (
                status_counts.get(result.status, 0) + 1
            )

    print("\nHTTP status codes:")

    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")

    print("=" * 50)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Controlled HTTP health/load tester."
    )

    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help="Target URL",
    )

    parser.add_argument(
        "--duration",
        type=int,
        default=DEFAULT_DURATION,
        help="Test duration in seconds",
    )

    parser.add_argument(
        "--concurrency",
        type=int,
        default=DEFAULT_CONCURRENCY,
        help="Number of concurrent workers",
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_DELAY,
        help="Delay between requests per worker",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable request logging",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.duration <= 0:
        raise SystemExit("Duration must be greater than 0.")

    if not 1 <= args.concurrency <= 9999999:
        raise SystemExit(
            "Concurrency must be between 1 and 9999999."
        )

    if args.delay < 0.5:
        raise SystemExit(
            "Delay must be at least 0.5 seconds."
        )

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    print(f"Target      : {args.url}")
    print(f"Duration    : {args.duration}s")
    print(f"Concurrency : {args.concurrency}")
    print(f"Delay       : {args.delay}s")
    print("\nStarting controlled test...")

    started = time.monotonic()

    results = asyncio.run(
        run_test(
            args.url,
            args.duration,
            args.concurrency,
            args.delay,
        )
    )

    elapsed = time.monotonic() - started

    print_report(results, max(1, int(elapsed)))


if __name__ == "__main__":
    main()
