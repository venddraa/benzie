"""Pengukuran Linux atas proses runtime milik Benzie, tanpa psutil."""

import os
from pathlib import Path
from statistics import median


def system_memory() -> dict:
    values = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith(("MemTotal:", "MemAvailable:", "SwapTotal:", "SwapFree:")):
            key, number, unit = line.split()
            values[key.rstrip(":")] = int(number) * 1024
    return values


def process_resources(pid: int) -> dict:
    status = (Path("/proc") / str(pid) / "status").read_text()
    values = {}
    for line in status.splitlines():
        if line.startswith(("VmRSS:", "VmHWM:")):
            key, number, unit = line.split()
            if unit != "kB":
                raise ValueError("Unit memori /proc tidak dikenali.")
            values[key.rstrip(":")] = int(number) * 1024
    stat = (Path("/proc") / str(pid) / "stat").read_text()
    fields = stat.rsplit(")", 1)[1].split()  # comm dapat mengandung spasi/kurung.
    cpu_seconds = (int(fields[11]) + int(fields[12])) / os.sysconf("SC_CLK_TCK")
    return {"rss_bytes": values["VmRSS"], "peak_rss_bytes": values["VmHWM"], "cpu_seconds": cpu_seconds}


def summarize(runs: list[dict]) -> dict:
    if not runs:
        raise ValueError("Tidak ada hasil benchmark.")
    return {
        "median_load_seconds": median(run["load_seconds"] for run in runs),
        "median_ttft_seconds": median(run["ttft_seconds"] for run in runs),
        "median_decode_tokens_per_second": median(run["decode_tokens_per_second"] for run in runs),
        "max_peak_rss_bytes": max(run["peak_rss_bytes"] for run in runs),
    }
