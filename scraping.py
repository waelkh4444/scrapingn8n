from flask import Flask, request, jsonify
import gspread
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import gspread.utils

app = Flask(__name__)

# === Fonction scraping
def get_infogreffe_info(siren):
    options = Options()
    options.add_argument("--headless")
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

        return dirigeant, ca
    finally:
        driver.quit()

@app.route('/scrape-sheet', methods=['POST'])
def scrape_sheet():
    try:
        gc = gspread.service_account(filename='C:/Users/Wael Khanfir/Downloads/credential.json')
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

if __name__ == "__main__":
    app.run(port=5000, debug=True)
