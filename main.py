import os
import re
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import pyfiglet
from yt_dlp import YoutubeDL
from spotify_scraper import SpotifyClient


class MusicDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Music Downloader & Playlist Scraper")
        self.root.geometry("900x720")
        self.root.minsize(750, 600)

        self.bg_color = "#f4f4f9"
        self.root.configure(bg=self.bg_color)
        
        style = ttk.Style()
        style.theme_use("clam")

        self.current_target_dir = "-"
        self.create_widgets()

    def create_widgets(self):
        banner_text = pyfiglet.figlet_format("Music Downloader", font="slant")
        self.banner_label = tk.Label(
            self.root, 
            text=banner_text, 
            font=("Consolas", 10, "bold"), 
            bg="#1e1e1e", 
            fg="#00ffcc",
            justify=tk.CENTER
        )
        self.banner_label.pack(fill=tk.X, padx=10, pady=10)

        input_frame = tk.Frame(self.root, bg=self.bg_color)
        input_frame.pack(fill=tk.X, padx=15, pady=5)

        lbl_input = tk.Label(input_frame, text="Song Name, Spotify or YouTube Link:", bg=self.bg_color, font=("Arial", 10, "bold"))
        lbl_input.pack(anchor=tk.W, pady=2)

        entry_frame = tk.Frame(input_frame, bg=self.bg_color)
        entry_frame.pack(fill=tk.X, expand=True)

        self.entry_inp = tk.Entry(entry_frame, font=("Arial", 11))
        self.entry_inp.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5), ipady=3)
        self.entry_inp.bind("<Return>", lambda event: self.start_download_thread())

        self.btn_download = tk.Button(entry_frame, text="Start Download", bg="#007acc", fg="white", font=("Arial", 10, "bold"), command=self.start_download_thread, padx=10)
        self.btn_download.pack(side=tk.RIGHT)

        list_frame = tk.Frame(self.root, bg=self.bg_color)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        lbl_list = tk.Label(list_frame, text="Download Queue & Status:", bg=self.bg_color, font=("Arial", 10, "bold"))
        lbl_list.pack(anchor=tk.W, pady=2)

        columns = ("nr", "song", "status", "progress")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="none")
        self.tree.heading("nr", text="No.")
        self.tree.heading("song", text="Title / Query")
        self.tree.heading("status", text="Status")
        self.tree.heading("progress", text="Progress Bar")
        
        self.tree.column("nr", width=40, anchor=tk.CENTER)
        self.tree.column("song", width=430, anchor=tk.W)
        self.tree.column("status", width=90, anchor=tk.CENTER)
        self.tree.column("progress", width=220, anchor=tk.W)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        footer_frame = tk.Frame(self.root, bg=self.bg_color)
        footer_frame.pack(fill=tk.X, padx=15, pady=10)

        self.btn_terminal = tk.Button(footer_frame, text="Open Terminal Output", bg="#444", fg="white", font=("Arial", 9), command=self.open_terminal_window)
        self.btn_terminal.pack(side=tk.LEFT)

        self.lbl_folder = tk.Label(footer_frame, text="Saved in: -", bg=self.bg_color, font=("Arial", 9, "underline"), fg="#0066cc", cursor="hand2")
        self.lbl_folder.pack(side=tk.RIGHT)
        self.lbl_folder.bind("<Button-1>", lambda e: self.open_folder_explorer())

    def open_folder_explorer(self):
        if self.current_target_dir != "-" and os.path.exists(self.current_target_dir):
            if sys.platform == "win32":
                os.startfile(self.current_target_dir)
            elif sys.platform == "darwin":
                subprocess.run(["open", self.current_target_dir])
            else:
                subprocess.run(["xdg-open", self.current_target_dir])
        else:
            messagebox.showwarning("Notice", "No valid folder has been created yet.")

    def open_terminal_window(self):
        term_win = tk.Toplevel(self.root)
        term_win.title("Terminal Output (Log)")
        term_win.geometry("700x400")

        self.term_text = scrolledtext.ScrolledText(term_win, wrap=tk.WORD, bg="#1e1e1e", fg="#00ffcc", font=("Consolas", 9))
        self.term_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.term_text.insert(tk.END, "--- Log output ready ---\n")
        self.term_text.see(tk.END)

    def log_to_terminal(self, message):
        print(message)
        if hasattr(self, 'term_text') and self.term_text.winfo_exists():
            self.term_text.insert(tk.END, message + "\n")
            self.term_text.see(tk.END)

    def clean_ansi(self, text):
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    def start_download_thread(self):
        inp = self.entry_inp.get().strip()
        if not inp:
            messagebox.showerror("Error", "Please enter a song name or link!")
            return

        self.btn_download.config(state=tk.DISABLED)
        self.tree.delete(*self.tree.get_children())
        
        threading.Thread(target=self.process_downloads, args=(inp,), daemon=True).start()

    def process_downloads(self, inp):
        try:
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            base_download_dir = os.path.join(desktop_path, "music downloads")
            os.makedirs(base_download_dir, exist_ok=True)
            target_dir = base_download_dir

            queries_to_download = []

            if "youtube.com" in inp or "youtu.be" in inp:
                self.log_to_terminal("[YouTube]: Link detected. Analyzing...")
                target_dir = os.path.join(base_download_dir, "YouTube Downloads")
                os.makedirs(target_dir, exist_ok=True)
                
                if "list=" in inp:
                    ydl_opts_extract = {'extract_flat': True, 'quiet': True}
                    try:
                        with YoutubeDL(ydl_opts_extract) as ydl:
                            info = ydl.extract_info(inp, download=False)
                            if 'entries' in info:
                                for entry in info['entries']:
                                    title = entry.get('title', 'Unknown Title')
                                    url = entry.get('url') or f"https://www.youtube.com/watch?v={entry.get('id')}"
                                    queries_to_download.append((title, url))
                            else:
                                queries_to_download.append((info.get('title', inp), inp))
                    except Exception:
                        queries_to_download.append((inp, inp))
                else:
                    queries_to_download.append((inp, inp))

            elif "spotify.com" in inp and "playlist" in inp:
                self.log_to_terminal("[SpotifyScraper]: Loading playlist data...")
                try:
                    with SpotifyClient() as client:
                        playlist = client.get_playlist(inp, max_tracks=500)
                        if not playlist or not playlist.tracks:
                            self.log_to_terminal("x Error: No songs found or playlist is private.")
                            self.btn_download.config(state=tk.NORMAL)
                            return
                        
                        raw_playlist_name = getattr(playlist, "name", "Spotify Playlist")
                        safe_playlist_name = re.sub(r'[\\/*?:"<>|]', "", raw_playlist_name).strip()
                        target_dir = os.path.join(base_download_dir, safe_playlist_name)
                        os.makedirs(target_dir, exist_ok=True)

                        for track_item in playlist.tracks:
                            track = track_item.track
                            artists_str = ", ".join([artist.name for artist in track.artists])
                            song_query = f"{track.name} {artists_str}"
                            queries_to_download.append((song_query, song_query))
                        
                        self.log_to_terminal(f"v Playlist detected: '{raw_playlist_name}' ({len(queries_to_download)} songs)")
                except Exception as e:
                    self.log_to_terminal(f"x Spotify Error: {e}")
                    self.btn_download.config(state=tk.NORMAL)
                    return
            else:
                queries_to_download.append((inp, inp))

            self.current_target_dir = target_dir
            self.root.after(0, lambda: self.lbl_folder.config(text=f"Saved in: {target_dir}"))

            tree_items = []
            for idx, (title, query) in enumerate(queries_to_download, start=1):
                item_id = self.tree.insert("", tk.END, values=(str(idx), title, "⏳ Pending", "[░░░░░░░░░░] 0%"))
                tree_items.append((item_id, title, query))

            def make_hook(item_id):
                def progress_hook(d):
                    if d['status'] == 'downloading':
                        raw_percent = self.clean_ansi(d.get('_percent_str', '0%')).strip().replace('%', '')
                        try:
                            p_val = float(raw_percent)
                        except ValueError:
                            p_val = 0.0
                        
                        filled_blocks = int(p_val // 10)
                        bar = "█" * filled_blocks + "░" * (10 - filled_blocks)
                        progress_str = f"[{bar}] {p_val:.1f}%"
                        
                        speed = self.clean_ansi(d.get('_speed_str', 'N/A'))
                        full_display = f"{progress_str} ({speed})"

                        self.root.after(0, lambda: self.tree.set(item_id, "progress", full_display))
                        self.root.after(0, lambda: self.tree.set(item_id, "status", "📥 Downloading..."))
                    elif d['status'] == 'finished':
                        self.root.after(0, lambda: self.tree.set(item_id, "progress", "[██████████] 100.0%"))
                return progress_hook

            options = {
                "format": "best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
                "outtmpl": os.path.join(target_dir, "%(title)s.%(ext)s"),
                "extractor_args": {"youtube": {"player_client": ["mweb", "android"]}},
                "quiet": True,
            }

            failed_items = []

            # First download pass
            for item_id, title, query in tree_items:
                self.log_to_terminal(f"Starting download: {query}")
                options["progress_hooks"] = [make_hook(item_id)]
                
                target = query if query.startswith("http") else f"ytsearch1:{query}"

                success = False
                try:
                    with YoutubeDL(options) as ydl:
                        ydl.download([target])
                    self.root.after(0, lambda id=item_id: self.tree.set(id, "status", "✅ Done"))
                    self.root.after(0, lambda id=item_id: self.tree.set(id, "progress", "[██████████] 100%"))
                    self.log_to_terminal(f"-> Success: {query}")
                    success = True
                except Exception as e:
                    self.log_to_terminal(f"-> x Error with '{query}': {e}")

                if not success:
                    self.root.after(0, lambda id=item_id: self.tree.set(id, "status", "❌ Error"))
                    self.root.after(0, lambda id=item_id: self.tree.set(id, "progress", "Failed"))
                    failed_items.append((title, query))

            # Automatic Retry Pass for Failed Songs
            if failed_items:
                self.log_to_terminal(f"\n--- Retrying {len(failed_items)} failed download(s)... ---")
                retry_tree_items = []
                
                for title, query in failed_items:
                    next_idx = len(self.tree.get_children()) + 1
                    item_id = self.tree.insert("", tk.END, values=(str(next_idx), f"{title} (Retry)", "⏳ Retrying", "[░░░░░░░░░░] 0%"))
                    retry_tree_items.append((item_id, query))

                for item_id, query in retry_tree_items:
                    self.log_to_terminal(f"Retrying download: {query}")
                    options["progress_hooks"] = [make_hook(item_id)]
                    target = query if query.startswith("http") else f"ytsearch1:{query}"

                    try:
                        with YoutubeDL(options) as ydl:
                            ydl.download([target])
                        self.root.after(0, lambda id=item_id: self.tree.set(id, "status", "✅ Done"))
                        self.root.after(0, lambda id=item_id: self.tree.set(id, "progress", "[██████████] 100%"))
                        self.log_to_terminal(f"-> Retry Success: {query}")
                    except Exception as e:
                        self.root.after(0, lambda id=item_id: self.tree.set(id, "status", "❌ Failed"))
                        self.root.after(0, lambda id=item_id: self.tree.set(id, "progress", "Failed permanently"))
                        self.log_to_terminal(f"-> x Retry failed for '{query}': {e}")

            self.log_to_terminal(f"\nAll downloads completed! Folder: {target_dir}")
            messagebox.showinfo("Finished", f"All downloads completed!\nSaved in:\n{target_dir}")

        except Exception as e:
            self.log_to_terminal(f"x System Error: {e}")
        finally:
            self.root.after(0, lambda: self.btn_download.config(state=tk.NORMAL))


if __name__ == "__main__":
    root = tk.Tk()
    app = MusicDownloaderApp(root)
    root.mainloop()