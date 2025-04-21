import os
import json
from tkinter import Tk, Button, Label, filedialog, messagebox, ttk, StringVar, Text, Scrollbar, END, RIGHT, Y, BOTH, \
    Toplevel, Checkbutton, IntVar, Frame, HORIZONTAL
from converter import FFmpegBatchProcessor
from utils import run_ffprobe, build_track_description


class TranscodeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FFmpeg Batch Converter")
        self.root.geometry("1000x720")

        self.selected_files = []
        self.output_folder = ""
        self.audio_tracks = []
        self.subtitle_tracks = []
        self.audio_vars = []
        self.subtitle_vars = []

        self.quality_var = StringVar(value="1080p Movie")
        self.progress_var = IntVar(value=0)
        self.status_var = StringVar(value="Idle")

        self.processor = FFmpegBatchProcessor(self)

        self.init_gui()

    def init_gui(self):
        Button(self.root, text="Select Files", command=self.select_files).pack(pady=5)
        Button(self.root, text="Output Folder", command=self.select_output_folder).pack(pady=5)
        Button(self.root, text="Start Conversion", command=self.processor.start_conversion).pack(pady=5)

        ttk.Label(self.root, text="Quality Preset:").pack()
        ttk.Combobox(self.root, textvariable=self.quality_var, values=[
            "4K Movie", "1080p Movie", "1080p Series", "Anime", "Fast"
        ]).pack(pady=5)

        self.progress_bar = ttk.Progressbar(self.root, orient=HORIZONTAL, length=600, mode='determinate',
                                            variable=self.progress_var)
        self.progress_bar.pack(pady=10)

        self.status_label = Label(self.root, textvariable=self.status_var)
        self.status_label.pack(pady=5)

        log_frame = Frame(self.root)
        log_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)

        self.log_text = Text(log_frame, height=20, wrap='word')
        self.log_text.pack(side='left', fill=BOTH, expand=True)

        scrollbar = Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side='right', fill=Y)

        self.log_text.config(yscrollcommand=scrollbar.set)

    def log(self, message):
        self.log_text.insert(END, message + "\n")
        self.log_text.see(END)

    def update_progress(self, percent, eta=""):
        self.progress_var.set(int(percent))
        if eta:
            self.status_var.set(f"Progress: {percent:.1f}% | ETA: {eta}")
        else:
            self.status_var.set(f"Progress: {percent:.1f}%")
        self.progress_bar.update_idletasks()

    def select_files(self):
        files = filedialog.askopenfilenames(filetypes=[("Video files", "*.mp4 *.mkv *.avi")])
        if files:
            self.selected_files = list(files)
            self.log(f"Selected {len(files)} files.")

    def select_output_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder = folder
            self.log(f"Output folder: {folder}")

    def show_track_selection(self, streams, title):
        win = Toplevel(self.root)
        win.title(title)

        vars_and_indexes = []
        for index, label in streams:
            var = IntVar(value=1)
            Checkbutton(win, text=label, variable=var).pack(anchor='w')
            vars_and_indexes.append((var, index))

        def on_ok():
            selected = [index for var, index in vars_and_indexes if var.get()]
            win.destroy()
            win.selected_indexes = selected

        Button(win, text="OK", command=on_ok).pack(pady=10)
        self.root.wait_window(win)
        return getattr(win, 'selected_indexes', [])

