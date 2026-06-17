from http.server import BaseHTTPRequestHandler
import cloudscraper
from bs4 import BeautifulSoup
import json
import random
import time

# Cache global adaptada para RHI Magnesita
cache_rhi = {
    "datos": {},
    "timestamp": 0
}

class handler(BaseHTTPRequestHandler):

    def intentar_scrape(self, materiales):
        # Lista de configuraciones para rotar identidad
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        ]

        scraper = cloudscraper.create_scraper(
            delay=10,
            browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
        )
        
        resultados = {}
        
        for metal in materiales:
            time.sleep(random.uniform(2.0, 3.0))
            
            headers = {
                'User-Agent': random.choice(user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'es-ES,es;q=0.9',
                'Referer': 'https://www.google.com/',
                'Sec-Fetch-Mode': 'navigate'
            }

            try:
                res = scraper.get(metal["url"], headers=headers, timeout=15)
                if res.status_code == 200:
                    soup = BeautifulSoup(res.text, 'html.parser')
                    
                    elemento = soup.find(attrs={"data-test": "instrument-price-last"}) or \
                               soup.select_one('div[data-test="instrument-price-last"]') or \
                               soup.select_one('.text-5xl\/9')
                    
                    if elemento:
                        # --- NUEVA LÓGICA DE LIMPIEZA TOTAL ---
                        # Eliminamos primero las comas y luego los puntos por completo
                        valor_crudo = elemento.text.strip()
                        valor_numerico_puro = valor_crudo.replace(',', '').replace('.', '')
                        
                        resultados[metal["id"]] = valor_numerico_puro
                    else:
                        resultados[metal["id"]] = "No encontrado"
                else:
                    resultados[metal["id"]] = f"Error {res.status_code}"
            except Exception as e:
                resultados[metal["id"]] = f"Error: {str(e)}"
        
        return resultados

    def do_GET(self):
        global cache_rhi
        
        materiales_config = [
            {"id": "magnesita", "url": "https://es.investing.com/equities/rhi-ag"}
        ]
        
        ahora = time.time()
        TIEMPO_CACHE = 1800  # 30 minutos
        
        if cache_rhi["datos"] and (ahora - cache_rhi["timestamp"] < TIEMPO_CACHE):
            final_data = cache_rhi["datos"]
            fuente = "cache"
        else:
            final_data = self.intentar_scrape(materiales_config)
            cache_rhi["datos"] = final_data
            cache_rhi["timestamp"] = ahora
            fuente = "real-time"

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        res_json = {
            "rhi_data": final_data,
            "status": "online",
            "fuente": fuente,
            "timestamp": int(ahora)
        }
        
        self.wfile.write(json.dumps(res_json).encode('utf-8'))
