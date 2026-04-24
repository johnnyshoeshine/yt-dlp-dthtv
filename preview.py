import cv2
from PIL import Image, ImageTk, ImageDraw, ImageOps
import numpy as np
import os

def get_preview_frame(video_path, logo_path, overlay_path, settings, max_size=(320, 240)):
    """
    Grabs the first frame of the video, applies logo and overlay based on settings,
    and returns a Tkinter-compatible image.
    """
    # 1. Grab frame using OpenCV
    cap = cv2.VideoCapture(video_path)
    success, frame = cap.read()
    cap.release()
    
    if not success:
        return None

    # Convert OpenCV BGR to RGB
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_frame = Image.fromarray(frame)
    
    # Get original dimensions for coordinate calculations
    orig_w, orig_h = pil_frame.size
    
    # 2. Apply Logo
    if logo_path and os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        
        # Invert Logo Colors if requested
        if settings.get('logo_invert', False):
            # For RGBA, we only want to invert the RGB channels
            r, g, b, a = logo.split()
            inverted_rgb = ImageOps.invert(Image.merge("RGB", (r, g, b)))
            ir, ig, ib = inverted_rgb.split()
            logo = Image.merge("RGBA", (ir, ig, ib, a))

        # Scale logo
        l_scale = settings.get('logo_scale', 1.0)
        l_w, l_h = logo.size
        new_l_w = int(l_w * l_scale)
        new_l_h = int(l_h * l_scale)
        logo = logo.resize((new_l_w, new_l_h), Image.Resampling.LANCZOS)
        
        # Calculate position based on corner
        padx = settings.get('logo_padx', 10)
        pady = settings.get('logo_pady', 10)
        corner = settings.get('logo_corner', 'BR')
        
        if corner == 'TL':
            pos_x, pos_y = padx, pady
        elif corner == 'TR':
            pos_x, pos_y = orig_w - new_l_w - padx, pady
        elif corner == 'BL':
            pos_x, pos_y = padx, orig_h - new_l_h - pady
        else: # BR
            pos_x, pos_y = orig_w - new_l_w - padx, orig_h - new_l_h - pady
        
        # Paste logo (using itself as mask for transparency)
        pil_frame.paste(logo, (pos_x, pos_y), logo)

    # 3. Apply Overlay
    if overlay_path and os.path.exists(overlay_path):
        overlay = Image.open(overlay_path).convert("RGBA")
        
        # Scale overlay
        ov_scale = settings.get('ov_scale', 0.7)
        ov_w, ov_h = overlay.size
        new_ov_w = int(orig_w * ov_scale)
        new_ov_h = int(ov_h * (new_ov_w / ov_w))
        overlay = overlay.resize((new_ov_w, new_ov_h), Image.Resampling.LANCZOS)
        
        # Apply Opacity
        opacity = settings.get('ov_opacity', 1.0)
        if opacity < 1.0:
            # Adjust alpha channel
            alpha = overlay.getchannel('A')
            alpha = alpha.point(lambda p: int(p * opacity))
            overlay.putalpha(alpha)
            
        # Calculate position (Center)
        pos_x = (orig_w - new_ov_w) // 2
        pos_y = (orig_h - new_ov_h) // 2
        
        # Paste overlay
        pil_frame.paste(overlay, (pos_x, pos_y), overlay)

    # 4. Resize for Viewfinder
    pil_frame.thumbnail(max_size, Image.Resampling.LANCZOS)
    
    # 5. Convert to Tkinter Format
    return ImageTk.PhotoImage(pil_frame)
