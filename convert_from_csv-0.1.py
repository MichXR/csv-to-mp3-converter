import csv
import os
import subprocess
import sys

CSV_FILE = "playlista.csv"
OUTPUT_DIR = "pobrane_mp3"

# ŚCIEŻKA DO FOLDERU FFMPEG
FFMPEG_DIR = r"E:\ffmpeg\ffmpeg-9.0.2-essentials_build\bin"


def main():
    if not os.path.exists(CSV_FILE):
        print(f"Błąd: Nie znaleziono pliku {CSV_FILE}.")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(CSV_FILE, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            track_name = row.get("Track name", "").strip()
            artist_name = row.get("Artist name", "").strip()

            if not track_name:
                continue

            query = f"{artist_name} - {track_name}" if artist_name else track_name
            print(f"\n[Pobieranie] Rozpoczynam: {query}")

            command = [
                sys.executable, "-m", "yt_dlp",
                f"ytsearch1:{query}",
                "-x",
                "--audio-format", "mp3",
                "--audio-quality", "0",
                "--ffmpeg-location", FFMPEG_DIR,  # Jawne wskazanie lokalizacji FFmpeg
                "-o", os.path.join(OUTPUT_DIR, "%(title)s.%(ext)s"),
                "--no-playlist"
            ]

            try:
                subprocess.run(command, check=True)
                print(f"[Sukces] Pobrano: {query}")
            except subprocess.CalledProcessError as e:
                print(f"[Błąd] Nie udało się pobrać '{query}': {e}")

    print("\nZakończono pobieranie playlisty!")


if __name__ == "__main__":
    main()
