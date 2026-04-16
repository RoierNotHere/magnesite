import requests
import json
import time
import random
from http.server import BaseHTTPRequestHandler
import cloudscraper
from bs4 import BeautifulSoup

# Variable global para el Timer
cache_rhi = {
    "precio": None,
    "timestamp": 0
}

class handler(BaseHTTPRequestHandler):

    def obtener_precio_rhi(self, url):
        # 1. Configuramos el scraper
        scraper = cloudscraper.create_scraper(
            delay=15, # Aumentamos el delay inicial de cloudscraper
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )
        
        try:
            # Headers más realistas: simula que vienes de Google España
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
                'Referer': 'https://www.google.es/',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'cross-site',
                'Pragma': 'no-cache',
                'Cache-Control': 'no-cache',
            }
            
            # --- CAMBIO DE SLEEP ---
            # Pausa mucho más larga y errática (entre 3 y 7 segundos)
            # Esto ayuda a "enfriar" la IP antes de pedir el dato
            tiempo_espera = random.uniform(3.5, 7.2)
            print(f"Esperando {tiempo_espera:.2f} segundos para evitar detección...")
            time.sleep(tiempo_espera)
            
            res = scraper.get(url, headers=headers, timeout=30)
            
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                
                # Intentamos los selectores conocidos
                tag = soup.find("div", {"data-test": "instrument-price-last"}) or \
                      soup.select_one('span[data-test="instrument-price-last"]') or \
                      soup.find("span", {"id": "last_last"})
                
                if tag:
                    valor = tag.get_text(strip=True)
                    print(f"ÉXITO: Valor capturado -> {valor}")
                    return valor
                
                return "Tag_No_Encontrado"
            
            print(f"BLOQUEO DETECTADO: Código {res.status_code}")
            return f"Error_{res.status_code}"
            
        except Exception as e:
            print(f"ERROR EN PETICIÓN: {str(e)}")
            return "Error_Excepcion"

    def do_GET(self):
        global cache_rhi
        
        url_rhi = "https://es.investing.com/equities/rhi-ag"
        ahora = time.time()
        TIEMPO_CACHE = 7200 # 2 horas

        if cache_rhi["precio"] and (ahora - cache_rhi["timestamp"] < TIEMPO_CACHE):
            valor_final = cache_rhi["precio"]
            fuente = "Caché (Ahorro créditos/IP)"
        else:
            valor_final = self.obtener_precio_rhi(url_rhi)
            
            if "Error" not in valor_final and valor_final != "No_Encontrado":
                cache_rhi["precio"] = valor_final
                cache_rhi["timestamp"] = ahora
                fuente = "Investing Real-time"
            else:
                fuente = "Bloqueado por Investing"

        datos = {
            "empresa": "RHI Magnesita",
            "precio": valor_final,
            "moneda": "EUR",
            "fuente": fuente,
            "status": "online" if "Error" not in valor_final else "blocked"
        }

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(datos).encode('utf-8'))