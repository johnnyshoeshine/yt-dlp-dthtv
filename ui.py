import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
import windnd
from engine import get_ffmpeg_command
from preview import get_preview_frame

class RetroBranderUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DHTV BRANDER v1.0")
        self.root.geometry("600x800")
        self.root.configure(bg="#d9d9d9")
        
        # Paths
        self.video_path = ""
        self.logo_path = ""
        self.overlay_path = ""
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
            
            if ext in ['.mp4', '.mkv', '.avi', '.mov']:
                # If we already have a video, maybe this is the overlay?
                if not self.video_path:
                    self.video_path = path
                    print(f"Video set: {path}")
                else:
                    self.overlay_path = path
                    print(f"Overlay set (video): {path}")
            elif ext in ['.png', '.jpg', '.jpeg', '.webp']:
                self.logo_path = path
                print(f"Logo set: {path}")
            elif ext in ['.gif']:
                self.overlay_path = path
                print(f"Overlay set (gif): {path}")
        
        self.update_preview()
        
    def setup_ui(self):
        # Top: Viewfinder (Canvas)
        self.viewfinder_frame = tk.Frame(self.root, bg="#000000", bd=2, relief="sunken")
        self.viewfinder_frame.pack(pady=10, padx=10, fill="both", expand=True)
        
        self.canvas = tk.Canvas(self.viewfinder_frame, bg="#1a1a1a", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas_text = self.canvas.create_text(300, 150, text="[ VIEWFINDER ]", fill="#00ff00", font=("Courier", 12))

        # Middle: Notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(pady=5, padx=10, fill="x")

        # Tabs
        self.logo_tab = ttk.Frame(self.notebook)
        self.overlay_tab = ttk.Frame(self.notebook)
        self.output_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.logo_tab, text="Logo")
        self.notebook.add(self.overlay_tab, text="Overlay")
        self.notebook.add(self.output_tab, text="Output")

        self.setup_logo_tab()
        self.setup_overlay_tab()
        self.setup_output_tab()

        # Bottom: Actions
        self.bottom_frame = tk.Frame(self.root, bg="#d9d9d9", bd=2, relief="raised")
        self.bottom_frame.pack(side="bottom", fill="x", padx=10, pady=10)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.bottom_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x", padx=10, pady=5)

        self.burn_button = tk.Button(
            self.bottom_frame, 
            text="BURN IT!", 
            bg="#d9d9d9", 
            activebackground="#c0c0c0",
            relief="raised",
            bd=3,
            font=("MS Sans Serif", 10, "bold"),
            command=self.start_burn
        )
        self.burn_button.pack(pady=5, padx=10, fill="x")

    def setup_logo_tab(self):
        # Padding X, Padding Y, Scale
        f = self.logo_tab
        
        tk.Label(f, text="X Padding:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.logo_padx = tk.Scale(f, from_=0, to=100, orient="horizontal", bg="#d9d9d9", length=400, command=lambda x: self.update_preview())
        self.logo_padx.set(10)
        self.logo_padx.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(f, text="Y Padding:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.logo_pady = tk.Scale(f, from_=0, to=100, orient="horizontal", bg="#d9d9d9", length=400, command=lambda x: self.update_preview())
        self.logo_pady.set(10)
        self.logo_pady.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(f, text="Scale:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.logo_scale = tk.Scale(f, from_=0.1, to=2.0, resolution=0.1, orient="horizontal", bg="#d9d9d9", length=400, command=lambda x: self.update_preview())
        self.logo_scale.set(1.0)
        self.logo_scale.grid(row=2, column=1, padx=5, pady=5)

    def setup_overlay_tab(self):
        # Freq, Dur, Scale, Opacity
        f = self.overlay_tab

        tk.Label(f, text="Frequency (m):").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.ov_freq = tk.Scale(f, from_=1, to=60, orient="horizontal", bg="#d9d9d9", length=400)
        self.ov_freq.set(5)
        self.ov_freq.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(f, text="Duration (s):").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.ov_dur = tk.Scale(f, from_=1, to=120, orient="horizontal", bg="#d9d9d9", length=400)
        self.ov_dur.set(30)
        self.ov_dur.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(f, text="Scale (%):").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.ov_scale = tk.Scale(f, from_=10, to=200, orient="horizontal", bg="#d9d9d9", length=400, command=lambda x: self.update_preview())
        self.ov_scale.set(70)
        self.ov_scale.grid(row=2, column=1, padx=5, pady=5)

        tk.Label(f, text="Opacity:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.ov_opacity = tk.Scale(f, from_=0.0, to=1.0, resolution=0.1, orient="horizontal", bg="#d9d9d9", length=400, command=lambda x: self.update_preview())
        self.ov_opacity.set(1.0)
        self.ov_opacity.grid(row=3, column=1, padx=5, pady=5)

        tk.Label(f, text="Blend Mode:").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        self.ov_blend = ttk.Combobox(f, values=["normal", "multiply", "screen", "overlay", "darken", "lighten"], state="readonly")
        self.ov_blend.set("normal")
        self.ov_blend.grid(row=4, column=1, sticky="w", padx=5, pady=5)
        self.ov_blend.bind("<<ComboboxSelected>>", lambda e: self.update_preview())

    def get_settings(self):
        return {
            'logo_padx': self.logo_padx.get(),
            'logo_pady': self.logo_pady.get(),
            'logo_scale': self.logo_scale.get(),
            'ov_scale': self.ov_scale.get() / 100.0,
            'ov_opacity': self.ov_opacity.get(),
            'ov_blend': self.ov_blend.get()
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

        tk.Label(f, text="Format:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.out_format = ttk.Combobox(f, values=[".mp4", ".mkv"], state="readonly")
        self.out_format.set(".mp4")
        self.out_format.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        self.use_nvenc = tk.BooleanVar(value=True)
        self.nvenc_check = tk.Checkbutton(f, text="Use NVIDIA NVENC", variable=self.use_nvenc, bg="#d9d9d9")
        self.nvenc_check.grid(row=1, column=0, columnspan=2, sticky="w", padx=5, pady=5)

    def start_burn(self):
        messagebox.showinfo("Burn It!", "Ready to burn. Logic pending Task 5 integration.")

if __name__ == "__main__":
    root = tk.Tk()
    app = RetroBranderUI(root)
    root.mainloop()
