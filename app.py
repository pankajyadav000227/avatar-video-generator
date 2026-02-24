from flask import Flask, render_template, request, jsonify, send_file
import pyttsx3
from PIL import Image, ImageDraw, ImageFont
import io
import os
from datetime import datetime
import subprocess
import platform

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max

# TTS engine setup
engine = pyttsx3.init()
engine.setProperty('rate', 150)
engine.setProperty('volume', 0.9)

def create_simple_avatar():
    """Create a simple animated avatar image using PIL"""
    # Create a simple cartoon avatar face
    img = Image.new('RGB', (400, 500), color='lightblue')
    draw = ImageDraw.Draw(img)
    
    # Face
    draw.ellipse([50, 50, 350, 450], fill='peachpuff', outline='black', width=3)
    
    # Eyes
    draw.ellipse([120, 140, 160, 180], fill='white', outline='black', width=2)
    draw.ellipse([240, 140, 280, 180], fill='white', outline='black', width=2)
    draw.ellipse([135, 155, 150, 170], fill='black')  # Left pupil
    draw.ellipse([255, 155, 270, 170], fill='black')  # Right pupil
    
    # Eyebrows
    draw.arc([120, 120, 160, 145], 0, 180, fill='brown', width=3)
    draw.arc([240, 120, 280, 145], 0, 180, fill='brown', width=3)
    
    # Nose
    draw.polygon([200, 200, 185, 230, 215, 230], fill='peachpuff', outline='black')
    
    # Mouth (smile)
    draw.arc([150, 280, 250, 350], 0, 180, fill='red', width=4)
    
    # Ears
    draw.ellipse([20, 180, 70, 280], fill='peachpuff', outline='black', width=2)
    draw.ellipse([330, 180, 380, 280], fill='peachpuff', outline='black', width=2)
    
    return img

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/generate', methods=['POST'])
def generate_video():
    try:
        data = request.json
        text = data.get('text', 'Hello, I am your talking avatar!')
        
        if not text or len(text.strip()) == 0:
            return jsonify({'error': 'Text cannot be empty'}), 400
        
        # Create temporary directory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        temp_dir = f'/tmp/avatar_{timestamp}'
        os.makedirs(temp_dir, exist_ok=True)
        
        audio_file = f'{temp_dir}/audio.wav'
        image_file = f'{temp_dir}/avatar.png'
        video_file = f'{temp_dir}/video.mp4'
        
        # Generate speech
        engine.save_to_file(text, audio_file)
        engine.runAndWait()
        
        # Create avatar image
        avatar_img = create_simple_avatar()
        avatar_img.save(image_file)
        
        # Create video using ffmpeg (simple approach - just combine image and audio)
        try:
            # Duration of audio in seconds (approximate)
            duration = len(text) / 150.0 + 0.5  # rough estimate
            
            # Use ffmpeg if available
            if platform.system() == 'Windows':
                cmd = f'ffmpeg -loop 1 -i "{image_file}" -i "{audio_file}" -c:v libx264 -c:a aac -shortest -y "{video_file}" -hide_banner -loglevel panic'
            else:
                cmd = f'ffmpeg -loop 1 -i {image_file} -i {audio_file} -c:v libx264 -c:a aac -shortest -y {video_file} -hide_banner -loglevel panic'
            
            result = subprocess.run(cmd, shell=True, capture_output=True, timeout=60)
            
            if result.returncode != 0 or not os.path.exists(video_file):
                # If ffmpeg fails, return audio file
                return send_file(audio_file, mimetype='audio/wav', as_attachment=True, download_name=f'avatar_audio_{timestamp}.wav')
            
            return send_file(video_file, mimetype='video/mp4', as_attachment=True, download_name=f'avatar_{timestamp}.mp4')
        
        except Exception as video_error:
            # Fallback: return audio file
            if os.path.exists(audio_file):
                return send_file(audio_file, mimetype='audio/wav', as_attachment=True, download_name=f'avatar_audio_{timestamp}.wav')
            return jsonify({'error': str(video_error)}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
