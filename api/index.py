import json
import time
from http.server import BaseHTTPRequestHandler
import requests
from bs4 import BeautifulSoup

# Cache global para cuidar tus 5,000 créditos gratis mensuales
cache_rhi = {
    "precio": None,
    "timestamp": 0
}

class handler(BaseHTTPRequestHandler):

    def obtener_precio_rhi(self, url):
        # 1. PEGA AQUÍ TU API KEY DE SCRAPERAPI
        SCRAPERAPI_KEY = "TU_API_KEY_AQUI"
        
        # Construimos la URL de la API con los parámetros para romper el bloqueo
        # 'render=true' le dice a ScraperAPI que procese el JavaScript de Cloudflare
        proxy_url = f"http://api.scraperapi.com?api_key={SCRAPERAPI_KEY}&url={url}&render=true"
        
        try:
            print("Enviando petición a través de ScraperAPI...")
            # Ya no necesitas cloudscraper ni headers raros, la API se encarga de todo
            res = requests.get(proxy_url, timeout=60)
            
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                
                # Usamos los mismos selectores de Investing
                tag = soup.find("div", {"data-test": "instrument-price-last"}) or \
                      soup.select_one('span[data-test="instrument-price-last"]') or \
                      soup.find("span", {"id": "last_last"})
                
                if tag:
                    # Lógica limpia para cambiar el punto por la coma sin meter decimales extras
                    valor_original = tag.get_text(strip=True).replace(',', '')
                    valor_final = valor_original.replace('.', ',')
                    print(f"¡LOGRADO CON PROXY!: {valor_final}")
                    return valor_final
                
                return "Tag_No_Encontrado"
            
            print(f"Error en ScraperAPI: Status {res.status_code}")
            return f"Error_{res.status_code}"
            
        except Exception as e:
            print(f"Excepción: {str(e)}")
            return "Error_Excepcion"

    def do_GET(self):
        global cache_rhi
        
        url_rhi = "https://es.investing.com/equities/rhi-ag"
        ahora = time.time()
        # Mantenemos las 2 horas de caché para que solo gaste 12 créditos al día
        TIEMPO_CACHE = 7200 

        if cache_rhi["precio"] and (ahora - cache_rhi["timestamp"] < TIEMPO_CACHE):
            valor_final = cache_rhi["precio"]
            fuente = "Caché interna (Crédito ahorrado)"
        else:
            valor_final = self.obtener_precio_rhi(url_rhi)
            
            if "Error" not in valor_final and valor_final != "Tag_No_Encontrado":
                cache_rhi["precio"] = valor_final
                cache_rhi["timestamp"] = ahora
                fuente = "Investing via ScraperAPI (Actualizado)"
            else:
                fuente = "Error en la API de Proxy"

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
