import subprocess
import os

def get_ffmpeg_command(input_video, logo, overlay_path, output, settings):
    """
    Generates the FFmpeg command for branding a video with a logo and a periodic overlay.
    """
    v_codec = "h264_nvenc" if settings.get('use_nvenc', False) else "libx264"
    
    # Logic for looping: -ignore_loop for GIF, -stream_loop for Video
    is_gif = overlay_path.lower().endswith('.gif') if overlay_path else False
    loop_flag = ['-ignore_loop', '0'] if is_gif else ['-stream_loop', '-1']
    
    opacity = settings.get('ov_opacity', 1.0) # Corrected key from opacity to ov_opacity
    
    # Logo Settings
    logo_padx = settings.get('logo_padx', 10)
    logo_pady = settings.get('logo_pady', 10)
    logo_scale = settings.get('logo_scale', 1.0)
    corner = settings.get('logo_corner', 'BR')
    
    if corner == 'TL':
        logo_pos = f"{logo_padx}:{logo_pady}"
    elif corner == 'TR':
        logo_pos = f"W-w-{logo_padx}:{logo_pady}"
    elif corner == 'BL':
        logo_pos = f"{logo_padx}:H-h-{logo_pady}"
    else: # BR
        logo_pos = f"W-w-{logo_padx}:H-h-{logo_pady}"
        
    logo_invert = settings.get('logo_invert', False)
    
    overlay_scale = settings.get('ov_scale', 0.7)
    overlay_freq = settings.get('ov_freq', 300)
    overlay_dur = settings.get('ov_dur', 30)
    overlay_trans = settings.get('ov_trans', 'None')
    overlay_trans_dur = settings.get('ov_trans_dur', 1.0)
    overlay_continuous = settings.get('ov_continuous', False)

    if overlay_continuous:
        enable_expr = "1"
        rel_t = "t"
        # For continuous, only fade in at start, no periodic end
        trans_factor = f"clip(t/{overlay_trans_dur},0,1)"
    else:
        enable_expr = f"between(mod(t,{overlay_freq}),0,{overlay_dur})"
        rel_t = f"mod(t,{overlay_freq})"
        trans_factor = f"clip({rel_t}/{overlay_trans_dur},0,1)*clip(({overlay_dur}-{rel_t})/{overlay_trans_dur},0,1)"

    if overlay_trans == "Fade":
        opacity_filter = f"format=rgba,colorchannelmixer=aa='{opacity}*{trans_factor}'"
        ov_x = "(W-w)/2"
        ov_y = "(H-h)/2"
    elif overlay_trans == "Slide":
        opacity_filter = f"format=rgba,colorchannelmixer=aa={opacity}"
        ov_x = "(W-w)/2"
        ov_y = f"H-(H-(H-h)/2)*({trans_factor})"
    else: # None
        opacity_filter = f"format=rgba,colorchannelmixer=aa={opacity}"
        ov_x = "(W-w)/2"
        ov_y = "(H-h)/2"
    
    cmd = [
        'ffmpeg', '-hwaccel', 'cuda' if settings.get('use_nvenc', False) else 'auto'
    ]

    if logo:
        logo_filters = f"scale=iw*{logo_scale}:-1"
        if logo_invert:
            logo_filters = f"format=rgba,negate=component_mask=7," + logo_filters
            
        filter_str = (
            f"[1:v]{logo_filters}[l_proc]; "
            f"[0:v][l_proc]overlay={logo_pos}[v_logo]; "
            f"[2:v]scale=iw*{overlay_scale}:-1,{opacity_filter}[ovl]; "
            f"[v_logo][ovl]overlay={ov_x}:{ov_y}:enable='{enable_expr}':shortest=1"
        )
        cmd.extend(['-i', input_video, '-i', logo])
        cmd.extend(loop_flag)
        cmd.extend(['-i', overlay_path])
    else:
        filter_str = (
            f"[0:v]scale=iw:ih[v_bg]; "
            f"[1:v]scale=iw*{overlay_scale}:-1,{opacity_filter}[ovl]; "
            f"[v_bg][ovl]overlay={ov_x}:{ov_y}:enable='{enable_expr}':shortest=1"
        )
        cmd.extend(['-i', input_video])
        cmd.extend(loop_flag)
        cmd.extend(['-i', overlay_path])

    cmd.extend([
        '-filter_complex', filter_str,
        '-c:v', v_codec, '-preset', 'p4', '-tune', 'hq', '-pix_fmt', 'yuv420p',
        '-c:a', 'copy', output, '-y'
    ])
    
    return cmd

def run_render(cmd):
    """
    Executes the FFmpeg command and yields output for progress tracking.
    """
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        encoding='utf-8',
        errors='replace'
    )
    
    for line in process.stdout:
        yield line
        
    process.wait()
    return process.returncode
