# Verwende ein Python-Basisimage
FROM python:3.10-slim

# Definiere das Arbeitsverzeichnis im Container
WORKDIR /usr/src/app

# Installiere die Abhängigkeiten
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere das Skript und andere Dateien
COPY . .

# Setze den Befehl, der beim Starten des Containers ausgeführt wird
CMD ["python", "main.py"]
