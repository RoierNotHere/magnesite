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
        # 1. Forzamos TLS real para romper el bloqueo de Cloudflare en data centers
        scraper = cloudscraper.create_scraper(
            delay=25, 
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        
        try:
            # 2. Lista de User-Agents modernos para ir rotando si uno falla
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0'
            ]
            
            # 3. Reconstrucción dinámica de headers limpios
            headers = {
                'User-Agent': random.choice(user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': 'https://www.google.com.gt/', # Simula búsqueda desde Guatemala
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'cross-site',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0'
            }
            
            # Pausa de seguridad más agresiva (entre 8 y 14 segundos)
            pausa = random.uniform(8.0, 14.0)
            print(f"Pausando {pausa:.2f}s para evitar el 403...")
            time.sleep(pausa)
            
            res = scraper.get(url, headers=headers, timeout=45)
            
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                
                # Lista expandida de selectores por si reestructuraron la página
                tag = soup.find("div", {"data-test": "instrument-price-last"}) or \
                      soup.select_one('span[data-test="instrument-price-last"]') or \
                      soup.find("span", {"id": "last_last"}) or \
                      soup.select_one('.instrument-price_last__KQ3Z3') # Selector dinámico alterno
                
                if tag:
                    # Lógica limpia sin .00 forzados
                    valor_original = tag.get_text(strip=True).replace(',', '')
                    valor_final = valor_original.replace('.', ',')
                    print(f"VALOR SCRAP COMPLETADO: {valor_final}")
                    return valor_final
                
                return "Tag_No_Encontrado"
            
            print(f"BLOQUEO: Código {res.status_code}")
            return f"Error_{res.status_code}"
            
        except Exception as e:
            print(f"Excepción: {str(e)}")
            return "Error_Excepcion"

    def do_GET(self):
        global cache_rhi
        
        url_rhi = "https://es.investing.com/equities/rhi-ag"
        ahora = time.time()
        TIEMPO_CACHE = 7200 # 2 horas

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
                fuente = "Error de Bloqueo"

        datos = {
            "empresa": "RHI Magnesita",
            "precio": valor_final,
            "fuente": fuente,
            "status": "online" if "Error" not in valor_final else "blocked"
        }

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(datos).encode('utf-8'))
