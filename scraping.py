from flask import Flask, request, jsonify
import gspread
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import gspread.utils
import os
from oauth2client.service_account import ServiceAccountCredentials
import json

app = Flask(__name__)

# === Fonction scraping
def get_infogreffe_info(siren):
    options = Options()
    options.add_argument("--headless=new")  # Obligation en environnement cloud
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)

    try:
        url = f"https://www.infogreffe.fr/entreprise/{siren}"
        driver.get(url)
        time.sleep(5)

        try:
            dirigeant = driver.find_element(
                By.XPATH, "//div[@data-testid='block-representant-legal']//div[contains(@class, 'textData')]"
            ).text.strip()
        except:
            dirigeant = "Non trouvé"

        try:
            ca = driver.find_element(
                By.XPATH, "//div[@data-testid='ca']"
            ).text.strip()
        except:
            ca = "Non trouvé"

        print(f"➡️ Dirigeant : {dirigeant} | CA : {ca}")
        return dirigeant, ca
    finally:
        driver.quit()

@app.route('/scrape-sheet', methods=['POST'])
def scrape_sheet():
    try:
        # Chargement des credentials Google Sheets depuis une variable d'environnement
        creds_json = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
        creds_dict = json.loads(creds_json)
        gc = gspread.service_account_from_dict(creds_dict)

        sh = gc.open("base_insee")
        worksheet = sh.sheet1
        rows = worksheet.get_all_values()
        headers = rows[0]

        siren_col = headers.index("siren")
        dirigeant_col = headers.index("Nom_dirigeant")
        ca_col = headers.index("Chiffre_daffaire")

        updates = []
        lignes_traitees = 0

        for i, row in enumerate(rows[1:], start=2):
            siren = row[siren_col] if len(row) > siren_col else ""
            dirigeant_val = row[dirigeant_col] if len(row) > dirigeant_col else ""
            ca_val = row[ca_col] if len(row) > ca_col else ""

            if not siren or dirigeant_val or ca_val:
                continue

            print(f"🔍 Traitement {siren}")
            dirigeant, ca = get_infogreffe_info(siren)

            if dirigeant == "Non trouvé" and ca == "Non trouvé":
                continue

            updates.append({
                'range': gspread.utils.rowcol_to_a1(i, dirigeant_col + 1),
                'values': [[dirigeant]]
            })
            updates.append({
                'range': gspread.utils.rowcol_to_a1(i, ca_col + 1),
                'values': [[ca]]
            })
            lignes_traitees += 1

            break  # 🔒 On ne traite qu'une ligne pour éviter crash mémoire

        if updates:
            worksheet.batch_update(updates)
            print(f"✅ Mise à jour Google Sheet réussie ({lignes_traitees} ligne(s))")

        return jsonify({
            "status": "success",
            "message": f"{lignes_traitees} ligne(s) mise(s) à jour.",
            "updates": lignes_traitees
        })

    except Exception as e:
        print(f"❌ Erreur : {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500
