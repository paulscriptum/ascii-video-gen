import React, { useState } from 'react';
import { Terminal, MonitorUp, Loader2, RefreshCw } from 'lucide-react';
import axios from 'axios';

const API_URL = 'http://127.0.0.1:5000';

const api = axios.create({
  baseURL: API_URL,
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json'
  }
});

function App() {
  const [prompt, setPrompt] = useState('');
  const [asciiArt, setAsciiArt] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [retryCount, setRetryCount] = useState(0);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      console.log('Sending request to:', `${API_URL}/api/generate`);
      const response = await api.post('/api/generate', {
        prompt: prompt
      });
      
      if (!response.data?.ascii) {
        throw new Error('Не получен ASCII-арт от сервера');
      }
      
      setAsciiArt(response.data.ascii);
      setRetryCount(0);
    } catch (err: any) {
      console.error('Error details:', err);
      let errorMessage = 'Произошла ошибка. Пожалуйста, попробуйте снова.';
      
      if (err.response) {
        errorMessage = `Ошибка сервера: ${err.response.data?.error || err.response.status}`;
      } else if (err.request) {
        errorMessage = 'Сервер недоступен. Пожалуйста, подождите немного и попробуйте снова.';
      } else {
        errorMessage = err.message || 'Неизвестная ошибка';
      }
      
      setError(errorMessage);
      setRetryCount(prev => prev + 1);
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = () => {
    if (prompt) {
      handleSubmit(new Event('submit') as any);
    }
  };

  return (
    <div className="min-h-screen bg-black text-green-500 p-4 font-mono">
      <div className="max-w-4xl mx-auto">
        <header className="flex items-center gap-2 mb-8">
          <Terminal className="w-8 h-8" />
          <h1 className="text-2xl">ASCII Art Генератор</h1>
        </header>

        <div className="border border-green-500 p-6 rounded-lg mb-8">
          <form onSubmit={handleSubmit} className="flex gap-4">
            <input
              type="text"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Опишите изображение..."
              className="flex-1 bg-black border border-green-500 p-2 rounded text-green-500 focus:outline-none focus:ring-1 focus:ring-green-500"
            />
            <button
              type="submit"
              disabled={loading || !prompt}
              className="border border-green-500 px-4 py-2 rounded hover:bg-green-500 hover:text-black transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Генерация...
                </>
              ) : (
                <>
                  <MonitorUp className="w-4 h-4" />
                  Создать
                </>
              )}
            </button>
          </form>
        </div>

        {error && (
          <div className="text-red-500 mb-4 p-4 border border-red-500 rounded flex items-center justify-between">
            <span>{error}</span>
            <button
              onClick={handleRetry}
              className="flex items-center gap-2 hover:text-red-300 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              Повторить
            </button>
          </div>
        )}

        <div className="relative aspect-square w-full border border-green-500 rounded-lg overflow-hidden bg-black">
          <div className="absolute inset-0 p-4">
            <div className="w-full h-full overflow-auto">
              <pre className="font-mono text-[0.5rem] leading-[0.5rem] tracking-[0.1em] whitespace-pre">
                {loading ? (
                  <div className="flex items-center justify-center h-full">
                    <Loader2 className="w-8 h-8 animate-spin" />
                  </div>
                ) : asciiArt ? (
                  asciiArt
                ) : (
                  <div className="text-center text-green-500/50 h-full flex items-center justify-center text-base leading-normal">
                    ASCII арт появится здесь...
                  </div>
                )}
              </pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;