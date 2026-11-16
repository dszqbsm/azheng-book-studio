"""Shared duration wording for cover artwork and opening narration."""
import math


def runtime_label(seconds, title):
    if not math.isfinite(seconds) or seconds <= 0:
        raise ValueError("Duration must be finite and positive")
    minutes = max(10, 10 * (math.floor(seconds + 300) // 600))
    cover_line = f"{minutes}分钟听完一本书"
    return {
        "duration_seconds": seconds,
        "display_minutes": minutes,
        "cover_line": cover_line,
        "opening_line": f"{cover_line}，今天我们听《{title}》。",
    }
