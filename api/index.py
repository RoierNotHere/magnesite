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
        # Clonamos el User-Agent exacto de un iPhone moderno con Safari
        ua_ios = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1'
        
        # Estructura de cabeceras nativas de iOS (Safari no usa sec-ch-ua, lo que nos simplifica el camuflaje)
        headers = {
            'User-Agent': ua_ios,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-cl,es;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://t.co/', # Simula que abrieron el link desde la app de Twitter/X
            'Connection': 'keep-alive',
            
            # Metadata de navegación para Safari Móvil
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'cross-site',
            
            'X-Requested-With': 'com.apple.mobilesafari'
        }

        # Una pausa un poco más corta pero muy aleatoria, típica de red móvil
        time.sleep(random.uniform(3.5, 7.2))

        try:
            print("[Prueba] Intentando camuflaje de iPhone/Safari...")
            # Forzamos un PoolManager estándar
            http = urllib3.PoolManager(cert_reqs='CERT_NONE')
            
            res = http.request('GET', url, headers=headers, timeout=30.0)
            print(f"[Resultado] HTTP Status: {res.status}")

            if res.status == 200:
                html_content = res.data.decode('utf-8', errors='ignore')
                soup = BeautifulSoup(html_content, "html.parser")
                
                # El selector exacto que extrajiste
                tag = soup.find(attrs={"data-test": "instrument-price-last"}) or \
                      soup.select_one('div[data-test="instrument-price-last"]') or \
                      soup.select_one('.text-5xl\/9')
                
                if tag:
                    valor_original = tag.get_text(strip=True)
                    print(f"[Éxito] Encontrado con perfil móvil: {valor_original}")
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
            fuente = "Caché móvil"
            status_api = "online"
        else:
            resultado_test = self.probar_medio_alternativo(url_rhi)
            
            if resultado_test.startswith("Exito_"):
                valor_final = resultado_test.split("_")[1]
                cache_rhi["precio"] = valor_final
                cache_rhi["timestamp"] = ahora
                fuente = "Investing via urllib3 (Perfil iOS)"
                status_api = "online"
            else:
                valor_final = resultado_test
                fuente = "Fallo en perfil móvil"
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
