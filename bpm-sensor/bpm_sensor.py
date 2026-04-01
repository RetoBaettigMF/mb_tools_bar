#!/usr/bin/env python3
"""
bpm-sensor - Detect BPM from an MP3 file using librosa.

Samples 3 evenly-distributed sections of the song, measures BPM for each,
and returns the median to avoid intro/outro distortions.
"""

import argparse
import json
import statistics
import sys
from pathlib import Path

try:
    import librosa
    import numpy as np
except ImportError as e:
    print(
        f"Error: required library missing ({e}). "
        "Run: pip install librosa numpy",
        file=sys.stderr,
    )
    sys.exit(1)

SAMPLE_RATE = 22050
DEFAULT_WINDOW_SECS = 30.0
SKIP_FRACTION = 0.10


def get_duration(mp3_path: Path) -> float:
    """Return duration of audio file in seconds."""
    return librosa.get_duration(path=str(mp3_path))


def measure_section_bpm(mp3_path: Path, start: float, duration: float) -> float:
    """Load a section and return its BPM using librosa beat tracking."""
    y, sr = librosa.load(
        str(mp3_path), sr=SAMPLE_RATE, mono=True, offset=start, duration=duration
    )
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    # beat_track returns an array in newer librosa versions
    bpm = float(np.atleast_1d(tempo)[0])
    if bpm <= 0:
        raise RuntimeError(f"Could not detect BPM for section at {start:.1f}s.")
    return bpm


def compute_section_windows(
    duration: float, n_sections: int, window_secs: float
) -> list[tuple[float, float]]:
    """Return list of (start, end) times for evenly-spaced windows."""
    skip_start = duration * SKIP_FRACTION
    skip_end = duration * (1.0 - SKIP_FRACTION)
    usable_span = skip_end - skip_start
    win = min(window_secs, usable_span / n_sections)

    windows = []
    for i in range(n_sections):
        if n_sections == 1:
            start = skip_start + (usable_span - win) / 2
        else:
            start = skip_start + i * (usable_span - win) / (n_sections - 1)
        windows.append((start, start + win))
    return windows


def detect_bpm(
    mp3_path: Path,
    n_sections: int = 3,
    window_secs: float = DEFAULT_WINDOW_SECS,
    verbose: bool = False,
) -> dict:
    """Detect BPM by sampling multiple sections. Returns result dict."""
    duration = get_duration(mp3_path)
    windows = compute_section_windows(duration, n_sections, window_secs)

    section_results = []
    errors = []

    for i, (start, end) in enumerate(windows):
        if verbose:
            mins_s, secs_s = divmod(int(start), 60)
            mins_e, secs_e = divmod(int(end), 60)
            print(
                f"  Analysing section {i + 1}: {mins_s}:{secs_s:02d} - {mins_e}:{secs_e:02d} ...",
                file=sys.stderr,
            )
        try:
            bpm = measure_section_bpm(mp3_path, start, end - start)
            section_results.append({"start": round(start, 1), "end": round(end, 1), "bpm": round(bpm, 1)})
        except RuntimeError as e:
            errors.append(str(e))
            if verbose:
                print(f"    Warning: {e}", file=sys.stderr)

    if not section_results:
        raise RuntimeError(
            f"BPM detection failed for all sections. Errors: {'; '.join(errors)}"
        )

    bpms = [s["bpm"] for s in section_results]
    median_bpm = round(statistics.median(bpms))

    return {
        "bpm": median_bpm,
        "sections": section_results,
        "file": mp3_path.name,
    }


def main():
    parser = argparse.ArgumentParser(
        prog="bpm-sensor",
        description="Detect BPM from an MP3 file by sampling multiple sections.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  bpm-sensor track.mp3
  bpm-sensor track.mp3 --verbose
  bpm-sensor track.mp3 --json
  bpm-sensor track.mp3 --sections 5 --window 20
""",
    )
    parser.add_argument("mp3_file", help="Path to the MP3 file")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Print per-section BPM to stderr"
    )
    parser.add_argument(
        "--json", action="store_true", help="Output full JSON result"
    )
    parser.add_argument(
        "--sections",
        type=int,
        default=3,
        metavar="N",
        help="Number of sections to sample (default: 3)",
    )
    parser.add_argument(
        "--window",
        type=float,
        default=DEFAULT_WINDOW_SECS,
        metavar="SECS",
        help="Window length per section in seconds (default: 30)",
    )

    args = parser.parse_args()

    mp3_path = Path(args.mp3_file)
    if not mp3_path.is_file():
        print(f"Error: '{mp3_path}' not found.", file=sys.stderr)
        sys.exit(1)

    try:
        result = detect_bpm(mp3_path, args.sections, args.window, args.verbose)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        if args.verbose:
            for s in result["sections"]:
                mins_s, secs_s = divmod(int(s["start"]), 60)
                mins_e, secs_e = divmod(int(s["end"]), 60)
                print(
                    f"  {mins_s}:{secs_s:02d} - {mins_e}:{secs_e:02d}: {s['bpm']} BPM",
                    file=sys.stderr,
                )
            print(f"Median: {result['bpm']} BPM", file=sys.stderr)
        print(result["bpm"])

    sys.exit(0)


if __name__ == "__main__":
    main()
