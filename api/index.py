import requests
import json
import time
import random
from http.server import BaseHTTPRequestHandler
import cloudscraper
from bs4 import BeautifulSoup

# Variable global para el Timer (Ahorro de peticiones)
cache_rhi = {
    "precio": None,
    "timestamp": 0
}

class handler(BaseHTTPRequestHandler):

    def obtener_precio_rhi(self, url):
        # 1. Configuramos el scraper para saltar protecciones
        scraper = cloudscraper.create_scraper(
            delay=10, 
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
                'Referer': 'https://www.google.com/'
            }
            
            # Pausa aleatoria para no ser detectado
            time.sleep(random.uniform(1.5, 3.0))
            
            res = scraper.get(url, headers=headers, timeout=20)
            
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                
                # Selectores específicos para el precio en Investing
                # 1. Intenta por data-test (el más confiable hoy)
                # 2. Intenta por la clase de precio de mercado
                tag = soup.find("div", {"data-test": "instrument-price-last"}) or \
                      soup.select_one('span[data-test="instrument-price-last"]') or \
                      soup.find("span", {"id": "last_last"})
                
                if tag:
                    valor = tag.get_text(strip=True)
                    print(f"VALOR RHI CAPTURADO: {valor}")
                    return valor
                
                return "No_Encontrado"
            
            return f"Error_{res.status_code}"
            
        except Exception as e:
            print(f"Error de excepción: {str(e)}")
            return "Error_Excepcion"

    def do_GET(self):
        global cache_rhi
        
        url_rhi = "https://es.investing.com/equities/rhi-ag"
        ahora = time.time()
        TIEMPO_CACHE = 7200 # 2 horas

        # --- LÓGICA DEL TIMER (Mismo formato que antes) ---
        if cache_rhi["precio"] and (ahora - cache_rhi["timestamp"] < TIEMPO_CACHE):
            print("Usando precio de RHI guardado en caché.")
            valor_final = cache_rhi["precio"]
            fuente = "Caché"
        else:
            print("Consultando Investing.com por nuevo precio...")
            valor_final = self.obtener_precio_rhi(url_rhi)
            
            # Solo guardamos en caché si la respuesta es un número y no un error
            if "Error" not in valor_final and valor_final != "No_Encontrado":
                cache_rhi["precio"] = valor_final
                cache_rhi["timestamp"] = ahora
                fuente = "Investing Real-time"
            else:
                fuente = "Intento Fallido / Bloqueado"

        # Respuesta final
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