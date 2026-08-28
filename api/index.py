import json
import time
import random
from http.server import BaseHTTPRequestHandler
import cloudscraper
from bs4 import BeautifulSoup

# Caché simplificada solo para el valor en USD
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
        """ Extrae el valor numérico sin importar si viene en formato europeo o anglosajón """
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

    def obtener_precio(self, url, scraper):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Referer': 'https://www.google.com/'
        }

        try:
            time.sleep(random.uniform(3.5, 6.0))
            res = scraper.get(url, headers=headers, timeout=40)

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

    def obtener_tasa_usdcny(self, scraper):
        url_usd_cny = "https://es.investing.com/currencies/usd-cny"
        res = self.obtener_precio(url_usd_cny, scraper)
        if isinstance(res, (int, float)) and res > 0:
            return res
        return 7.20 # Respaldo por si falla el scraping de la divisa

    def do_GET(self):
        global cache_investing

        magnesio_url = "https://es.investing.com/commodities/magnesium-99.9-min-china-futures"
        ahora = time.time()
        TIEMPO_CACHE = 7200  # 2 horas

        if cache_investing["magnesio_usd"] and (ahora - cache_investing["timestamp"] < TIEMPO_CACHE):
            valor_usd = cache_investing["magnesio_usd"]
        else:
            scraper = self.crear_scraper()
            precio_cny = self.obtener_precio(magnesio_url, scraper)

            if isinstance(precio_cny, (int, float)):
                tasa_usdcny = self.obtener_tasa_usdcny(scraper)
                valor_usd = round(precio_cny / tasa_usdcny, 2)

                cache_investing["magnesio_usd"] = valor_usd
                cache_investing["timestamp"] = ahora
            else:
                valor_usd = None

        # Devuelve directamente el valor o null si falló
        datos = {"precio_usd": valor_usd}

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(datos).encode('utf-8'))
