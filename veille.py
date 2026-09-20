# # veille.py — Récupère les actus IA, les résume avec Gemini, écrit veille.json
import os
import json
import time
import feedparser
import requests

# 1. La clé vient du SECRET GitHub (jamais écrite dans le code)
CLE_API = os.environ["GEMINI_API_KEY"]

# 2. Les sources RSS à surveiller
FLUX = [
    "https://www.actuia.com/feed/",
    "https://www.lebigdata.fr/feed",
]

# 3. On récupère les articles récents de chaque flux
articles = []
for url in FLUX:
    flux = feedparser.parse(url)
    for entree in flux.entries[:5]:          # 5 articles max par flux
        articles.append({
            "titre": entree.get("title", ""),
            "lien": entree.get("link", ""),
        })

# 4. On prépare la consigne (le "brief") pour l'IA
liste_texte = "\n".join(f"- {a['titre']} ({a['lien']})" for a in articles)
consigne = (
    "Voici des titres d'actualites sur l'intelligence artificielle.\n"
    "Choisis les 3 PLUS IMPORTANTES et resume chacune en 2 phrases claires, en francais.\n"
    "Reponds UNIQUEMENT avec un tableau JSON, sans texte autour, au format :\n"
    '[{"titre": "...", "resume": "...", "lien": "..."}]\n\n'
    f"Articles :\n{liste_texte}"
)

# 5. On appelle l'API Gemini, avec plusieurs tentatives en cas de surcharge
URL_API = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent"

def appeler_gemini(consigne, essais=5):
    for i in range(essais):
        reponse = requests.post(
            URL_API,
            headers={"x-goog-api-key": CLE_API, "Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": consigne}]}]},
            timeout=60,
        )
        data = reponse.json()
        if "candidates" in data:
            return data["candidates"][0]["content"]["parts"][0]["text"]

        statut = data.get("error", {}).get("status", "inconnu")
        attente = 5 * (2 ** i)               # 5s, 10s, 20s, 40s, 80s
        print(f"Tentative {i+1}/{essais} echouee ({statut}), nouvel essai dans {attente}s")
        time.sleep(attente)

    raise RuntimeError(f"Gemini indisponible apres {essais} tentatives")

texte_ia = appeler_gemini(consigne)

# 6. On nettoie (l'IA ajoute parfois des balises ```json)
texte_ia = texte_ia.replace("```json", "").replace("```", "").strip()

# 7. On ecrit le fichier final que le portfolio lira
veille = json.loads(texte_ia)
with open("veille.json", "w", encoding="utf-8") as f:
    json.dump(veille, f, ensure_ascii=False, indent=2)

print("veille.json genere avec", len(veille), "actualites.")
