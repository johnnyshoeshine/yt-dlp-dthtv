import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
import subprocess
import windnd
from engine import get_ffmpeg_command
from preview import get_preview_frame
import network
import glitch
import themes

class RetroBranderUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DHTV BRANDER v1.0")
        self.root.geometry("600x850")
        
        # Theme Initialization
        self.current_theme_name = "LIGHT"
        self.theme = themes.LIGHT
        self.root.configure(bg=self.theme["bg"])
        
        # Paths
        self.video_path = ""
        self.logo_path = ""
        self.overlay_path = ""
        self.deck_state = "MAIN" # DECK SELECT state: MAIN or OVERLAY
        self.photo = None # Keep reference to avoid garbage collection
        
        # Retro Style configuration
        style = ttk.Style()
        style.theme_use('classic')
        style.configure("TFrame", background="#d9d9d9")
        style.configure("TLabel", background="#d9d9d9", font=("MS Sans Serif", 8))
        style.configure("TButton", background="#d9d9d9", font=("MS Sans Serif", 8, "bold"))
        style.configure("TNotebook", background="#d9d9d9")
        style.configure("TNotebook.Tab", background="#d9d9d9", font=("MS Sans Serif", 8))
        
        self.setup_ui()
        
        # Hook Drag and Drop
        windnd.hook_dropfiles(self.root, self.on_drop)
        
        # Handle files passed via command line (dropped onto .exe)
        if len(sys.argv) > 1:
            self.on_drop([f.encode('utf-8') for f in sys.argv[1:]])

    def on_drop(self, files):
        for f in files:
            # windnd might return bytes
            path = f.decode('utf-8') if isinstance(f, bytes) else f
            ext = os.path.splitext(path)[1].lower()
            
            if self.deck_state == "MAIN":
                if ext in ['.mp4', '.mkv', '.avi', '.mov']:
                    self.video_path = path
                    print(f"Background set: {path}")
                elif ext in ['.png', '.jpg', '.jpeg', '.webp']:
                    self.logo_path = path
                    print(f"Logo set: {path}")
            else: # OVERLAY mode
                if ext in ['.mp4', '.mkv', '.avi', '.mov', '.gif']:
                    self.overlay_path = path
                    print(f"Overlay set: {path}")
                elif ext in ['.png', '.jpg', '.jpeg', '.webp']:
                    self.logo_path = path # Logos can still be dropped in overlay mode
                    print(f"Logo set: {path}")
        
        self.update_preview()
        
    def toggle_deck(self):
        if self.deck_state == "MAIN":
            self.deck_state = "OVERLAY"
            self.deck_button.config(text="DECK: OVERLAY", bg=self.theme["deck_overlay"])
        else:
            self.deck_state = "MAIN"
            self.deck_button.config(text="DECK: MAIN", bg=self.theme["deck_main"])

    def setup_ui(self):
        # Top: Deck Select Toggle
        self.top_frame = tk.Frame(self.root, bg=self.theme["bg"])
        self.top_frame.pack(fill="x", padx=10, pady=5)
        
        self.deck_button = tk.Button(
            self.top_frame,
            text="DECK: MAIN",
            bg=self.theme["deck_main"],
            fg=self.theme["button_fg"],
            activebackground=self.theme["active_bg"],
            relief="raised",
            bd=3,
            font=("MS Sans Serif", 8, "bold"),
            command=self.toggle_deck,
            width=20
        )
        self.deck_button.pack(side="left", pady=5)

        self.theme_button = tk.Button(
            self.top_frame,
            text=f"THEME: {self.current_theme_name}",
            bg=self.theme["button_bg"],
            fg=self.theme["button_fg"],
            activebackground=self.theme["active_bg"],
            relief="raised",
            bd=3,
            font=("MS Sans Serif", 8, "bold"),
            command=self.toggle_theme,
            width=15
        )
        self.theme_button.pack(side="right", pady=5)

        # Top: Viewfinder (Canvas)
        self.viewfinder_frame = tk.Frame(self.root, bg=self.theme["viewfinder_bg"], bd=2, relief="sunken")
        self.viewfinder_frame.pack(pady=10, padx=10, fill="both", expand=True)
        
        self.canvas = tk.Canvas(self.viewfinder_frame, bg=self.theme["canvas_bg"], highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas_text = self.canvas.create_text(300, 150, text="[ VIEWFINDER ]", fill=self.theme["viewfinder_fg"], font=("Courier", 12))

        # Middle: Notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(pady=5, padx=10, fill="x")

        # Tabs
        self.logo_tab = ttk.Frame(self.notebook)
        self.overlay_tab = ttk.Frame(self.notebook)
        self.trans_tab = ttk.Frame(self.notebook)
        self.glitch_tab = ttk.Frame(self.notebook)
        self.output_tab = ttk.Frame(self.notebook)
        self.network_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.logo_tab, text="Logo")
        self.notebook.add(self.overlay_tab, text="Overlay")
        self.notebook.add(self.trans_tab, text="Transitions")
        self.notebook.add(self.glitch_tab, text="Glitch")
        self.notebook.add(self.output_tab, text="Output")
        self.notebook.add(self.network_tab, text="Network")

        self.setup_logo_tab()
        self.setup_overlay_tab()
        self.setup_trans_tab()
        self.setup_glitch_tab()
        self.setup_output_tab()
        self.setup_network_tab()

        # Bottom: Actions
        self.bottom_frame = tk.Frame(self.root, bg=self.theme["bg"], bd=2, relief="raised")
        self.bottom_frame.pack(side="bottom", fill="x", padx=10, pady=10)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.bottom_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x", padx=10, pady=5)

        self.burn_button = tk.Button(
            self.bottom_frame, 
            text="BURN IT!", 
            bg=self.theme["button_bg"], 
            fg=self.theme["button_fg"],
            activebackground=self.theme["active_bg"],
            relief="raised",
            bd=3,
            font=("MS Sans Serif", 10, "bold"),
            command=self.start_burn
        )
        self.burn_button.pack(pady=5, padx=10, fill="x")
        
        # Apply initial theme styles
        self.apply_theme()

    def manual_load_video(self):
        path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.mkv *.avi *.mov")])
        if path:
            self.video_path = path
            self.update_preview()

    def manual_load_overlay(self):
        path = filedialog.askopenfilename(filetypes=[("Video/GIF files", "*.mp4 *.mkv *.avi *.mov *.gif")])
        if path:
            self.overlay_path = path
            self.update_preview()

    def setup_logo_tab(self):
        # Padding X, Padding Y, Scale
        f = self.logo_tab
        
        self.load_bg_btn = tk.Button(f, text="Load Background...", command=self.manual_load_video, bg="#d9d9d9", relief="raised")
        self.load_bg_btn.grid(row=0, column=0, columnspan=2, pady=10, padx=5, sticky="w")

        tk.Label(f, text="X Padding:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.logo_padx = tk.Scale(f, from_=0, to=100, orient="horizontal", bg="#d9d9d9", length=400, command=lambda x: self.update_preview())
        self.logo_padx.set(10)
        self.logo_padx.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(f, text="Y Padding:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.logo_pady = tk.Scale(f, from_=0, to=100, orient="horizontal", bg="#d9d9d9", length=400, command=lambda x: self.update_preview())
        self.logo_pady.set(10)
        self.logo_pady.grid(row=2, column=1, padx=5, pady=5)

        tk.Label(f, text="Scale:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.logo_scale = tk.Scale(f, from_=0.1, to=2.0, resolution=0.1, orient="horizontal", bg="#d9d9d9", length=400, command=lambda x: self.update_preview())
        self.logo_scale.set(1.0)
        self.logo_scale.grid(row=3, column=1, padx=5, pady=5)

        # Corner Picker
        tk.Label(f, text="Corner:").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        self.corner_frame = tk.Frame(f, bg="#d9d9d9")
        self.corner_frame.grid(row=4, column=1, sticky="w", padx=5, pady=5)
        
        self.corner_var = tk.StringVar(value="BR")
        self.corner_btns = {}
        for i, (label, value) in enumerate([("TL", "TL"), ("TR", "TR"), ("BL", "BL"), ("BR", "BR")]):
            btn = tk.Button(
                self.corner_frame, 
                text=label, 
                width=4, 
                command=lambda v=value: self.set_corner(v),
                relief="raised",
                bg="#d9d9d9"
            )
            btn.grid(row=i//2, column=i%2, padx=2, pady=2)
            self.corner_btns[value] = btn
        self.set_corner("BR") # Default

        # Invert Toggle
        self.invert_logo = tk.BooleanVar(value=False)
        self.invert_check = tk.Checkbutton(f, text="Invert Logo Colors", variable=self.invert_logo, bg="#d9d9d9", command=self.update_preview)
        self.invert_check.grid(row=5, column=0, columnspan=2, sticky="w", padx=5, pady=5)

    def set_corner(self, corner):
        self.corner_var.set(corner)
        for val, btn in self.corner_btns.items():
            if val == corner:
                btn.config(relief="sunken", bg=self.theme["sunken_bg"])
            else:
                btn.config(relief="raised", bg=self.theme["button_bg"])
        self.update_preview()

    def setup_overlay_tab(self):
        # Freq, Dur, Scale, Opacity
        f = self.overlay_tab
        
        self.load_ov_btn = tk.Button(f, text="Load Overlay...", command=self.manual_load_overlay, bg="#d9d9d9", relief="raised")
        self.load_ov_btn.grid(row=0, column=0, columnspan=2, pady=10, padx=5, sticky="w")

        tk.Label(f, text="Frequency (m):").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.ov_freq = tk.Scale(f, from_=1, to=60, orient="horizontal", bg="#d9d9d9", length=400)
        self.ov_freq.set(5)
        self.ov_freq.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(f, text="Duration (s):").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.ov_dur = tk.Scale(f, from_=1, to=120, orient="horizontal", bg="#d9d9d9", length=400)
        self.ov_dur.set(30)
        self.ov_dur.grid(row=2, column=1, padx=5, pady=5)

        tk.Label(f, text="Scale (%):").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.ov_scale = tk.Scale(f, from_=10, to=200, orient="horizontal", bg="#d9d9d9", length=400, command=lambda x: self.update_preview())
        self.ov_scale.set(70)
        self.ov_scale.grid(row=3, column=1, padx=5, pady=5)

        tk.Label(f, text="Opacity:").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        self.ov_opacity = tk.Scale(f, from_=0.0, to=1.0, resolution=0.1, orient="horizontal", bg="#d9d9d9", length=400, command=lambda x: self.update_preview())
        self.ov_opacity.set(1.0)
        self.ov_opacity.grid(row=4, column=1, padx=5, pady=5)

        tk.Label(f, text="Blend Mode:").grid(row=5, column=0, sticky="w", padx=5, pady=5)
        self.ov_blend = ttk.Combobox(f, values=["normal", "multiply", "screen", "overlay", "darken", "lighten"], state="readonly")
        self.ov_blend.set("normal")
        self.ov_blend.grid(row=5, column=1, sticky="w", padx=5, pady=5)
        self.ov_blend.bind("<<ComboboxSelected>>", lambda e: self.update_preview())

    def setup_trans_tab(self):
        f = self.trans_tab
        
        tk.Label(f, text="Transition Type:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.ov_trans = ttk.Combobox(f, values=["None", "Fade", "Slide"], state="readonly")
        self.ov_trans.set("None")
        self.ov_trans.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        self.ov_continuous = tk.BooleanVar(value=False)
        self.continuous_check = tk.Checkbutton(f, text="Continuous Mode (Always On)", variable=self.ov_continuous, bg="#d9d9d9")
        self.continuous_check.grid(row=1, column=0, columnspan=2, sticky="w", padx=5, pady=5)
        
        tk.Label(f, text="Trans. Duration (s):").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.ov_trans_dur = tk.Scale(f, from_=0.1, to=5.0, resolution=0.1, orient="horizontal", bg="#d9d9d9", length=400)
        self.ov_trans_dur.set(1.0)
        self.ov_trans_dur.grid(row=2, column=1, padx=5, pady=5)

    def setup_network_tab(self):
        f = self.network_tab
        
        tk.Label(f, text="Video URL:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.url_entry = tk.Entry(f, width=50)
        self.url_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        tk.Label(f, text="Method:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.method_var = tk.StringVar(value="download")
        tk.Radiobutton(f, text="Download", variable=self.method_var, value="download", bg="#d9d9d9").grid(row=1, column=1, sticky="w")
        tk.Radiobutton(f, text="Stream", variable=self.method_var, value="stream", bg="#d9d9d9").grid(row=1, column=1, padx=100, sticky="w")
        
        self.load_button = tk.Button(f, text="LOAD URL", command=self.load_url, bg="#d9d9d9", relief="raised")
        self.load_button.grid(row=2, column=0, columnspan=2, pady=10)
        
        self.net_status = tk.Label(f, text="Status: Ready", fg="blue")
        self.net_status.grid(row=3, column=0, columnspan=2)

    def load_url(self):
        url = self.url_entry.get().strip()
        if not url: return
        
        target = "background" if self.deck_state == "MAIN" else "overlay"
        method = self.method_var.get()
        
        self.net_status.config(text=f"Status: Initializing {method}...", fg="orange")
        self.load_button.config(state="disabled")

        def callback(result, error):
            self.root.after(0, lambda: self.handle_load_result(result, error, target))

        if method == "stream":
            network.get_stream_url(url, callback)
        else:
            network.download_video(url, callback)

    def handle_load_result(self, result, error, target):
        self.load_button.config(state="normal")
        if error:
            self.net_status.config(text=f"Status: Error - {error[:50]}...", fg="red")
            messagebox.showerror("Network Error", error)
        else:
            self.net_status.config(text="Status: Complete!", fg="green")
            if target == "background":
                self.video_path = result
            else:
                self.overlay_path = result
            self.update_preview()


    def setup_glitch_tab(self):
        f = self.glitch_tab
        
        tk.Label(f, text="Mosh Frequency:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.mosh_freq = tk.Scale(f, from_=0.0, to=1.0, resolution=0.01, orient="horizontal", bg="#d9d9d9", length=400)
        self.mosh_freq.set(0.1)
        self.mosh_freq.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(f, text="Mosh Duration:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.mosh_dur = tk.Scale(f, from_=1, to=30, orient="horizontal", bg="#d9d9d9", length=400)
        self.mosh_dur.set(5)
        self.mosh_dur.grid(row=1, column=1, padx=5, pady=5)
        
        self.mosh_btn = tk.Button(f, text="PREVIEW MOSH (3s)", command=self.preview_mosh, bg="#d9d9d9", relief="raised")
        self.mosh_btn.grid(row=2, column=0, columnspan=2, pady=20)

    def preview_mosh(self):
        if not self.video_path:
            messagebox.showwarning("Warning", "Load a video first!")
            return
            
        self.mosh_btn.config(state="disabled", text="MOSHING...")
        self.root.update()
        
        try:
            # 1. Extract a 3-second clip
            temp_clip = "temp_preview_clip.mp4"
            subprocess.run([
                'ffmpeg', '-y', '-ss', '0', '-i', self.video_path,
                '-t', '3', '-c', 'copy', temp_clip
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # 2. Mosh it
            mosh_out = "preview_mosh.mp4"
            glitch.mosh_video(temp_clip, mosh_out, self.mosh_freq.get(), self.mosh_dur.get())
            
            # 3. Play it (or show in viewfinder)
            # For now, we just open it with system default
            os.startfile(mosh_out)
            
            # Clean up temp files later or just leave them
            if os.path.exists(temp_clip): os.remove(temp_clip)
            
        except Exception as e:
            messagebox.showerror("Mosh Error", str(e))
        finally:
            self.mosh_btn.config(state="normal", text="PREVIEW MOSH (3s)")

    def browse_output_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.out_folder_path.set(folder)

    def get_settings(self):
        return {
            'logo_padx': self.logo_padx.get(),
            'logo_pady': self.logo_pady.get(),
            'logo_scale': self.logo_scale.get(),
            'logo_corner': self.corner_var.get(),
            'logo_invert': self.invert_logo.get(),
            'ov_freq': self.ov_freq.get() * 60,
            'ov_dur': self.ov_dur.get(),
            'ov_scale': self.ov_scale.get() / 100.0,
            'ov_opacity': self.ov_opacity.get(),
            'ov_blend': self.ov_blend.get(),
            'ov_trans': self.ov_trans.get(),
            'ov_continuous': self.ov_continuous.get(),
            'ov_trans_dur': self.ov_trans_dur.get(),
            'mosh_freq': self.mosh_freq.get(),
            'mosh_dur': self.mosh_dur.get(),
            'audio_mode': self.audio_mode.get(),
            'use_nvenc': self.use_nvenc.get(),
            'out_res': self.out_res.get(),
            'out_crf': self.out_crf.get(),
            'out_fps': self.out_fps.get(),
            'out_name': self.out_name.get(),
            'out_folder': self.out_folder_path.get(),
            'open_folder': self.open_folder.get()
        }

    def update_preview(self):
        if not self.video_path:
            return
            
        settings = self.get_settings()
        self.photo = get_preview_frame(
            self.video_path, 
            self.logo_path, 
            self.overlay_path, 
            settings,
            max_size=(600, 300) # Size of the viewfinder area
        )
        
        if self.photo:
            self.canvas.delete("all")
            self.canvas.create_image(300, 150, image=self.photo, anchor="center")
        else:
            self.canvas.delete("all")
            self.canvas.create_text(300, 150, text="[ PREVIEW ERROR ]", fill="#ff0000", font=("Courier", 12))

    def setup_output_tab(self):
        f = self.output_tab

        # Resolution
        tk.Label(f, text="Resolution:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.out_res = ttk.Combobox(f, values=["Original", "1080p", "720p", "480p"], state="readonly")
        self.out_res.set("Original")
        self.out_res.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        # Quality (CRF)
        tk.Label(f, text="Quality (CRF):").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.out_crf = tk.Scale(f, from_=0, to=51, orient="horizontal", bg=self.theme["bg"], length=400)
        self.out_crf.set(23)
        self.out_crf.grid(row=1, column=1, padx=5, pady=5)

        # Framerate
        tk.Label(f, text="Framerate:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.out_fps = ttk.Combobox(f, values=["Original", "24", "30", "60"], state="readonly")
        self.out_fps.set("Original")
        self.out_fps.grid(row=2, column=1, sticky="w", padx=5, pady=5)

        # Output Name
        tk.Label(f, text="Output Name:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.out_name = tk.Entry(f, width=40, bg=self.theme["entry_bg"], fg=self.theme["entry_fg"])
        self.out_name.insert(0, "{original}_branded")
        self.out_name.grid(row=3, column=1, sticky="w", padx=5, pady=5)

        # Output Folder
        tk.Label(f, text="Output Folder:").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        self.out_folder_frame = tk.Frame(f, bg=self.theme["bg"])
        self.out_folder_frame.grid(row=4, column=1, sticky="w", padx=5, pady=5)
        
        self.out_folder_path = tk.StringVar()
        self.out_folder_entry = tk.Entry(self.out_folder_frame, textvariable=self.out_folder_path, width=40, bg=self.theme["entry_bg"], fg=self.theme["entry_fg"])
        self.out_folder_entry.pack(side="left")
        
        self.browse_folder_btn = tk.Button(self.out_folder_frame, text="Browse...", command=self.browse_output_folder, bg=self.theme["button_bg"], fg=self.theme["button_fg"])
        self.browse_folder_btn.pack(side="left", padx=5)

        # Open Folder Checkbox
        self.open_folder = tk.BooleanVar(value=True)
        self.open_folder_check = tk.Checkbutton(f, text="Open Folder After Burn", variable=self.open_folder, bg=self.theme["bg"])
        self.open_folder_check.grid(row=5, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        # Hardware Acceleration
        self.use_nvenc = tk.BooleanVar(value=True)
        self.nvenc_check = tk.Checkbutton(f, text="Use NVIDIA NVENC (Recommended)", variable=self.use_nvenc, bg=self.theme["bg"])
        self.nvenc_check.grid(row=6, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        # Audio Mode
        tk.Label(f, text="Audio Mode:").grid(row=7, column=0, sticky="w", padx=5, pady=5)
        self.audio_mode = ttk.Combobox(f, values=["Original", "Mute Main", "Overlay Only", "Silent"], state="readonly")
        self.audio_mode.set("Original")
        self.audio_mode.grid(row=7, column=1, sticky="w", padx=5, pady=5)

    def start_burn(self):
        messagebox.showinfo("Burn It!", "Ready to burn. Logic pending Task 5 integration.")

    def toggle_theme(self):
        if self.current_theme_name == "LIGHT":
            self.current_theme_name = "DARK"
            self.theme = themes.DARK
        else:
            self.current_theme_name = "LIGHT"
            self.theme = themes.LIGHT
            
        self.theme_button.config(text=f"THEME: {self.current_theme_name}")
        self.apply_theme()

    def update_styles(self):
        style = ttk.Style()
        style.theme_use('classic')
        style.configure("TFrame", background=self.theme["bg"])
        style.configure("TLabel", background=self.theme["bg"], foreground=self.theme["fg"], font=("MS Sans Serif", 8))
        style.configure("TButton", background=self.theme["button_bg"], foreground=self.theme["button_fg"], font=("MS Sans Serif", 8, "bold"))
        style.configure("TNotebook", background=self.theme["bg"])
        style.configure("TNotebook.Tab", background=self.theme["bg"], foreground=self.theme["fg"], font=("MS Sans Serif", 8))
        style.configure("TCombobox", fieldbackground=self.theme["entry_bg"], background=self.theme["button_bg"], foreground=self.theme["entry_fg"])

    def apply_theme(self):
        self.root.configure(bg=self.theme["bg"])
        self.update_styles()
        self.update_widget_colors(self.root)
        
        # Specific overrides for non-standard elements
        if hasattr(self, 'canvas'):
            self.canvas.configure(bg=self.theme["canvas_bg"])
            self.viewfinder_frame.configure(bg=self.theme["viewfinder_bg"])
            self.canvas.itemconfig(self.canvas_text, fill=self.theme["viewfinder_fg"])
        
        # Update deck button color
        if hasattr(self, 'deck_button'):
            if self.deck_state == "MAIN":
                self.deck_button.config(bg=self.theme["deck_main"])
            else:
                self.deck_button.config(bg=self.theme["deck_overlay"])
            
        # Update corner buttons
        if hasattr(self, 'corner_btns'):
            self.set_corner(self.corner_var.get())

    def update_widget_colors(self, container):
        for widget in container.winfo_children():
            w_type = widget.winfo_class()
            
            # Skip ttk widgets as they are handled by styles
            if w_type.startswith("T"):
                # But recurse into them!
                if widget.winfo_children():
                    self.update_widget_colors(widget)
                continue

            try:
                if w_type == "Frame":
                    widget.configure(bg=self.theme["bg"])
                elif w_type == "Label":
                    widget.configure(bg=self.theme["bg"], fg=self.theme["fg"])
                elif w_type == "Button":
                    # Special buttons might have their own bg logic in apply_theme
                    if widget not in [self.deck_button, self.theme_button, self.burn_button]:
                        widget.configure(bg=self.theme["button_bg"], fg=self.theme["button_fg"], activebackground=self.theme["active_bg"])
                    else:
                        widget.configure(fg=self.theme["button_fg"], activebackground=self.theme["active_bg"])
                        if widget in [self.theme_button, self.burn_button]:
                            widget.configure(bg=self.theme["button_bg"])
                elif w_type == "Scale":
                    widget.configure(bg=self.theme["bg"], fg=self.theme["fg"], highlightbackground=self.theme["bg"])
                elif w_type == "Checkbutton":
                    widget.configure(bg=self.theme["bg"], fg=self.theme["fg"], selectcolor=self.theme["entry_bg"], activebackground=self.theme["bg"], activeforeground=self.theme["fg"])
                elif w_type == "Radiobutton":
                    widget.configure(bg=self.theme["bg"], fg=self.theme["fg"], selectcolor=self.theme["entry_bg"], activebackground=self.theme["bg"], activeforeground=self.theme["fg"])
                elif w_type == "Entry":
                    widget.configure(bg=self.theme["entry_bg"], fg=self.theme["entry_fg"], insertbackground=self.theme["entry_fg"])
            except tk.TclError:
                pass # Some widgets might not support certain properties
            
            # Recurse
            if widget.winfo_children():
                self.update_widget_colors(widget)

if __name__ == "__main__":
    root = tk.Tk()
    app = RetroBranderUI(root)
    root.mainloop()
