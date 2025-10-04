#!/usr/bin/env python3
"""
Minimal Veeam net-perf parser (file or folder)
- validate: show matching lines (quick check)
- scan: parse and write CSV (events)
* Auto-names output as <logs_folder_or_file_name>.csv in the script folder if --out is omitted.
"""
from __future__ import annotations
import argparse, csv, re
from pathlib import Path
from typing import Iterable, Iterator, Optional, Tuple, List, Dict

# ---- timestamp ----
TS = re.compile(r"^(?P<ts>[0-9:.\-\s]{19,26})\s+")
def parse_ts_prefix(line: str) -> Tuple[Optional[str], str]:
    m = TS.match(line)
    if not m: return None, line
    return m.group("ts"), line[m.end():]

def parse_size(text: str) -> Optional[int]:
    mult = {"KB":2**10,"MB":2**20,"GB":2**30,"TB":2**40}
    try:
        num, unit = text.strip().split()
        return int(float(num)*mult[unit.upper()])
    except Exception:
        return None

def parse_dur(hms: str) -> int:
    h,m,s = [int(x) for x in hms.split(":")]
    return h*3600 + m*60 + s

# ---- patterns ----
BOTTLE = re.compile(r"Bottleneck:\s*Network:\s*(?P<pct>\d{1,3})%", re.I)
XFER   = re.compile(r"Transfer(?:red)?:\s*(?P<bytes>[\d.]+\s*(?:KB|MB|GB|TB)).*?Duration:\s*(?P<dur>\d{2}:\d{2}:\d{2}).*?Avg speed:\s*(?P<spd>[\d.]+\s*(?:KB|MB|GB)/s)", re.I)
WAN    = re.compile(r"WAN Accelerator.*?(?:hit|cache hit)[:=]?\s*(?P<hit>\d{1,3})%", re.I)
RETRY  = re.compile(r"\b(?:retry|retries)\s*[:=]?\s*(?P<retries>\d+)\b", re.I)

# ---- file/dir reader ----
def yield_lines(path: Path) -> Iterator[str]:
    if path.is_dir():
        for f in path.rglob("*.log"):
            try:
                with f.open("r", encoding="utf-8", errors="ignore") as fh:
                    for line in fh:
                        yield line.rstrip("\n")
            except Exception:
                continue
    else:
        with path.open("r", encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                yield line.rstrip("\n")

# ---- parsing ----
def parse_events(lines: Iterable[str]) -> List[Dict[str, object]]:
    out = []
    for raw in lines:
        ts_text, msg = parse_ts_prefix(raw)
        row = {
            "event_time": ts_text,
            "bytes_sent": None,
            "duration_s": None,
            "network_bottleneck_pct": None,
            "wan_cache_hit_pct": None,
            "retries": None,
            "message": msg,
        }
        hit = False
        m = BOTTLE.search(msg)
        if m:
            row["network_bottleneck_pct"] = int(m["pct"]); hit = True
        m = XFER.search(msg)
        if m:
            row["bytes_sent"] = parse_size(m["bytes"])
            row["duration_s"] = parse_dur(m["dur"])
            hit = True
        m = WAN.search(msg)
        if m:
            row["wan_cache_hit_pct"] = int(m["hit"]); hit = True
        m = RETRY.search(msg)
        if m:
            row["retries"] = int(m["retries"]); hit = True
        if hit:
            out.append(row)
    return out

def write_csv(rows: List[Dict[str, object]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    headers = ["event_time","bytes_sent","duration_s","network_bottleneck_pct","wan_cache_hit_pct","retries","message"]
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for r in rows:
            w.writerow(r)

# ---- CLI ----
def main():
    ap = argparse.ArgumentParser(description="Veeam network metrics parser (file or folder)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("validate")
    v.add_argument("--input", required=True)
    v.add_argument("--limit", type=int, default=40)

    s = sub.add_parser("scan")
    s.add_argument("--input", required=True)
    # --out is now optional; when omitted we auto-name the CSV in the script folder
    s.add_argument("--out", required=False)

    args = ap.parse_args()
    p = Path(args.input)

    if args.cmd == "validate":
        shown = 0
        for line in yield_lines(p):
            _, msg = parse_ts_prefix(line)
            if any([BOTTLE.search(msg), XFER.search(msg), WAN.search(msg), RETRY.search(msg)]):
                print(line); shown += 1
                if shown >= args.limit:
                    break
        if shown == 0:
            print("No recognizable lines found. Share a few sample lines to tune the patterns.")
    else:
        rows = parse_events(yield_lines(p))
        # --- smart output name: <input_base>.csv in the script's folder if --out missing
        script_dir = Path(__file__).parent
        input_base = p.stem if p.is_file() else p.name  # file without ext OR last folder name
        auto_out = script_dir / f"{input_base}.csv"
        out_path = Path(args.out) if args.out else auto_out

        write_csv(rows, out_path)
        print(f"✅ Done. {len(rows)} events written to {out_path}")

if __name__ == "__main__":
    main()

