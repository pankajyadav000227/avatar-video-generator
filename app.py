from flask import Flask, render_template, request, jsonify, send_file
import pyttsx3
import cv2
import numpy as np
from PIL import Image, ImageDraw
import io
import os
from datetime import datetime
import wave

app = Flask(__name__)

# TTS engine setup
engine = pyttsx3.init()
engine.setProperty('rate', 150)
engine.setProperty('volume', 0.9)

def text_to_speech(text, output_path):
    """Convert text to speech using pyttsx3"""
    engine.save_to_file(text, output_path)
    engine.runAndWait()
    return output_path

def create_talking_avatar(audio_path, avatar_image_path, output_path):
    """Create talking avatar video from audio and static image"""
    # Load audio properties
    audio = wave.open(audio_path, 'rb')
    frames = audio.readframes(audio.getnframes())
    audio.close()
    
    # Load avatar image
    avatar = cv2.imread(avatar_image_path)
    height, width = avatar.shape[:2]
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, 24, (width, height))
    
    # Simple animation: simulate talking by slightly modifying avatar each frame
    total_frames = len(frames) // 4  # Convert byte frames to audio frames
    
    for i in range(max(total_frames, 60)):
        frame = avatar.copy()
        
        # Add simple mouth animation
        mouth_y = int(height * 0.65)
        mouth_x = int(width * 0.5)
        
        # Oscillating mouth effect
        mouth_height = int(15 * abs(np.sin(i * 0.1)))
        cv2.ellipse(frame, (mouth_x, mouth_y), (15, mouth_height), 0, 0, 180, (0, 0, 255), 2)
        
        # Add eye blink effect
        if (i // 10) % 2 == 0:
            cv2.line(frame, (int(width*0.35), int(height*0.35)), (int(width*0.35)+10, int(height*0.35)), (0, 0, 0), 2)
            cv2.line(frame, (int(width*0.65), int(height*0.35)), (int(width*0.65)+10, int(height*0.35)), (0, 0, 0), 2)
        
        out.write(frame)
    
    out.release()
    return output_path

def create_simple_avatar():
    """Create a simple avatar image using PIL"""
    # Create a simple cartoon avatar face
    img = Image.new('RGB', (300, 400), color='lightblue')
    draw = ImageDraw.Draw(img)
    
    # Face
    draw.ellipse([50, 50, 250, 350], fill='peachpuff', outline='black', width=3)
    
    # Eyes
    draw.ellipse([100, 120, 130, 150], fill='white', outline='black', width=2)
    draw.ellipse([170, 120, 200, 150], fill='white', outline='black', width=2)
    draw.ellipse([110, 130, 120, 140], fill='black')  # Left pupil
    draw.ellipse([180, 130, 190, 140], fill='black')  # Right pupil
    
    # Nose
    draw.polygon([150, 160, 140, 180, 160, 180], fill='peachpuff', outline='black')
    
    # Mouth (neutral)
    draw.arc([120, 200, 180, 240], 0, 180, fill='red', width=3)
    
    # Ears
    draw.ellipse([30, 150, 60, 200], fill='peachpuff', outline='black', width=2)
    draw.ellipse([240, 150, 270, 200], fill='peachpuff', outline='black', width=2)
    
    return img

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/generate', methods=['POST'])
def generate_video():
    try:
        data = request.json
        text = data.get('text', 'Hello, I am your talking avatar!')
        
        # Create temporary files
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        audio_path = f'/tmp/audio_{timestamp}.wav'
        avatar_path = f'/tmp/avatar_{timestamp}.png'
        video_path = f'/tmp/video_{timestamp}.mp4'
        
        # Generate speech
        text_to_speech(text, audio_path)
        
        # Create avatar
        avatar_img = create_simple_avatar()
        avatar_img.save(avatar_path)
        
        # Create video
        create_talking_avatar(audio_path, avatar_path, video_path)
        
        # Return video as download
        return send_file(video_path, mimetype='video/mp4', as_attachment=True, download_name=f'avatar_{timestamp}.mp4')
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
