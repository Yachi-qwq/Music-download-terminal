import os
import pyfiglet
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError, ExtractorError

print(pyfiglet.figlet_format("Music Download"))
print("-" * 40)

try:
  # Setup download directory on desktop
  desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
  download_dir = os.path.join(desktop_path, "music downloads")
  os.makedirs(download_dir, exist_ok=True)

  inp = input("* Song name or URL: ").strip()

  if not inp:
    print("x Error: No input provided. Please enter a song name or URL.")
  else:
    print("v Searching and downloading... Please wait.\n")

    # Resolve search query or direct URL
    target = inp if inp.startswith("http") else f"ytsearch1:{inp}"

    # yt-dlp configuration
    options = {
        "format": "best",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "outtmpl": os.path.join(download_dir, "%(title)s.%(ext)s"),
        "extractor_args": {"youtube": {"player_client": ["mweb", "android"]}},
    }

    try:
      with YoutubeDL(options) as ydl:
        info = ydl.extract_info(target, download=True)
        if "entries" in info:
          info = info["entries"][0]

        filename = f"{info.get('title', 'audio')}.mp3"
        full_path = os.path.join(download_dir, filename)

      print("\n")
      print("v Downloaded successfully!")
      print(f"-> Saved in: {full_path}")

    except DownloadError as de:
      print(f"\nx Download failed: Check your connection or the URL/query.")
    except ExtractorError as ee:
      print(f"\nx Extraction error: Could not parse video information.")
    except Exception as e:
      print(f"\nx An unexpected error occurred during download: {e}")

except KeyboardInterrupt:
  print("\n\nx Operation cancelled by user.")
except Exception as e:
  print(f"\nx System error: {e}")

input("\n-> Press enter key to exit . . .")
