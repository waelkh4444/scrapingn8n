# Utilise une image Python
FROM python:3.11-slim

# Variables d’environnement
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    unzip \
    chromium-driver \
    chromium \
    && apt-get clean

# Définir les variables d’environnement pour Selenium
ENV CHROME_BIN=/usr/bin/chromium
ENV PATH=$PATH:/usr/bin/chromium

# Créer et définir le répertoire de travail
WORKDIR /app

# Copier les fichiers dans l’image
COPY . /app

# Installer les dépendances Python
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Exposer le port utilisé par Flask
EXPOSE 5000

# Commande pour lancer l'application Flask avec gunicorn
CMD ["gunicorn", "scraping:app", "--bind", "0.0.0.0:5000"]
