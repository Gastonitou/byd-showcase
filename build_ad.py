#!/usr/bin/env python3
"""Build BYD compilation video - using filter script file."""
import subprocess, os, sys

DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(DIR, "BYD_All_Models_Compilation.mp4")

CLIPS = [
    ("Der neue BYD DOLPHIN - TV Spot.mp4", "BYD DOLPHIN", 29),
    ("BYD ATTO 3 - TVC 40s [BYD Brand Video].mp4", "BYD ATTO 3", 40),
    ("Der BYD ATTO 3 EVO 2026 - TV Spot.mp4", "BYD ATTO 3 EVO", 25),
    ("Anuncio BYD SEAL U DUAL MODE 2024.mp4", "BYD SEAL U", 20),
    ("All-new BYD Han L & BYD Tang L - official video.mp4", "BYD HAN L und TANG L", 63),
]

# Write concat file
concat_file = os.path.join(DIR, "concat_list.txt")
with open(concat_file, "w") as f:
    for clip, _, _ in CLIPS:
        abs_path = os.path.join(DIR, clip).replace("'", "'\\''")
        f.write(f"file '{abs_path}'\n")

# Calculate total duration
total_dur = sum(d for _, _, d in CLIPS)

# Build drawtext filter
dt_filters = []
start = 0.0
for _, label, dur in CLIPS:
    end = start + dur
    # Model label at bottom center
    dt_filters.append(
        f"drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
        f"text={label}:fontcolor=white:fontsize=36:"
        f"x=(w-text_w)/2:y=h-text_h-90:"
        f"shadowcolor=black@0.8:shadowx=3:shadowy=3:"
        f"enable=between(t\\,{start}\\,{end})"
    )
    # BYD brand top-left (show first 4s of each clip)
    dt_filters.append(
        f"drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
        f"text=BYD:fontcolor=0xE94560:fontsize=52:"
        f"x=60:y=40:"
        f"shadowcolor=black@0.8:shadowx=3:shadowy=3:"
        f"enable=between(t\\,{start}\\,{start+4})"
    )
    start = end

# Build the filter graph
dv_filters = ",\n  ".join(dt_filters)

filter_graph = f"""\
[0:v]fade=t=in:st=0:d=1,
  fade=t=out:st={total_dur-1}:d=1,
  {dv_filters}[v];

[0:a]afade=t=in:d=1,
  afade=t=out:st={total_dur-1}:d=1[a]
"""

# Write filter to file
filter_file = os.path.join(DIR, "filter.txt")
with open(filter_file, "w") as f:
    f.write(filter_graph)

print("=" * 60)
print("BYD ALL MODELS COMPILATION")
print("=" * 60)
for label, _, dur in CLIPS:
    print(f"  {label:30s} {dur}s")
print(f"\nTotal: ~{total_dur}s")
print(f"Output: {OUTPUT}")
print("=" * 60)
sys.stdout.flush()

cmd = [
    "ffmpeg", "-y",
    "-f", "concat", "-safe", "0",
    "-i", concat_file,
    "-filter_complex_script", filter_file,
    "-map", "[v]", "-map", "[a]",
    "-c:v", "libx264", "-preset", "medium", "-crf", "21",
    "-c:a", "aac", "-b:a", "192k",
    "-pix_fmt", "yuv420p",
    "-movflags", "+faststart",
    OUTPUT
]

result = subprocess.run(cmd, capture_output=True, text=True)

if result.returncode != 0:
    err = result.stderr[-3000:] if result.stderr else "Unknown"
    print("ERROR:", err)
    sys.exit(1)

size = os.path.getsize(OUTPUT)
print(f"\nDone! ({size/1024/1024:.1f} MB)")
print(f"Saved: {OUTPUT}")
