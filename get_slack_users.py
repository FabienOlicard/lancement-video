import os
import requests
from dotenv import load_dotenv

load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")

response = requests.get(
    "https://slack.com/api/users.list",
    headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"}
)

# Affiche tout le contenu brut de la réponse pour débug
print("Réponse brute de l'API Slack :")
print(response.status_code)
print(response.text)
