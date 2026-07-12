import subprocess
from pathlib import Path


def audio_to_mp4(audio_path: Path, black_image_path: Path, output_path: Path) -> Path:
    """Mux an audio file with a static black image into an MP4, so Google Drive
    treats it as a video (required for its caption-track UI, which is video-only)."""
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(black_image_path),
        "-i", str(audio_path),
        "-c:v", "libx264", "-tune", "stillimage",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        str(output_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path
