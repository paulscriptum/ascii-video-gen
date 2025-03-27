from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import requests
from io import BytesIO
import os
from dotenv import load_dotenv
from openai import OpenAI
import logging
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:5173", "http://localhost:3000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "max_age": 3600
    }
})

# Настройка retry стратегии для requests
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("https://", adapter)
http.mount("http://", adapter)

# Инициализация клиента OpenAI
client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY')
)

# Классический набор символов для ASCII-арта в стиле BBS
ASCII_CHARS = '$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,"^`\'. '

def image_to_ascii(image_url, width=100):
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Downloading image from URL: {image_url} (attempt {attempt + 1}/{max_retries})")
            response = http.get(image_url, timeout=30)
            response.raise_for_status()
            
            logger.info("Image downloaded successfully")
            img = Image.open(BytesIO(response.content))
            
            # Конвертируем в оттенки серого и настраиваем контраст
            img = img.convert('L')
            # Увеличиваем контраст
            img = Image.eval(img, lambda x: min(255, max(0, int(2.0 * x - 255))))
            # Инвертируем изображение для правильного отображения
            img = Image.eval(img, lambda x: 255 - x)
            
            # Изменяем размер, сохраняя квадратные пропорции
            img = img.resize((width, width))
            
            pixels = list(img.getdata())
            ascii_str = ''
            
            # Создаем ASCII арт с более плотным расположением символов
            for i in range(width):
                for j in range(width):
                    pixel_value = pixels[i * width + j]
                    # Используем нелинейное отображение для лучшей детализации
                    char_index = int((pixel_value / 255) * (len(ASCII_CHARS) - 1))
                    # Добавляем пробел после каждого символа для компенсации прямоугольности
                    ascii_str += ASCII_CHARS[char_index] + ' '
                ascii_str += '\n'
            
            logger.info("ASCII conversion completed successfully")
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
def home():
    return "ASCII Art Generator API is running!"

@app.route('/api/generate', methods=['POST', 'OPTIONS'])
def generate_image():
    if request.method == 'OPTIONS':
        return '', 204

    try:
        logger.info("Received generate request")
        data = request.get_json()
        if not data:
            logger.error("No JSON data received")
            return jsonify({'error': 'No data provided'}), 400

        prompt = data.get('prompt')
        if not prompt:
            logger.error("No prompt provided")
            return jsonify({'error': 'No prompt provided'}), 400
            
        try:
            enhanced_prompt = f"low poly monochrome illustration of {prompt}, pixel art, high contrast black and white, black background, dramatic lighting, detailed linework, sharp edges, centered composition"
            logger.info(f"Generating image with enhanced prompt: {enhanced_prompt}")
            
            response = client.images.generate(
                model="dall-e-3",
                prompt=enhanced_prompt,
                n=1,
                size="1024x1024",
                quality="standard",
                response_format="url"
            )
            
            image_url = response.data[0].url
            logger.info(f"Image generated successfully: {image_url}")
            
            ascii_art = image_to_ascii(image_url)
            
            if ascii_art is None:
                logger.error("Failed to convert image to ASCII")
                return jsonify({'error': 'Failed to convert image to ASCII'}), 500
                
            logger.info("Successfully generated ASCII art")
            return jsonify({
                'ascii': ascii_art,
                'image_url': image_url
            })
            
        except Exception as e:
            logger.error(f"Error generating image: {str(e)}")
            return jsonify({'error': f'Error generating image: {str(e)}'}), 500
            
    except Exception as e:
        logger.error(f"Error in generate_image: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)