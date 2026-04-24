import subprocess
import os
import struct

def mosh_video(input_path, output_path, frequency=0.1, duration=5):
    """
    Experimental datamoshing by removing I-frames from an MPEG4 AVI stream.
    frequency: probability of triggering a mosh at an I-frame (0.0 to 1.0)
    duration: how many I-frames to skip once a mosh is triggered.
    """
    
    # 1. Convert to moshable AVI (MPEG4)
    # We use a large GOP to have fewer I-frames to work with, or a small one to have more control.
    # qscale:v 1 for high quality. -an for no audio (datamoshing audio is messy)
    temp_avi = "temp_moshable.avi"
    cmd_prep = [
        'ffmpeg', '-y', '-i', input_path,
        '-vcodec', 'mpeg4', '-f', 'avi',
        '-qscale:v', '2', '-g', '30', '-an',
        temp_avi
    ]
    subprocess.run(cmd_prep, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        with open(temp_avi, 'rb') as f:
            data = f.read()

        # AVI parsing (very basic)
        # We look for '00dc' chunks which are video data in MPEG4 AVI
        
        # This is a very simplified approach: 
        # In MPEG4, an I-frame (keyframe) starts with a specific byte pattern in the VOP header.
        # But even simpler: AVI files have an index at the end (idx1) that marks keyframes.
        # However, we can also just look for the VOP header: 00 00 01 B6
        # The next 2 bits after B6 tell the frame type: 00 = I-frame, 01 = P-frame, 10 = B-frame.
        
        # A more reliable way for "true" datamoshing is to use a library or a very specific bitstream parser.
        # Since I am an AI agent, I will implement a robust-enough byte-level manipulator.
        
        pos = 0
        output_data = bytearray()
        
        # Copy header (until 'movi' list)
        movi_pos = data.find(b'movi')
        if movi_pos == -1:
            raise ValueError("Not a valid AVI file (no movi chunk)")
        
        output_data.extend(data[:movi_pos+4])
        pos = movi_pos + 4
        
        mosh_counter = 0
        
        while pos < len(data) - 8:
            chunk_id = data[pos:pos+4]
            try:
                chunk_size = struct.unpack('<I', data[pos+4:pos+8])[0]
            except Exception:
                break
            
            full_chunk_size = 8 + chunk_size
            if full_chunk_size % 2 != 0: full_chunk_size += 1 # AVI chunks are word-aligned
            
            if chunk_id == b'00dc':
                chunk_data = data[pos:pos+full_chunk_size]
                # Check if it's an I-frame (VOP start 00 00 01 B6, type 00)
                vop_pos = chunk_data.find(b'\x00\x00\x01\xb6')
                if vop_pos != -1 and vop_pos + 4 < len(chunk_data):
                    vop_type = (chunk_data[vop_pos+4] >> 6) & 0x03
                    if vop_type == 0: # I-frame
                        if mosh_counter > 0:
                            mosh_counter -= 1
                            # Skip this I-frame chunk to cause moshing
                            pass 
                        elif pos > movi_pos + 2000 and frequency > 0: # Skip first few frames
                            import random
                            if random.random() < frequency:
                                mosh_counter = int(duration)
                                # Skip this one too
                                pass
                            else:
                                output_data.extend(chunk_data)
                        else:
                            output_data.extend(chunk_data)
                    else:
                        output_data.extend(chunk_data)
                else:
                    output_data.extend(chunk_data)
            else:
                output_data.extend(data[pos:pos+full_chunk_size])
            
            pos += full_chunk_size
            if pos >= len(data): break
            if chunk_id == b'idx1': break

        # Note: Removing frames from AVI without updating the index (idx1) 
        # makes the file "broken" but most players (and FFmpeg) will still try to play it,
        # which is EXACTLY what we want for datamoshing.
        
        with open("glitched.avi", "wb") as f:
            f.write(output_data)
            
        # 3. Convert back to MP4
        cmd_final = [
            'ffmpeg', '-y', '-i', 'glitched.avi',
            '-vcodec', 'libx264', '-pix_fmt', 'yuv420p',
            output_path
        ]
        subprocess.run(cmd_final, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
    finally:
        if os.path.exists(temp_avi): os.remove(temp_avi)
        if os.path.exists("glitched.avi"): os.remove("glitched.avi")

if __name__ == "__main__":
    # Test
    pass
