from flask import Flask, request, jsonify
import gspread
import requests
from bs4 import BeautifulSoup
import gspread.utils
import os
import json

app = Flask(__name__)

# === Fonction scraping avec BeautifulSoup
def get_infogreffe_info(siren):
    url = f"https://www.infogreffe.fr/entreprise/{siren}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return "Non trouvé", "Non trouvé"

        soup = BeautifulSoup(response.text, 'html.parser')

        dirigeant_div = soup.find("div", {"data-testid": "block-representant-legal"})
        dirigeant = dirigeant_div.find("div", class_="textData").get_text(strip=True) if dirigeant_div else "Non trouvé"

        ca_div = soup.find("div", {"data-testid": "ca"})
        ca = ca_div.get_text(strip=True) if ca_div else "Non trouvé"

        return dirigeant, ca

    except Exception as e:
        print(f"Erreur de scraping: {e}")
        return "Non trouvé", "Non trouvé"

@app.route('/scrape-sheet', methods=['POST'])
def scrape_sheet():
    try:
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

        if updates:
            worksheet.batch_update(updates)

        return jsonify({
            "status": "success",
            "message": f"{lignes_traitees} lignes mises à jour.",
            "updates": lignes_traitees
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
