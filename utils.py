import subprocess
import json
import re


def run_ffprobe(file, stream_type):
    """Run ffprobe on a file and return the parsed JSON output of all streams."""
    try:
        result = subprocess.run([
            "ffprobe", "-v", "error", f"-select_streams", stream_type,
            "-show_entries", "stream=index:stream_tags=language,title",
            "-of", "json", file
        ], capture_output=True, text=True)

        data = json.loads(result.stdout)

        streams = []
        if not data.get("streams"):
            print(f"[ffprobe] No streams found in: {file}")
            return []
        for stream in data.get("streams", []):
            index = stream.get("index")
            tags = stream.get("tags", {})
            lang = tags.get("language", "und")
            title = tags.get("title", "")
            display = f"Track {index} - {lang.upper()} - {title}"
            streams.append((index, display))

        return streams



    except Exception as e:
        print(f"[ffprobe error] {e}")
        return {"streams": []}


def build_track_description(stream):
    """Return a human-readable track description."""
    lang = stream.get('tags', {}).get('language', 'und')
    return f"{stream['codec_type']} #{stream['index']} ({lang})"


def get_video_stream_info(file):
    """Return first video stream info such as codec, width, height."""
    result = subprocess.run([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=codec_name,width,height",
        "-of", "json", file
    ], capture_output=True, text=True)
    return json.loads(result.stdout).get("streams", [{}])[0]


def estimate_output_size(duration_sec, bitrate_kbps):
    """Estimate output file size in MB given duration and bitrate."""
    return round((duration_sec * bitrate_kbps) / 8 / 1024, 2)


def get_duration_seconds(file):
    """Get video duration in seconds using ffprobe."""
    result = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", file
    ], capture_output=True, text=True)
    return float(result.stdout.strip())


def get_avg_bitrate_for_cq( cq):
    cq_map = {
        "22": 14000,
        "24": 10000,
        "25": 8500,
        "26": 7000,
        "30": 5000
    }
    return cq_map.get(cq, 10000)  # default fallback


def parse_ffmpeg_progress(line, duration):
    time_match = re.search(r'time=(\d+):(\d+):(\d+\.?\d*)', line)
    if not time_match or duration <= 0:
        return None, None

    h, m, s = map(float, time_match.groups())
    current_time = h * 3600 + m * 60 + s
    percent = (current_time / duration) * 100
    eta_sec = max(duration - current_time, 0)
    eta_str = f"{int(eta_sec // 60)}m {int(eta_sec % 60)}s"
    return percent, eta_str
