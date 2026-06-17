import requests
import json
import time
import random
from http.server import BaseHTTPRequestHandler
import cloudscraper
from bs4 import BeautifulSoup

# Cache global para proteger la IP
cache_rhi = {
    "precio": None,
    "timestamp": 0
}

class handler(BaseHTTPRequestHandler):

    def obtener_precio_rhi(self, url):
        # Subimos el delay inicial de cloudscraper para que negocie el JavaScript más lento
        scraper = cloudscraper.create_scraper(
            delay=30, 
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        
        try:
            # Headers ultra-modernos imitando Chrome 126 con procedencia de red social
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'es-419,es;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br, zstd', # Añadimos zstd que lo usan los Chrome nuevos
                'Referer': 'https://www.linkedin.com/', # Cambiamos el origen a LinkedIn
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'cross-site',
                'Sec-Fetch-User': '?1',
                'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'Priority': 'u=0, i' # Header de prioridad nuevo en Chrome
            }
            
            # Pausa humana más larga e impredecible
            pausa = random.uniform(10.1, 16.4)
            print(f"Pausando {pausa:.2f}s con estrategia LinkedIn...")
            time.sleep(pausa)
            
            res = scraper.get(url, headers=headers, timeout=50)
            
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html
