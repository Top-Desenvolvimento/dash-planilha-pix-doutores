from playwright.sync_api import sync_playwright
from coletor_pix import processar_unidade, SISTEMAS
from regras_doutores import montar_mapa_creditos

mapa = montar_mapa_creditos()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # 👈 abre navegador

    resultado = processar_unidade(browser, SISTEMAS[0], mapa)

    for r in resultado:
        print(r)

    browser.close()
