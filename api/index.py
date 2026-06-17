import json
import time
import random
from http.server import BaseHTTPRequestHandler
import cloudscraper
from bs4 import BeautifulSoup

# Cache global para proteger tu IP y espaciar las consultas
cache_rhi = {
    "precio": None,
    "timestamp": 0
}

class handler(BaseHTTPRequestHandler):

    def obtener_precio_rhi(self, url):
        # Inicializamos cloudscraper simulando una versión exacta de Chrome en Windows
        scraper = cloudscraper.create_scraper(
            delay=15, 
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        
        try:
            # 1. Lista de User-Agents reales y actualizados
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0'
            ]
            
            ua_elegido = random.choice(user_agents)
            
            # 2. Configuración de Headers de "Navegador Seguro"
            headers = {
                'User-Agent': ua_elegido,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-User': '?1',
                'sec-ch-ua': '"Chromium";v="125", "Google Chrome";v="125", "Not-A.Brand";v="99"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'Referer': 'https://www.google.com/'
            }

            # --- PASO DE CAMUFLAJE PREVIO ---
            # Primero visitamos Google para obtener cookies legítimas de sesión corporativa
            try:
                print("Simulando navegación previa en buscador...")
                scraper.get("https://www.google.com", headers={'User-Agent': ua_elegido}, timeout=15)
                # Pausa caótica antes de ir por el objetivo real
                time.sleep(random.uniform(3.2, 6.7))
            except:
                pass # Si Google falla, continuamos de todos modos

            # --- TIMERS CAÓTICOS (JITTER) ---
            # Hacemos una serie de pausas impredecibles para romper patrones de bots
            for _ in range(random.randint(2, 4)):
                time.sleep(random.uniform(2.5, 4.5))
            
            print(f"Lanzando petición camuflada a Investing...")
            res = scraper.get(url, headers=headers, timeout=35)
            
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                
                # Buscamos en la estructura del HTML
                tag = soup.find("div", {"data-test": "instrument-price-last"}) or \
                      soup.select_one('span[data-test="instrument-price-last"]') or \
                      soup.find("span", {"id": "last_last"})
                
                if tag:
                    # LÓGICA DE PRECIO SIMPLE (Sin .00 automáticos)
                    # Quitamos comas viejas y cambiamos el punto decimal por la coma del Scrap
                    valor_original = tag.get_text(strip=True).replace(',', '')
                    valor_final = valor_original.replace('.', ',')
                    
                    print(f"VALOR CONSEGUIDO: {valor_final}")
                    return valor_final
                
                return "Tag_No_Encontrado"
            
            print(f"BLOQUEO CLOUDSHARE: Código {res.status_code}")
            return f"Error_{res.status_code}"
            
        except Exception as e:
            print(f"Excepción interna: {str(e)}")
            return "Error_Excepcion"

    def do_GET(self):
        global cache_rhi
        
        url_rhi = "https://es.investing.com/equities/rhi-ag"
        ahora = time.time()
        TIEMPO_CACHE = 7200 # Conservamos las 2 horas para proteger la IP del servidor

        if cache_rhi["precio"] and (ahora - cache_rhi["timestamp"] < TIEMPO_CACHE):
            valor_final = cache_rhi["precio"]
            fuente = "Caché Local"
        else:
            valor_final = self.obtener_precio_rhi(url_rhi)
            
            if "Error" not in valor_final and valor_final != "Tag_No_Encontrado":
                cache_rhi["precio"] = valor_final
                cache_rhi["timestamp"] = ahora
                fuente = "Investing Original (Actualizado)"
            else:
                fuente = "Modo de Espera por Bloqueo"

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
