from benzie.inference.benchmark import process_resources, summarize


def test_proc_units_and_cpu_fields_with_spaces_in_process_name(monkeypatch):
    from pathlib import Path

    stat = "42 (name with ) spaces) " + " ".join(["S"] + ["0"] * 10 + ["20", "30"])
    monkeypatch.setattr(Path, "read_text", lambda path: "VmRSS:\t100 kB\nVmHWM:\t150 kB\n" if path.name == "status" else stat)
    monkeypatch.setattr("benzie.inference.benchmark.os.sysconf", lambda _: 100)
    assert process_resources(42) == {"rss_bytes": 102400, "peak_rss_bytes": 153600, "cpu_seconds": 0.5}


def test_summary_uses_median_latency_and_max_memory():
    runs = [
        {"load_seconds": load, "ttft_seconds": load / 2, "decode_tokens_per_second": speed, "peak_rss_bytes": peak}
        for load, speed, peak in [(1, 10, 100), (9, 50, 200), (2, 20, 150)]
    ]
    assert summarize(runs) == {
        "median_load_seconds": 2, "median_ttft_seconds": 1,
        "median_decode_tokens_per_second": 20, "max_peak_rss_bytes": 200,
    }
