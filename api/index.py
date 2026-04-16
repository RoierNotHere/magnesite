import cloudscraper
from bs4 import BeautifulSoup
import json
import time
import random

# Simulación de base de datos/caché en memoria
cache_data = {
    "precio": None,
    "timestamp": 0
}

def obtener_precio_rhi():
    global cache_data
    
    url = "https://es.investing.com/equities/rhi-ag"
    ahora = time.time()
    TIEMPO_CACHE = 7200  # 2 horas en segundos

    # 1. Lógica del Timer/Caché para ahorrar peticiones
    if cache_data["precio"] and (ahora - cache_data["timestamp"] < TIEMPO_CACHE):
        print("\n[MODO AHORRO] Usando valor en caché para no saturar a Investing.")
        return cache_data["precio"], "Caché"

    # 2. Si el timer expiró, entramos a la web
    print(f"\n[PETICIÓN] Entrando a: {url}")
    
    # Configuramos el scraper para saltar Cloudflare
    scraper = cloudscraper.create_scraper(
        delay=10,
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'mobile': False
        }
    )

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            'Accept-Language': 'es-ES,es;q=0.9',
            'Referer': 'https://www.google.com/'
        }

        # Pequeño delay aleatorio para parecer humano
        time.sleep(random.uniform(1.5, 3.0))
        
        response = scraper.get(url, headers=headers, timeout=20)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Selectores de Investing para el precio
            tag = soup.find("div", {"data-test": "instrument-price-last"}) or \
                  soup.select_one('span[data-test="instrument-price-last"]') or \
                  soup.find("span", {"id": "last_last"})

            if tag:
                valor = tag.get_text(strip=True)
                
                # Guardamos en caché
                cache_data["precio"] = valor
                cache_data["timestamp"] = ahora
                
                print(f"[EXITO] Valor encontrado: {valor}")
                return valor, "Investing Real-time"
            else:
                print("[ERROR] No se encontró el tag del precio. Investing pudo cambiar el diseño.")
                return "Tag_No_Encontrado", "Error"
        
        print(f"[BLOQUEO] Código de estado: {response.status_code}")
        return f"Error_{response.status_code}", "Bloqueado"

    except Exception as e:
        print(f"[CRÍTICO] Ocurrió un error: {str(e)}")
        return "Error_Excepcion", "Error"

# --- BLOQUE DE TESTEO ---
if __name__ == "__main__":
    print("=== INICIANDO TEST DE SCRAPING RHI ===")
    
    # Prueba 1: Petición Real
    precio, fuente = obtener_precio_rhi()
    print(f"RESULTADO 1 -> Precio: {precio} | Fuente: {fuente}")

    print("\n--- Esperando 2 segundos para simular otra entrada ---")
    time.sleep(2)

    # Prueba 2: Debería entrar el TIMER (Caché)
    precio_cache, fuente_cache = obtener_precio_rhi()
    print(f"RESULTADO 2 -> Precio: {precio_cache} | Fuente: {fuente_cache}")