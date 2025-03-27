import tkinter as tk
from tkinter import ttk, scrolledtext
import requests
from PIL import Image
from io import BytesIO
import os
from dotenv import load_dotenv
from openai import OpenAI
import logging
import threading
import webbrowser
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Инициализация OpenAI клиента
client = OpenAI(
    api_key='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',
    base_url="https://api.openai.com/v1"
)

ASCII_CHARS = '@#$%=+~-:. '

# Создание Flask приложения
app = Flask(__name__)
CORS(app)

# Настройка retry стратегии
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("https://", adapter)
http.mount("http://", adapter)

def image_to_ascii(image_url, width=100):
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Downloading image from URL: {image_url} (attempt {attempt + 1}/{max_retries})")
            response = http.get(image_url, timeout=30)
            response.raise_for_status()
            
            img = Image.open(BytesIO(response.content))
            img = img.convert('L')
            aspect_ratio = img.height / img.width
            height = int(width * aspect_ratio)
            img = img.resize((width, height))
            
            pixels = list(img.getdata())
            ascii_str = ''
            
            for i in range(height):
                for j in range(width):
                    pixel_value = pixels[i * width + j]
                    ascii_str += ASCII_CHARS[pixel_value * (len(ASCII_CHARS) - 1) // 255]
                ascii_str += '\n'
            
            return ascii_str
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading image (attempt {attempt + 1}): {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                return None
        except Exception as e:
            logger.error(f"Error converting image to ASCII: {str(e)}")
            return None

@app.route('/')
def serve_static():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ASCII Art Generator</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');
            
            body {
                background-color: black;
                color: #00ff00;
                font-family: 'VT323', monospace;
                margin: 0;
                padding: 20px;
                min-height: 100vh;
                -webkit-font-smoothing: none;
                -moz-osx-font-smoothing: none;
            }
            
            .container {
                max-width: 800px;
                margin: 0 auto;
            }
            
            .header {
                display: flex;
                align-items: center;
                gap: 10px;
                margin-bottom: 20px;
            }
            
            .input-container {
                display: flex;
                gap: 10px;
                margin-bottom: 20px;
            }
            
            input {
                flex: 1;
                background: black;
                border: 1px solid #00ff00;
                color: #00ff00;
                padding: 10px;
                font-family: 'VT323', monospace;
                font-size: 16px;
            }
            
            button {
                background: black;
                border: 1px solid #00ff00;
                color: #00ff00;
                padding: 10px 20px;
                cursor: pointer;
                font-family: 'VT323', monospace;
                font-size: 16px;
                transition: all 0.3s;
            }
            
            button:hover {
                background: #00ff00;
                color: black;
            }
            
            button:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }
            
            .output {
                border: 1px solid #00ff00;
                padding: 20px;
                min-height: 400px;
                white-space: pre;
                font-family: monospace;
                overflow: auto;
            }
            
            .error {
                color: red;
                border: 1px solid red;
                padding: 10px;
                margin-bottom: 20px;
            }
            
            @keyframes flicker {
                0% { opacity: 0.97; }
                5% { opacity: 0.95; }
                10% { opacity: 0.97; }
                15% { opacity: 0.94; }
                20% { opacity: 0.98; }
                50% { opacity: 0.95; }
                80% { opacity: 0.98; }
                100% { opacity: 0.96; }
            }
            
            body {
                animation: flicker 0.15s infinite;
                position: relative;
            }
            
            body::before {
                content: " ";
                display: block;
                position: absolute;
                top: 0;
                left: 0;
                bottom: 0;
                right: 0;
                background: linear-gradient(
                    rgba(18, 16, 16, 0) 50%,
                    rgba(0, 0, 0, 0.25) 50%
                );
                background-size: 100% 2px;
                pointer-events: none;
                z-index: 2;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>ASCII Art Generator</h1>
            </div>
            
            <div class="input-container">
                <input type="text" id="prompt" placeholder="Опишите изображение...">
                <button onclick="generateArt()" id="generateBtn">Создать</button>
            </div>
            
            <div id="error" class="error" style="display: none;"></div>
            <div id="output" class="output">ASCII арт появится здесь...</div>
        </div>
        
        <script>
            async function generateArt() {
                const prompt = document.getElementById('prompt').value;
                const output = document.getElementById('output');
                const error = document.getElementById('error');
                const generateBtn = document.getElementById('generateBtn');
                
                if (!prompt) return;
                
                generateBtn.disabled = true;
                output.textContent = 'Генерация...';
                error.style.display = 'none';
                
                try {
                    const response = await fetch('/api/generate', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ prompt }),
                    });
                    
                    const data = await response.json();
                    
                    if (data.error) {
                        throw new Error(data.error);
                    }
                    
                    output.textContent = data.ascii;
                } catch (err) {
                    error.textContent = err.message;
                    error.style.display = 'block';
                    output.textContent = 'ASCII арт появится здесь...';
                } finally {
                    generateBtn.disabled = false;
                }
            }
            
            document.getElementById('prompt').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    generateArt();
                }
            });
        </script>
    </body>
    </html>
    """

@app.route('/api/generate', methods=['POST'])
def generate_image():
    try:
        data = request.get_json()
        if not data or 'prompt' not in data:
            return jsonify({'error': 'No prompt provided'}), 400
            
        prompt = data['prompt']
        enhanced_prompt = f"{prompt}, white background, high contrast, clear details, strong lighting"
        
        try:
            response = client.images.generate(
                model="dall-e-3",
                prompt=enhanced_prompt,
                n=1,
                size="1024x1024",
                quality="standard",
                response_format="url"
            )
            
            image_url = response.data[0].url
            ascii_art = image_to_ascii(image_url)
            
            if ascii_art is None:
                return jsonify({'error': 'Failed to convert image to ASCII'}), 500
                
            return jsonify({
                'ascii': ascii_art,
                'image_url': image_url
            })
            
        except Exception as e:
            logger.error(f"Error generating image: {str(e)}")
            return jsonify({'error': str(e)}), 500
            
    except Exception as e:
        logger.error(f"Error in generate_image: {str(e)}")
        return jsonify({'error': str(e)}), 500

def open_browser():
    webbrowser.open('http://localhost:5000')

if __name__ == '__main__':
    # Открываем браузер в отдельном потоке
    threading.Timer(1.5, open_browser).start()
    # Запускаем Flask сервер
    app.run(host='0.0.0.0', port=5000, debug=True)