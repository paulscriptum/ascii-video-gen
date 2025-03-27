import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: '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',
  dangerouslyAllowBrowser: true,
  baseURL: 'https://api.openai.com/v1' // Исправляем URL на правильный
});

export async function generateImage(prompt: string): Promise<string> {
  try {
    console.log('Generating image with prompt:', prompt);
    const response = await openai.images.generate({
      model: "dall-e-3",
      prompt: prompt,
      n: 1,
      size: "1024x1024",
      quality: "standard",
      response_format: "url",
    });

    if (!response.data?.[0]?.url) {
      throw new Error('No image URL received from OpenAI');
    }

    console.log('Generated image URL:', response.data[0].url);
    return response.data[0].url;
  } catch (error: any) {
    console.error('Error generating image:', error);
    throw new Error(error.message || 'Failed to generate image');
  }
}