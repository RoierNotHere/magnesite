import json
import time
import random
from http.server import BaseHTTPRequestHandler
import requests
import cloudscraper
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

cache_rhi = {
    "precio": None,
    "timestamp": 0
}

class handler(BaseHTTPRequestHandler):

    def probar_estrategias(self, url):
        try:
            ua = UserAgent()
            ua_aleatorio = ua.random
        except:
            ua_aleatorio = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"

        # Mantenemos las dos estrategias para ver cuál rompe el 403 con este nuevo selector
        estrategia = "cloudscraper_avanzado" 
        
        headers = {
            'User-Agent': ua_aleatorio,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en-US;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.google.com/',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'cross-site'
        }

        # Pausas dinámicas
        for _ in range(random.randint(2, 4)):
            time.sleep(random.uniform(2.0, 4.0))

        try:
            if estrategia == "cloudscraper_avanzado":
                scraper = cloudscraper.create_scraper(
                    delay=20,
                    browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
                )
                res = scraper.get(url, headers=headers, timeout=30)
            else:
                session = requests.Session()
                session.get("https://www.google.com", headers={'User-Agent': ua_aleatorio}, timeout=10)
                time.sleep(random.uniform(2, 4))
                res = session.get(url, headers=headers, timeout=30)

            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                
                # --- NUEVA ESTRATEGIA DE BÚSQUEDA POR EL HTML REAL ---
                # Buscamos primero por el atributo exacto data-test o por la clase CSS específica
                tag = soup.find(attrs={"data-test": "instrument-price-last"}) or \
                      soup.select_one('div[data-test="instrument-price-last"]') or \
                      soup.select_one('.text-5xl\/9') or \
                      soup.find("span", {"id": "last_last"})

                if tag:
                    valor_original = tag.get_text(strip=True) # Trae "33,900"
                    
                    # LÓGICA DE FORMATO ADAPTADA:
                    # Como viene "33,900", si queremos que sea en cienes (33,90), 
                    # simplemente trabajamos el texto directo.
                    if ',' in valor_original:
                        # Si termina en '00' o similar, podemos manejarlo directamente como cadena
                        # Aquí cambiamos la coma por punto para verificar si es numérico y evitar caídas
                        valor_final = valor_original
                    else:
                        valor_final = valor_original.replace('.', ',')

                    print(f"[Scrap Éxito] Valor final procesado: {valor_final}")
                    return f"Exito_{valor_final}"
                
                return "Error_Tag_No_Encontrado"
                
            return f"Error_{res.status_code}"

        except Exception as e:
            return f"Error_Excepcion_{str(e)[:30]}"

    def do_GET(self):
        global cache_rhi
        
        url_rhi = "https://es.investing.com/equities/rhi-ag"
        ahora = time.time()
        TIEMPO_CACHE = 60 # 1 minuto para testear rápido

        if cache_rhi["precio"] and (ahora - cache_rhi["timestamp"] < TIEMPO_CACHE):
            valor_final = cache_rhi["precio"]
            fuente = "Caché activa"
        else:
            resultado_test = self.probar_estrategias(url_rhi)
            
            if resultado_test.startswith("Exito_"):
                valor_final = resultado_test.split("_")[1]
                cache_rhi["precio"] = valor_final
                cache_rhi["timestamp"] = ahora
                fuente = "Investing Conectado"
            else:
                valor_final = resultado_test
                fuente = "Fallo en la prueba"

        datos = {
            "empresa": "RHI Magnesita",
            "precio": valor_final,
            "fuente": fuente,
            "status": "online" if resultado_test.startswith("Exito_") else "blocked"
        }

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(datos).encode('utf-8'))
