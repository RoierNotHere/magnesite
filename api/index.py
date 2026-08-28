import json
import time
import random
import requests
from http.server import BaseHTTPRequestHandler
import cloudscraper
from bs4 import BeautifulSoup

# Caché rápida en memoria
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
        """ Convierte string de precio a float manejando formatos europeos o anglosajones """
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
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Referer': 'https://www.google.com/'
        }

        try:
            time.sleep(random.uniform(3.0, 5.0))
            res = scraper.get(url, headers=headers, timeout=30)

            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                tag = soup.find(attrs={"data-test": "instrument-price-last"}) or \
                      soup.select_one('span[data-test="instrument-price-last"]') or \
                      soup.find("span", {"id": "last_last"})

                if tag:
                    return self.parsear_numero(tag.get_text(strip=True))
            return None
        except Exception:
            return None

    def obtener_tasa_usd_cny(self):
        """ Consulta el tipo de cambio oficial mediante API rápida o usa valor de reserva """
        try:
            # API gratuita para tipo de cambio en tiempo real (USD -> CNY)
            url_api = "https://open.er-api.com/v6/latest/USD"
            response = requests.get(url_api, timeout=5)
            if response.status_code == 200:
                data = response.json()
                rate = data.get("rates", {}).get("CNY")
                if rate and rate > 0:
                    return rate
        except Exception:
            pass
        return 7.20 # Valor de reserva si la red falla

    def do_GET(self):
        global cache_investing

        magnesio_url = "https://es.investing.com/commodities/magnesium-99.9-min-china-futures"
        ahora = time.time()
        TIEMPO_CACHE = 7200  # 2 horas

        if cache_investing["magnesio_usd"] and (ahora - cache_investing["timestamp"] < TIEMPO_CACHE):
            valor_usd = cache_investing["magnesio_usd"]
        else:
            scraper = self.crear_scraper()
            precio_cny = self.obtener_precio_magnesio(magnesio_url, scraper)

            if isinstance(precio_cny, (int, float)):
                tasa_usdcny = self.obtener_tasa_usd_cny()
                valor_usd = round(precio_cny / tasa_usdcny, 2)

                cache_investing["magnesio_usd"] = valor_usd
                cache_investing["timestamp"] = ahora
            else:
                valor_usd = None

        # Devuelve solo la estructura JSON limpia con el valor numérico
        datos = {"precio_usd": valor_usd}

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(datos).encode('utf-8'))
