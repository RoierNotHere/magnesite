import requests
import json
import time
import random
from http.server import BaseHTTPRequestHandler
import cloudscraper
from bs4 import BeautifulSoup

# Cache global para proteger la IP y evitar bloqueos por repetición
cache_rhi = {
    "precio": None,
    "timestamp": 0
}

class handler(BaseHTTPRequestHandler):

    def obtener_precio_rhi(self, url):
        # 1. Configuramos el scraper con el delay alto que nos funcionó
        scraper = cloudscraper.create_scraper(
            delay=20, 
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        
        try:
            # 2. Headers de camuflaje total (los que saltan el 403)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7',
                'Referer': 'https://www.google.com/',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
                'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
                'sec-ch-ua-platform': '"Windows"',
                'Cookie': 'edition_redirect=1; gtm_id=GTM-PG97WS; _ga=GA1.2.123456789.123456789;'
            }
            
            # --- PAUSA HUMANA ---
            pausa = random.uniform(6.0, 11.0)
            print(f"Iniciando pausa de {pausa:.2f}s para RHI...")
            time.sleep(pausa)
            
            res = scraper.get(url, headers=headers, timeout=40)
            
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                
                # Selectores que me pasaste para Magnesita
                tag = soup.find("div", {"data-test": "instrument-price-last"}) or \
                      soup.select_one('span[data-test="instrument-price-last"]') or \
                      soup.find("span", {"id": "last_last"})
                
                if tag:
                    # --- LÓGICA DE FORMATO: COMA EN ÚLTIMOS 2 DÍGITOS ---
                    # Limpiamos comas o puntos que traiga la web
                    valor_sucio = tag.get_text(strip=True).replace(',', '')
                    
                    try:
                        numero = float(valor_sucio)
                        # Forzamos 2 decimales y ponemos la coma
                        valor_final = "{:.2f}".format(numero).replace('.', ',')
                        print(f"VALOR RHI CAPTURADO: {valor_final}")
                        return valor_final
                    except:
                        return valor_sucio
                
                return "Tag_No_Encontrado"
            
            print(f"BLOQUEO RHI: Status {res.status_code}")
            return f"Error_{res.status_code}"
            
        except Exception as e:
            return "Error_Excepcion"

    def do_GET(self):
        global cache_rhi
        
        # Link de Magnesita (RHI)
        url_rhi = "https://es.investing.com/equities/rhi-ag"
        ahora = time.time()
        TIEMPO_CACHE = 7200 # 2 horas

        # Lógica del Timer
        if cache_rhi["precio"] and (ahora - cache_rhi["timestamp"] < TIEMPO_CACHE):
            valor_final = cache_rhi["precio"]
            fuente = "Caché"
        else:
            valor_final = self.obtener_precio_rhi(url_rhi)
            
            if "Error" not in valor_final and valor_final != "Tag_No_Encontrado":
                cache_rhi["precio"] = valor_final
                cache_rhi["timestamp"] = ahora
                fuente = "Investing Actualizado"
            else:
                fuente = "Error / Bloqueo"

        # Respuesta final del JSON
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
