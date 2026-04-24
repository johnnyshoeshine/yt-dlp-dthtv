import subprocess
import os

def get_ffmpeg_command(input_video, logo, overlay_path, output, settings):
    """
    Generates the FFmpeg command for branding a video with a logo and a periodic overlay.
    
    settings = { 
        'logo_pos': 'W-w-10:10', 
        'overlay_freq': 300, 
        'overlay_dur': 30, 
        'overlay_scale': 0.7, 
        'opacity': 1.0,
        'use_nvenc': True 
    }
    """
    v_codec = "h264_nvenc" if settings.get('use_nvenc', False) else "libx264"
    
    # Logic for looping: -ignore_loop for GIF, -stream_loop for Video
    is_gif = overlay_path.lower().endswith('.gif')
    loop_flag = ['-ignore_loop', '0'] if is_gif else ['-stream_loop', '-1']
    
    opacity = settings.get('opacity', 1.0)
    opacity_filter = f"format=rgba,colorchannelmixer=aa={opacity}"
    
    logo_pos = settings.get('logo_pos', 'W-w-10:10')
    overlay_scale = settings.get('overlay_scale', 0.7)
    overlay_freq = settings.get('overlay_freq', 300)
    overlay_dur = settings.get('overlay_dur', 30)
    
    # Build filter complex
    # 1. Overlay logo on top of input video
    # 2. Scale the overlay (GIF/Video) and apply opacity
    # 3. Apply temporal overlay (center aligned, enabled periodically)
    filter_str = (
        f"[0:v][1:v]overlay={logo_pos}[v_logo]; "
        f"[2:v]scale=iw*{overlay_scale}:-1,{opacity_filter}[ovl]; "
        f"[v_logo][ovl]overlay=(W-w)/2:(H-h)/2:enable='between(mod(t,{overlay_freq}),0,{overlay_dur})':shortest=1"
    )
    
    cmd = [
        'ffmpeg', '-hwaccel', 'cuda' if settings.get('use_nvenc', False) else 'auto',
        '-i', input_video, '-i', logo
    ]
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
    Executes the FFmpeg command and yields output for progress tracking (simplified for now).
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
