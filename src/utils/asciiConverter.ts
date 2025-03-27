import Jimp from 'jimp';
import { Buffer } from 'node:buffer';

const ASCII_CHARS = '@#$%=+~-:. ';

/**
 * Converts an image to ASCII art
 * @param imageSource URL, File path, Buffer, or Jimp instance
 * @param width Maximum width of the ASCII art (number of characters)
 * @returns ASCII art string
 */
export async function imageToAscii(
  imageSource: string | Buffer | Jimp, 
  width: number = 100
): Promise<string> {
  try {
    // Load the image using jimp
    let image: Jimp;
    
    if (typeof imageSource === 'string') {
      // Handle URL or file path
      image = await Jimp.read(imageSource);
    } else if (Buffer.isBuffer(imageSource)) {
      // Handle Buffer
      image = await Jimp.read(imageSource);
    } else {
      // Handle Jimp instance
      image = imageSource;
    }
    
    // Resize the image to the specified width while maintaining aspect ratio
    image.resize(width, Jimp.AUTO);
    
    let asciiArt = '';
    
    // Process each pixel
    for (let y = 0; y < image.getHeight(); y++) {
      for (let x = 0; x < image.getWidth(); x++) {
        // Get pixel color
        const pixel = Jimp.intToRGBA(image.getPixelColor(x, y));
        
        // Calculate brightness
        const brightness = (pixel.r + pixel.g + pixel.b) / 3;
        
        // Map brightness to ASCII character
        const charIndex = Math.floor((brightness / 255) * (ASCII_CHARS.length - 1));
        asciiArt += ASCII_CHARS[charIndex];
      }
      asciiArt += '\n';
    }
    
    return asciiArt;
  } catch (error) {
    console.error('Error converting image to ASCII:', error);
    throw new Error('Error converting image');
  }
}