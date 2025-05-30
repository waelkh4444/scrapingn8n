# Utilise une image Python légère
FROM python:3.11-slim

# Crée le dossier de travail
WORKDIR /app

# Copie les fichiers nécessaires
COPY . .

# Installe les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Expose le port utilisé par Flask
EXPOSE 5000

# Commande de démarrage
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "scraping:app"]
