import json
import time
import random
import requests
from http.server import BaseHTTPRequestHandler
import cloudscraper
from bs4 import BeautifulSoup

# Caché en memoria
cache_investing = {"magnesio_usd": None, "timestamp": 0}

class handler(BaseHTTPRequestHandler):

    def crear_scraper(self):
        return cloudscraper.create_scraper(
            delay=20, 
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )

    def parsear_numero(self, texto_raw):
        """ Limpia el string y lo convierte a float respetando formato europeo o americano """
        limpio = ''.join(c for c in texto_raw if c.isdigit() or c in ['.', ','])
        if not limpio:
            return None

        if '.' in limpio and ',' in limpio:
            if limpio.rfind(',') > limpio.rfind('.'):
                limpio = limpio.replace('.', '').replace(',', '.')
            else:
                limpio = limpio.replace(',', '')
        elif ',' in limpio:
            limpio = limpio.replace(',', '.')

        return float(limpio)

    def obtener_precio_magnesio(self, url, scraper):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://www.google.com/',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }

        try:
            pausa = random.uniform(3.5, 6.0)
            print(f"Haciendo pausa de {pausa:.2f}s antes de scrapear el magnesio...")
            time.sleep(pausa)

            res = scraper.get(url, headers=headers, timeout=40)

            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                
                # Buscar por el tag especifico data-test="instrument-price-last" o fallbacks
                tag = soup.find(attrs={"data-test": "instrument-price-last"}) or \
                      soup.select_one('span[data-test="instrument-price-last"]') or \
                      soup.find("span", {"id": "last_last"})

                if tag:
                    val_text = tag.get_text(strip=True)
                    print(f"Texto capturado del tag: {val_text}")
                    return self.parsear_numero(val_text)
                else:
                    print("No se encontró la etiqueta del precio en el HTML.")
            else:
                print(f"Error de HTTP en Investing: {res.status_code}")

            return None
        except Exception as e:
            print(f"Excepción al scrapear: {e}")
            return None

    def obtener_tasa_cny_usd(self):
        """ Obtiene el cambio USD/CNY via API pública o usa tasa fija de respaldo si falla """
        try:
            res = requests.get("https://open.er-api.com/v6/latest/USD", timeout=5)
            if res.status_code == 200:
                data = res.json()
                rate = data.get("rates", {}).get("CNY")
                if rate:
                    return float(rate)
        except Exception as e:
            print(f"Error al obtener tasa de cambio: {e}")
        
        return 7.20 # Valor por defecto seguro si la API de divisa no responde

    def do_GET(self):
        global cache_investing

        magnesio_url = "https://es.investing.com/commodities/magnesium-99.9-min-china-futures"
        ahora = time.time()
        TIEMPO_CACHE = 7200  # 2 horas

        if cache_investing["magnesio_usd"] and (ahora - cache_investing["timestamp"] < TIEMPO_CACHE):
            print("Entrando a datos de caché...")
            valor_usd = cache_investing["magnesio_usd"]
        else:
            scraper = self.crear_scraper()
            
            # 1. Scrapear primero el precio del magnesio en CNY
            precio_cny = self.obtener_precio_magnesio(magnesio_url, scraper)

            if precio_cny is not None:
                # 2. Convertir CNY a USD con la tasa de cambio
                tasa_usdcny = self.obtener_tasa_cny_usd()
                valor_usd = round(precio_cny / tasa_usdcny, 2)
                
                print(f"Precio CNY: {precio_cny} | Tasa USD/CNY: {tasa_usdcny} | Precio USD: {valor_usd}")

                # Guardar en caché
                cache_investing["magnesio_usd"] = valor_usd
                cache_investing["timestamp"] = ahora
            else:
                valor_usd = None

        # Responder únicamente con la clave "precio_usd"
        datos = {"precio_usd": valor_usd}

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(datos).encode('utf-8'))
