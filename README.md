# FFmpeg Batch Transcoder App

A desktop application for batch converting video files using FFmpeg with NVIDIA hardware acceleration. Built with Python and Tkinter.

## Features

- Batch convert multiple video files to H.264 using NVENC
- GUI interface for selecting files, output folder, and quality presets
- Customize audio and subtitle streams per file
- Estimated output size, duration, and real-time progress updates

## Requirements

- Python 3.9+
- FFmpeg installed and available in your system's PATH
- NVIDIA GPU with NVENC support
- Tkinter (included with Python)
- Git (for version control)

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ffmpeg-transcoder-app.git
   cd ffmpeg-transcoder-app
