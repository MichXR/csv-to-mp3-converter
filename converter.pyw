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
        self.root.title("CSV to MP3 Downloader (yt-dlp + ffmpeg)")
        self.root.geometry("680x660")
        self.root.minsize(620, 580)

        self.csv_path = ""
        self.is_downloading = False
        self.current_process = None

        self.create_widgets()

    def create_widgets(self):
        # CSV selection section
        frame_csv = tk.LabelFrame(self.root, text=" Playlist CSV File ", padx=10, pady=10)
        frame_csv.pack(fill="x", padx=15, pady=10)

        self.lbl_csv = tk.Label(frame_csv, text="No file selected", fg="gray", anchor="w")
        self.lbl_csv.pack(side="left", fill="x", expand=True, padx=(0, 10))

        btn_browse_csv = tk.Button(frame_csv, text="Browse CSV...", command=self.browse_csv, width=15)
        btn_browse_csv.pack(side="right")

        # Output folder section
        frame_folder = tk.LabelFrame(self.root, text=" Output MP3 Folder ", padx=10, pady=10)
        frame_folder.pack(fill="x", padx=15, pady=5)

        self.entry_folder = tk.Entry(frame_folder)
        default_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloaded_mp3")
        self.entry_folder.insert(0, default_dir)
        self.entry_folder.pack(side="left", fill="x", expand=True, padx=(0, 10))

        btn_browse_folder = tk.Button(frame_folder, text="Browse Folder...", command=self.browse_folder, width=15)
        btn_browse_folder.pack(side="right")

        # Control buttons panel (Start / Stop)
        frame_buttons = tk.Frame(self.root)
        frame_buttons.pack(fill="x", padx=15, pady=10)

        self.btn_start = tk.Button(frame_buttons, text="Start Download", command=self.start_download_thread,
                                   bg="#4CAF50", fg="white", font=("Arial", 11, "bold"), height=2)
        self.btn_start.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.btn_stop = tk.Button(frame_buttons, text="Stop", command=self.stop_download, bg="#f44336", fg="white",
                                  font=("Arial", 11, "bold"), height=2, state="disabled")
        self.btn_stop.pack(side="right", fill="x", expand=True, padx=(5, 0))

        # Logs / console section
        frame_logs = tk.LabelFrame(self.root, text=" Download Status ", padx=10, pady=10)
        frame_logs.pack(fill="both", expand=True, padx=15, pady=10)

        self.log_area = scrolledtext.ScrolledText(frame_logs, wrap="word", state="disabled", bg="#1e1e1e", fg="#00ff00",
                                                  font=("Consolas", 9))
        self.log_area.pack(fill="both", expand=True)

    def browse_csv(self):
        filename = filedialog.askopenfilename(
            title="Select CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.csv_path = filename
            self.lbl_csv.config(text=filename, fg="black")

    def browse_folder(self):
        folder = filedialog.askdirectory(title="Select output folder")
        if folder:
            self.entry_folder.delete(0, tk.END)
            self.entry_folder.insert(0, folder)

    def log(self, message):
        self.log_area.config(state="normal")
        self.log_area.insert("end", message + "\n")
        self.log_area.see("end")
        self.log_area.config(state="disabled")

    def start_download_thread(self):
        if self.is_downloading:
            return

        if not self.csv_path or not os.path.exists(self.csv_path):
            messagebox.showerror("Error", "Please select a valid CSV file first!")
            return

        output_dir = self.entry_folder.get().strip()
        if not output_dir:
            messagebox.showerror("Error", "Output folder path cannot be empty!")
            return

        self.is_downloading = True
        self.btn_start.config(state="disabled", bg="gray")
        self.btn_stop.config(state="normal")

        # Run process in a separate thread to keep GUI responsive
        threading.Thread(target=self.run_download, args=(self.csv_path, output_dir), daemon=True).start()

    def stop_download(self):
        if self.is_downloading:
            self.is_downloading = False
            self.log("\n[Notice] Stop requested... Aborting after current track.")

            if self.current_process:
                try:
                    self.current_process.terminate()
                except Exception:
                    pass

    def run_download(self, csv_file, output_dir):
        FFMPEG_PATH = r"C:\ffmpeg\bin\ffmpeg.exe"

        if not os.path.exists(FFMPEG_PATH):
            self.log(f"[CRITICAL ERROR] ffmpeg.exe not found at path: {FFMPEG_PATH}")
            self.reset_ui()
            return

        if not os.path.isabs(output_dir):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            output_dir = os.path.join(script_dir, output_dir)

        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as ex:
            self.log(f"[ERROR] Cannot create folder '{output_dir}': {ex}")
            self.reset_ui()
            return

        self.log(f"Started downloading to folder: {output_dir}\n")

        try:
            with open(csv_file, mode="r", encoding="utf-8-sig") as file:
                reader = csv.DictReader(file)

                for row in reader:
                    if not self.is_downloading:
                        break

                    track_name = row.get("Track name", "").strip()
                    artist_name = row.get("Artist name", "").strip()

                    if not track_name:
                        continue

                    query = f"{artist_name} - {track_name}" if artist_name else track_name
                    safe_query = sanitize_filename(query)

                    # Check if MP3 file already exists
                    already_downloaded = False
                    if os.path.exists(output_dir):
                        for filename in os.listdir(output_dir):
                            if filename.endswith(".mp3") and (
                                    safe_query.lower() in filename.lower() or track_name.lower() in filename.lower()):
                                already_downloaded = True
                                break

                    if already_downloaded:
                        self.log(f"[Skipped] File already exists: {query}")
                        continue

                    self.log(f"\n[Downloading] {query}")

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
                        self.current_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                                                text=True)
                        stdout, stderr = self.current_process.communicate()

                        if self.current_process.returncode == 0:
                            self.log(f"[Success] Downloaded: {query}")
                        else:
                            if self.is_downloading:
                                self.log(f"[Error] Failed to download '{query}'.")
                    except Exception as e:
                        if self.is_downloading:
                            self.log(f"[Error] An issue occurred: {e}")
                    finally:
                        self.current_process = None

            if not self.is_downloading:
                self.log("\n=== Download stopped by user. ===")
            else:
                self.log("\n=== Playlist download finished successfully! ===")
                messagebox.showinfo("Success", "Playlist download has been completed!")

        except Exception as ex:
            self.log(f"[General Error] {ex}")

        self.reset_ui()

    def reset_ui(self):
        self.is_downloading = False
        self.current_process = None
        self.btn_start.config(state="normal", bg="#4CAF50")
        self.btn_stop.config(state="disabled")


if __name__ == "__main__":
    root = tk.Tk()
    app = DownloaderApp(root)
    root.mainloop()