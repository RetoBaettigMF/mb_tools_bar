#!/usr/bin/env python3
"""Download a YouTube video as an MP3 file."""

import sys
import yt_dlp


def download_as_mp3(url: str, output_dir: str = ".") -> None:
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{output_dir}/%(title)s.%(ext)s",
        "noplaylist": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


def main():
    if len(sys.argv) < 2:
        print("Usage: yt2mp3 <youtube-url> [output-dir]")
        sys.exit(1)

    url = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "."

    download_as_mp3(url, output_dir)


if __name__ == "__main__":
    main()
