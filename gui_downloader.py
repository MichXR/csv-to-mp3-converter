import csv
import os
import subprocess
import sys
import re
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext


def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()


class DownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pobieracz MP3 z CSV (yt-dlp + ffmpeg)")
        self.root.geometry("650x550")
        self.root.minsize(600, 500)

        self.csv_path = ""
        self.is_downloading = False

        self.create_widgets()

    def create_widgets(self):
        # Sekcja wyboru CSV
        frame_csv = tk.LabelFrame(self.root, text=" Plik CSV z playlistą ", padx=10, pady=10)
        frame_csv.pack(fill="x", padx=15, pady=10)

        self.lbl_csv = tk.Label(frame_csv, text="Nie wybrano pliku", fg="gray", anchor="w")
        self.lbl_csv.pack(side="left", fill="x", expand=True, padx=(0, 10))

        btn_browse = tk.Button(frame_csv, text="Wybierz CSV...", command=self.browse_csv, width=15)
        btn_browse.pack(side="right")

        # Sekcja folderu docelowego
        frame_folder = tk.LabelFrame(self.root, text=" Folder docelowy na pliki MP3 ", padx=10, pady=10)
        frame_folder.pack(fill="x", padx=15, pady=5)

        self.entry_folder = tk.Entry(frame_folder)
        self.entry_folder.insert(0, "pobrane_mp3")
        self.entry_folder.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # Sekcja logów / konsoli
        frame_logs = tk.LabelFrame(self.root, text=" Status pobierania ", padx=10, pady=10)
        frame_logs.pack(fill="both", expand=True, padx=15, pady=10)

        self.log_area = scrolledtext.ScrolledText(frame_logs, wrap="word", state="disabled", bg="#1e1e1e", fg="#00ff00",
                                                  font=("Consolas", 9))
        self.log_area.pack(fill="both", expand=True)

        # Przycisk startu
        self.btn_start = tk.Button(self.root, text="Rozpocznij pobieranie", command=self.start_download_thread,
                                   bg="#4CAF50", fg="white", font=("Arial", 11, "bold"), height=2)
        self.btn_start.pack(fill="x", padx=15, pady=15)

    def browse_csv(self):
        filename = filedialog.askopenfilename(
            title="Wybierz plik CSV",
            filetypes=[("Pliki CSV", "*.csv"), ("Wszystkie pliki", "*.*")]
        )
        if filename:
            self.csv_path = filename
            self.lbl_csv.config(text=filename, fg="black")

    def log(self, message):
        self.log_area.config(state="normal")
        self.log_area.insert("end", message + "\n")
        self.log_area.see("end")
        self.log_area.config(state="disabled")

    def start_download_thread(self):
        if self.is_downloading:
            return

        if not self.csv_path or not os.path.exists(self.csv_path):
            messagebox.showerror("Błąd", "Wybierz najpierw poprawny plik CSV!")
            return

        output_dir = self.entry_folder.get().strip()
        if not output_dir:
            output_dir = "pobrane_mp3"

        self.is_downloading = True
        self.btn_start.config(state="disabled", bg="gray")

        # Uruchamiamy proces w osobnym wątku, aby okno programu nie "zamarzało"
        threading.Thread(target=self.run_download, args=(self.csv_path, output_dir), daemon=True).start()

    def run_download(self, csv_file, output_dir):
        FFMPEG_PATH = r"E:\ffmpeg\ffmpeg-9.0.2-essentials_build\bin"

        if not os.path.exists(FFMPEG_PATH):
            self.log(f"[BŁĄD KRYTYCZNY] Nie znaleziono ffmpeg.exe w ścieżce: {FFMPEG_PATH}")
            self.reset_ui()
            return

        os.makedirs(output_dir, exist_ok=True)
        self.log(f"Rozpoczęto pobieranie do folderu: {output_dir}\n")

        try:
            with open(csv_file, mode="r", encoding="utf-8-sig") as file:
                reader = csv.DictReader(file)

                for row in reader:
                    track_name = row.get("Track name", "").strip()
                    artist_name = row.get("Artist name", "").strip()

                    if not track_name:
                        continue

                    query = f"{artist_name} - {track_name}" if artist_name else track_name
                    safe_query = sanitize_filename(query)

                    # Sprawdzenie, czy plik MP3 już istnieje
                    already_downloaded = False
                    if os.path.exists(output_dir):
                        for filename in os.listdir(output_dir):
                            if filename.endswith(".mp3") and (
                                    safe_query.lower() in filename.lower() or track_name.lower() in filename.lower()):
                                already_downloaded = True
                                break

                    if already_downloaded:
                        self.log(f"[Pominięto] Plik już istnieje: {query}")
                        continue

                    self.log(f"\n[Pobieranie] {query}")

                    command = [
                        sys.executable, "-m", "yt_dlp",
                        f"ytsearch1:{query}",
                        "-x",
                        "--audio-format", "mp3",
                        "--audio-quality", "0",
                        "--ffmpeg-location", FFMPEG_PATH,
                        "-o", os.path.join(output_dir, "%(title)s.%(ext)s"),
                        "--no-playlist"
                    ]

                    try:
                        result = subprocess.run(command, capture_output=True, text=True, check=True)
                        self.log(f"[Sukces] Pobrano: {query}")
                    except subprocess.CalledProcessError as e:
                        self.log(f"[Błąd] Nie udało się pobrać '{query}'.")

            self.log("\n=== Zakończono pobieranie playlisty! ===")
            messagebox.showinfo("Sukces", "Pobieranie playlisty zostało zakończone!")

        except Exception as ex:
            self.log(f"[Błąd ogólny] {ex}")

        self.reset_ui()

    def reset_ui(self):
        self.is_downloading = False
        self.btn_start.config(state="normal", bg="#4CAF50")


if __name__ == "__main__":
    root = tk.Tk()
    app = DownloaderApp(root)
    root.mainloop()