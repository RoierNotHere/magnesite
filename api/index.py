import json
import time
import random
from http.server import BaseHTTPRequestHandler
import urllib3
from bs4 import BeautifulSoup

cache_rhi = {
    "precio": None,
    "timestamp": 0
}

class handler(BaseHTTPRequestHandler):

    def probar_medio_alternativo(self, url):
        # Fijamos un único User-Agent ultra detallado para que coincida con los metadatos de abajo
        ua_exacto = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
        
        # Cabeceras optimizadas con las firmas obligatorias de Cloudflare (Sec-Fetch y sec-ch-ua)
        headers = {
            'User-Agent': ua_exacto,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.google.com/',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            
            # --- FIRMAS METADATA REALES DE CHROME 125 ---
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'cross-site',
            'Sec-Fetch-User': '?1',
            'sec-ch-ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-ch-ua-platform-version': '"10.0.0"',
            
            'Cache-Control': 'max-age=0',
            'DNT': '1'
        }

        # Aplicamos una pausa humana antes de lanzar la conexión
        time.sleep(random.uniform(4.5, 8.5))

        try:
            print("[Prueba] Conectando con cabeceras Sec-Ch-Ua avanzadas...")
            # Mantenemos el PoolManager limpio
            http = urllib3.PoolManager(cert_reqs='CERT_NONE')
            
            res = http.request('GET', url, headers=headers, timeout=30.0)
            print(f"[Resultado] HTTP Status: {res.status}")

            if res.status == 200:
                html_content = res.data.decode('utf-8', errors='ignore')
                soup = BeautifulSoup(html_content, "html.parser")
                
                # El selector que encontraste
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
            return f"Error_Excepcion_{str(e)[:40]}"

    def do_GET(self):
        global cache_rhi
        
        url_rhi = "https://es.investing.com/equities/rhi-ag"
        ahora = time.time()
        TIEMPO_CACHE = 45 

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
                fuente = "Investing via urllib3 (Headers Chrome 125)"
                status_api = "online"
            else:
                valor_final = resultado_test
                fuente = "Fallo en las cabeceras"
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
