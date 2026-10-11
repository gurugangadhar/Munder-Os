"""
Munder Difflin — Stanley's Video Compositor & Media Director
Uses the embedded, verified local FFmpeg 7.1 executable to composite
multi-scene image cards and neural voiceover into a crisp 1080x1920 MP4 video.
"""

import os
import subprocess
from typing import List, Dict, Any
from core.media.scriptwriter import VideoScene


try:
    import imageio_ffmpeg
    DEFAULT_FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    DEFAULT_FFMPEG = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "tools", "ffmpeg.exe"))


class CompositorAgent:
    """Stanley Hudson — Video Compositor & Media Director."""

    def __init__(self, output_dir: str, ffmpeg_path: str = None):
        self.output_dir = output_dir
        self.ffmpeg_path = ffmpeg_path or DEFAULT_FFMPEG
        os.makedirs(self.output_dir, exist_ok=True)

    def composite_short(self, image_paths: List[str], audio_path: str, scenes: List[VideoScene], output_filename: str = "munder_short_001.mp4") -> Dict[str, Any]:
        """Composites scene slides and audio into a vertical 1080x1920 MP4 video."""
        if not os.path.exists(self.ffmpeg_path):
            raise FileNotFoundError(f"FFmpeg executable not found at: {self.ffmpeg_path}")

        output_mp4 = os.path.join(self.output_dir, output_filename)
        concat_txt = os.path.join(self.output_dir, "concat.txt")

        # 1. Build FFmpeg concat manifest
        with open(concat_txt, "w", encoding="utf-8") as f:
            for img, scene in zip(image_paths, scenes):
                clean_path = img.replace("\\", "/")
                f.write(f"file '{clean_path}'\n")
                f.write(f"duration {scene.duration_est_sec}\n")
            # Repeat last file to satisfy FFmpeg concat demuxer convention
            clean_last = image_paths[-1].replace("\\", "/")
            f.write(f"file '{clean_last}'\n")

        # 2. Run FFmpeg command
        cmd = [
            self.ffmpeg_path,
            "-y",  # Overwrite
            "-f", "concat",
            "-safe", "0",
            "-i", concat_txt,
            "-i", audio_path,
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",  # Stop at end of audio
            "-movflags", "+faststart",
            output_mp4
        ]

        print(f"[Stanley] Running FFmpeg assembly to {output_mp4}...")
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            print(f"[ERROR] FFmpeg failed:\n{result.stderr}")
            return {
                "success": False,
                "error": result.stderr,
                "output_path": None
            }

        file_size_mb = os.path.getsize(output_mp4) / (1024 * 1024)
        print(f"[Stanley] Video rendered successfully! Size: {file_size_mb:.2f} MB")

        return {
            "success": True,
            "output_path": output_mp4,
            "file_size_mb": file_size_mb,
            "format": "1080x1920 9:16 Vertical MP4",
            "qa_status": "PENDING_DWIGHT_APPROVAL"
        }
