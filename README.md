# Lanceur de Vidéo MONDAY + Slack

## Étapes pour lancer la webapp localement :

1. Ouvre un terminal dans ce dossier.
2. Installe les dépendances :
```
pip install -r requirements.txt
```

3. Renseigne les variables dans le fichier `.env` :
   - `MONDAY_API_KEY`
   - `SLACK_WEBHOOK_URL`
   - `MONDAY_BOARD_ID` (tu peux l’obtenir via https://monday.com/developers/v2/try-it-yourself/)

4. Lance la webapp :
```
python app.py
```

5. Va dans ton navigateur sur http://127.0.0.1:5000

Tu pourras alors lancer tes projets vidéos depuis ton navigateur !