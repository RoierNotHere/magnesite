import json
import time
import random
from http.server import BaseHTTPRequestHandler
import urllib3
from bs4 import BeautifulSoup

# Cache global temporal corta para pruebas rápidas
cache_rhi = {
    "precio": None,
    "timestamp": 0
}

class handler(BaseHTTPRequestHandler):

    def probar_medio_alternativo(self, url):
        # Lista local fija para evitar que se caiga el servidor por dependencias externas
        user_agents_locales = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0'
        ]
        
        headers = {
            'User-Agent': random.choice(user_agents_locales),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en-US;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.google.com/',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'cross-site'
        }

        # Pequeña pausa aleatoria antes de conectar
        time.sleep(random.uniform(3.0, 6.0))

        try:
            print("[Prueba] Conectando mediante PoolManager de urllib3...")
            # Creamos un gestor de conexiones limpio sin rastro de librerías comunes de bots
            http = urllib3.PoolManager(cert_reqs='CERT_NONE') # Evita problemas raros de SSL corporativos
            
            res = http.request('GET', url, headers=headers, timeout=25.0)
            print(f"[Resultado] HTTP Status: {res.status}")

            if res.status == 200:
                # Decodificamos la respuesta HTML
                html_content = res.data.decode('utf-8', errors='ignore')
                soup = BeautifulSoup(html_content, "html.parser")
                
                # Buscamos exactamente con el selector que me diste
                tag = soup.find(attrs={"data-test": "instrument-price-last"}) or \
                      soup.select_one('div[data-test="instrument-price-last"]') or \
                      soup.select_one('.text-5xl\/9')
                
                if tag:
                    valor_original = tag.get_text(strip=True)
                    print(f"[Éxito] Encontrado: {valor_original}")
                    return f"Exito_{valor_original}"
                
                return "Error_Tag_No_Encontrado"
                
            return f"Error_{res.status}"

        except Exception as e:
            # Captura el error exacto para mostrarlo en el JSON si algo vuelve a fallar
            return f"Error_Excepcion_{str(e)[:40]}"

    def do_GET(self):
        global cache_rhi
        
        url_rhi = "https://es.investing.com/equities/rhi-ag"
        ahora = time.time()
        TIEMPO_CACHE = 45 # 45 segundos para pruebas fluidas

        if cache_rhi["precio"] and (ahora - cache_rhi["timestamp"] < TIEMPO_CACHE):
            valor_final = cache_rhi["precio"]
            fuente = "Caché de contingencia"
            status_api = "online"
        else:
            resultado_test = self.probar_medio_alternativo(url_rhi)
            
            if resultado_test.startswith("Exito_"):
                valor_final = resultado_test.split("_")[1]
                cache_rhi["precio"] = valor_final
                cache_rhi["timestamp"] = ahora
                fuente = "Investing via urllib3"
                status_api = "online"
            else:
                valor_final = resultado_test  # Muestra el código de error en el campo precio
                fuente = "Fallo en el nuevo medio"
                status_api = "blocked"

        datos = {
            "empresa": "RHI Magnesita",
            "precio": valor_final,
            "fuente": fuente,
            "status": status_api
        }

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(datos).encode('utf-8'))
