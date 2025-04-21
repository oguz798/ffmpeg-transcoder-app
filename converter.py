import os
import threading
import subprocess
import re
import time
from tkinter import IntVar
from utils import run_ffprobe, build_track_description, get_video_stream_info, get_duration_seconds, \
    estimate_output_size, get_avg_bitrate_for_cq, parse_ffmpeg_progress


class FFmpegBatchProcessor:
    def __init__(self, gui):
        self.gui = gui
        self.stop_flag = threading.Event()
        self.current_process = None
        self.track_selections = {}  # Stores selections for each file

    def collect_all_track_selection(self):
        for file in self.gui.selected_files:
            audio_streams = run_ffprobe(file, "a")
            subtitle_streams = run_ffprobe(file, "s")

            audio_vars = [(IntVar(value=1), idx) for idx in self.gui.show_track_selection(audio_streams,
                                                                                          f"Select Audio Tracks for {os.path.basename(file)}")] if audio_streams else []
            subtitle_vars = [(IntVar(value=1), idx) for idx in self.gui.show_track_selection(subtitle_streams,
                                                                                        f"Select Subtitle Tracks for {os.path.basename(file)}")] if subtitle_streams else []

            self.track_selections[file] = {
                "audio": audio_vars,
                "subtitle": subtitle_vars
            }

    def get_selected_tracks(self, file):
        maps = [["-map", "0:v:0"]]  # Always include the first video stream

        for var, index in self.track_selections[file]["audio"]:
            if var.get():
                maps.append(["-map", f"0:{index}"])
        for var, index in self.track_selections[file]["subtitle"]:
            if var.get():
                maps.append(["-map", f"0:{index}"])

        return [item for sublist in maps for item in sublist]

    def determine_cq(self):
        preset = self.gui.quality_var.get().strip()
        if "4K" in preset:
            return "22"
        elif "1080p Movie" in preset:
            return "24"
        elif "1080p Series" in preset:
            return "25"
        elif "Anime" in preset:
            return "26"
        elif "Fast" in preset:
            return "30"
        return "24"

    def start_conversion(self):
        if not self.gui.selected_files or not self.gui.output_folder:
            self.gui.log("Please select files and output folder")
            return
        threading.Thread(target=self.run_batch, daemon=True).start()

    def run_batch(self):

        self.collect_all_track_selection()
        total_files = len(self.gui.selected_files)

        for index, file in enumerate(self.gui.selected_files):
            try:
                self.gui.progress_var.set(0)
                self.gui.progress_bar.update_idletasks()

                filename = os.path.basename(file)
                base, _ = os.path.splitext(filename)
                out_path = os.path.join(self.gui.output_folder, base + "_converted.mkv")

                duration = get_duration_seconds(file)
                video_info = get_video_stream_info(file)
                width = video_info.get('width', '?')
                height = video_info.get('height', '?')

                cq = self.determine_cq()
                bitrate = get_avg_bitrate_for_cq(cq)
                estimated_size = estimate_output_size(duration, bitrate)

                self.gui.log(f"\nFile: {filename}")
                self.gui.log(f"Resolution: {width}x{height}")
                self.gui.log(f"Duration: {int(duration)} seconds")
                self.gui.log(f"Estimated Output Size: {estimated_size} MB")

                maps = self.get_selected_tracks(file)
                cmd = ["ffmpeg", "-hwaccel", "cuda", "-i", file, "-pix_fmt", "yuv420p", "-c:v", "h264_nvenc", "-cq", cq,
                       "-preset", "medium"]
                for m in maps:
                    cmd.extend(m.split())
                cmd += ["-c:a", "copy", "-c:s", "copy", out_path]

                self.gui.log(f"\nRunning: {' '.join(cmd)}")
                start_time = time.time()
                self.current_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                                        text=True)
                for line in self.current_process.stdout:
                    self.gui.log(line.strip())
                    percent, eta_str = parse_ffmpeg_progress(line, duration)
                    if percent is not None:
                        self.gui.update_progress(percent, eta_str)

                retcode = self.current_process.wait()
                self.gui.log(f"conversion exited with code {retcode}")
                self.gui.update_progress((index + 1) / total_files * 100)
                self.gui.log(f"Done: {out_path}")

            except Exception as e:
                self.gui.log(f"Error processing {file}: {str(e)}")
                continue  # Move on to the next file
