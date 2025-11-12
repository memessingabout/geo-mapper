# gui.py  (FULL FILE – replace your current one)

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import darkdetect
from .config import load_settings, save_settings, MAPS_DIR, TILES_DIR
from .gpx_parser import parse_gpx_file, safe_date_from_filename
from .map_generator import create_map
import webbrowser

class GPXMapperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GPX Route Animator v3.0")
        self.root.geometry("720x580")
        self.settings = load_settings()
        self.dark_mode = self.settings.get("gui_dark_mode", darkdetect.isDark())
        self.setup_ui()
        self.apply_theme()

    def setup_ui(self):
        pad = {'padx': 10, 'pady': 5}

        # Header
        tk.Label(self.root, text="GPX Multi-Map Generator", font=("Arial", 16, "bold")).pack(pady=10)

        # Folder
        f1 = ttk.Frame(self.root)
        f1.pack(fill='x', **pad)
        tk.Label(f1, text="Folder:").pack(side='left')
        self.folder_var = tk.StringVar(value=self.settings.get("last_folder", ""))
        tk.Entry(f1, textvariable=self.folder_var, width=50).pack(side='left', padx=5, expand=True, fill='x')
        ttk.Button(f1, text="Browse", command=self.browse).pack(side='right')

        # File List with Scrollbar
        list_frame = ttk.Frame(self.root)
        list_frame.pack(fill='both', expand=True, **pad)

        self.listbox = tk.Listbox(list_frame, selectmode='extended', height=15)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        self.listbox.config(yscrollcommand=scrollbar.set)

        self.listbox.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Offline tiles + Dark Mode Button
        f2 = ttk.Frame(self.root)
        f2.pack(fill='x', **pad)
        ttk.Label(f2, text="Offline:").pack(side='left', padx=(0,5))
        self.tiles_var = tk.StringVar(value=self.settings.get("offline_tiles", ""))
        self.tiles_combobox = ttk.Combobox(f2, textvariable=self.tiles_var, width=30, state="readonly")
        self.tiles_combobox.pack(side='left', padx=5)
        ttk.Button(f2, text="Refresh", command=self.refresh_tiles).pack(side='left', padx=5)

        # DARK MODE BUTTON (no dark_var)
        self.dark_btn = ttk.Button(f2, text="Dark Mode", command=self.toggle_dark)
        self.dark_btn.pack(side='right', padx=5)

        # Buttons
        f3 = ttk.Frame(self.root)
        f3.pack(fill='x', **pad)
        ttk.Button(f3, text="Refresh Files", command=self.load_files).pack(side='left', padx=5)
        ttk.Button(f3, text="Generate Selected", command=self.generate).pack(side='right', padx=5)

        # Status
        self.status = tk.Label(self.root, text="Ready", anchor='w', fg="gray")
        self.status.pack(fill='x', **pad)

        # Init
        self.refresh_tiles()
        self.load_files()

    def apply_theme(self):
        # Full palette
        if self.dark_mode:
            bg = "#2b2b2b"
            fg = "#ffffff"
            select_bg = "#3a3a3a"
            select_fg = "#ffffff"
            active_bg = "#4a4a4a"
            active_fg = "#ffffff"
        else:
            bg = "#ffffff"
            fg = "#000000"
            select_bg = "#cccccc"
            select_fg = "#000000"
            active_bg = "#e5e5e5"
            active_fg = "#000000"

        try:
            self.root.tk.eval(f'''
                tk_setPalette \
                    background "{bg}" \
                    foreground "{fg}" \
                    selectbackground "{select_bg}" \
                    selectforeground "{select_fg}" \
                    activebackground "{active_bg}" \
                    activeforeground "{active_fg}"
            ''')
        except Exception as e:
            print(f"[Theme] Palette failed: {e}")

        style = ttk.Style()
        style.theme_use('clam')

        # Update button
        self.dark_btn.config(text="Light Mode" if self.dark_mode else "Dark Mode")
        self.root.update_idletasks()

    def toggle_dark(self):
        self.dark_mode = not self.dark_mode
        self.settings["gui_dark_mode"] = self.dark_mode
        save_settings(self.settings)
        self.apply_theme()

    def browse(self):
        folder = filedialog.askdirectory(initialdir=self.folder_var.get())
        if folder:
            self.folder_var.set(folder)
            self.load_files()

    def refresh_tiles(self):
        tiles = [""] + [str(p) for p in TILES_DIR.glob("*.mbtiles")]
        self.tiles_combobox['values'] = tiles
        if self.tiles_var.get() not in tiles:
            self.tiles_var.set(tiles[0] if tiles else "")

    def load_files(self):
        folder = Path(self.folder_var.get())
        if not folder.is_dir():
            self.listbox.delete(0, tk.END)
            self.status.config(text="Invalid folder", fg="red")
            return

        self.settings["last_folder"] = str(folder.resolve())
        save_settings(self.settings)

        self.listbox.delete(0, tk.END)
        files = [f for f in folder.iterdir() if f.suffix.lower() == '.gpx']
        dated = []
        for f in files:
            if d := safe_date_from_filename(f.name):
                dated.append((d, f))
        dated.sort()
        for d, f in dated:
            self.listbox.insert(tk.END, f"{d} → {f.name}")
        self.status.config(text=f"{len(dated)} files", fg="green")

    def generate(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("No Selection", "Select one or more files.")
            return

        self.status.config(text="Generating...", fg="blue")
        self.root.update()

        successes = 0
        for idx in sel:
            item = self.listbox.get(idx)
            date_str = item.split(' → ')[0]
            gpx_path = Path(self.folder_var.get()) / item.split(' → ')[1]

            try:
                gpx = parse_gpx_file(gpx_path)
            except Exception as e:
                messagebox.showerror("Parse Error", str(e))
                continue

            output_path = MAPS_DIR / f"{date_str}_route.html"
            offline = self.tiles_var.get() if self.tiles_var.get() else None

            success, msg = create_map(
                gpx=gpx, date_str=date_str, output_path=output_path,
                map_dark_mode=self.dark_mode, use_offline=offline,
                parent_root=self.root
            )

            if success:
                successes += 1
                webbrowser.open(str(output_path.resolve()))
            else:
                if "Cancelled" not in msg:
                    messagebox.showinfo("Skipped", msg)

        self.status.config(text=f"Generated {successes}/{len(sel)} maps",
                            fg="green" if successes else "red")
