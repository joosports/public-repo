# Tse Long Tin — Highlight Reel Build Notes

**Output:** `output/tse-long-tin-highlights.mp4` (1080p, 30 fps, H.264/AAC, ~1:57, ~71 MB)

## Structure

| # | Time (approx) | Source clip | Content | Caption |
|---|---|---|---|---|
| title | 0:00–0:04 | generated | Name card (TSE LONG TIN 謝朗天, position/teams/stats) | — |
| seg01 | 0:04 | 537996ac… (8.1s) | Kitchee vs Lee Man, broadcast | KITCHEE \| LEE MAN |
| seg02 | 0:12 | 67d7cdc5… (11.8s) | Kitchee vs Lee Man, broadcast | KITCHEE \| LEE MAN |
| seg03 | 0:24 | ecab4e33… (7.3s) | Kitchee vs Lee Man, broadcast | KITCHEE \| LEE MAN |
| seg04 | 0:31 | fe6bbde6… (3.4s) | Kitchee vs Lee Man, broadcast | KITCHEE \| LEE MAN |
| seg05 | 0:35 | 84012059… (6.7s→5.5s) | HK Elite vs PVF, **#4 identified** | HONG KONG ELITE \| PVF — PHOENIX CUP 2026 |
| seg06 | 0:40 | c6a11c59… (6s→5s) | HK Elite vs PVF, press/duel | HONG KONG ELITE \| PVF — PHOENIX CUP 2026 |
| seg07 | 0:45 | f585178c… (8s→4.9s) | HK Elite vs Chengdu, box defence | HONG KONG ELITE \| CHENGDU — PHOENIX CUP 2026 |
| seg08 | 0:50 | 8f2bd7aa… (15.1s→14.6s) | Kitchee night match (blue), set-piece defence | KITCHEE \| NIGHT MATCH |
| seg09 | 1:05 | d862d1f… (20.1s→18s) | Kitchee night match, corners/box battles | KITCHEE \| NIGHT MATCH |
| seg10 | 1:23 | f04555ef… part 1 (→14s) | Kitchee match play, build-up | KITCHEE \| MATCH PLAY |
| seg11 | 1:37 | f04555ef… part 2 (22–38s) | Kitchee match play, attack phase | KITCHEE \| MATCH PLAY |
| outro | 1:53–1:57 | generated | Name card + joosports.github.io | — |

Clips 11–16 (other youth/futsal footage) were **excluded** per instruction: only matches confirmed to feature Long Tin.

## Identification method

- Kitchee #28/#79 (fallback: tallest in the back line), HK Elite #4, HK red #12 (fallback: tallest).
- Jersey numbers are only legible at broadcast close-ups; in the wide coach-cam clips identification relies on position/height — flag those segments (seg08–seg11) as position-based, not number-confirmed.
- **#4 was clearly confirmed** on video in the HK Elite vs PVF clip (seg05, jersey readable on back).

## Reproduce

- ffmpeg 9.0.2 (Gyan full build, installed via winget).
- Temp build scripts: `%TEMP%\opencode\build-longtin.ps1`, `finish-longtin.ps1`, `final-concat-longtin.ps1`.
- Per-segment normalize: `scale=1920:1080:force_original_aspect_ratio=decrease,pad,setsar=1,fps=30`, libx264 CRF 20, AAC 192k.
- Final assembly uses the concat *filter* (not concat demuxer) because several source clips have non-monotonic timestamps that corrupt stream-copy concatenation.
