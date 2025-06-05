from flask import Flask, render_template_string, request
from datetime import datetime, timedelta
import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

MONDAY_API_KEY = os.getenv("MONDAY_API_KEY")
MONDAY_BOARD_ID = os.getenv("MONDAY_BOARD_ID")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")

HEADERS = {
    "Authorization": MONDAY_API_KEY,
    "Content-Type": "application/json"
}

SLACK_HEADERS = {
    "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
    "Content-Type": "application/json"
}

SLACK_USERS = {
    "Fabien": "U07HUQK9XD4",
    "Loïc": "U07J49AJCFP",
    "Denis": "U07JNMA9AMV",
    "Fanny": "U07KFTMRC1X"
}

TEMPLATE = '''
<!doctype html>
<title>Lancement Vidéo</title>
<h1>Créer un tableau Monday pour une vidéo</h1>
<form method=post>
  Titre: <input type=text name=title><br><br>
  Date de sortie (JJ-MM-AAAA): <input type=text name=date><br><br>
  Chaîne:
  <select name=channel>
    <option>Chaîne Principale</option>
    <option>Chaîne Secondaire</option>
    <option>Ckankonjoue</option>
    <option>Casse-Tête</option>
  </select><br><br>
  Partenariat ?
  <select name=partner>
    <option>Non</option>
    <option>Oui $$$</option>
  </select><br><br>
  <input type=submit value="Créer le processus sur Monday">
</form>
'''

SET_A = [
    ("Ecriture", ["Fabien"], -18),
    ("Tournage", ["Fabien", "Loïc", "Denis"], -17),
    ("Montage", ["Loïc", "Denis"], -10),
    ("Relecture", ["Fanny"], -5),
    ("Vignette", ["Loïc"], -3),
    ("Mise en ligne", ["Fabien", "Loïc"], -2),
    ("Publication", ["Fabien"], 0)
]

SET_B = [
    ("Devis signé", ["Fanny"], -25),
    ("Ecriture", ["Fabien"], -22),
    ("Ecriture intégration", ["Fanny", "Fabien"], -20),
    ("Tournage", ["Fabien", "Loïc", "Denis"], -15),
    ("Montage", ["Loïc", "Denis"], -12),
    ("Relecture", ["Fanny"], -10),
    ("Envoie V1 à la marque", ["Fanny", "Loïc", "Denis"], -9),
    ("Envoie Vdef à la marque", ["Fanny", "Loïc", "Denis"], -6),
    ("Vignette", ["Loïc"], -3),
    ("Mise en ligne", ["Fabien", "Loïc"], -2),
    ("Publication", ["Fabien"], 0),
    ("Facturation", ["Fanny"], 1)
]

name_to_id = {
    "Fabien": 15941243,
    "Loïc": 15941262,
    "Fanny": 15941263,
    "Denis": 17889986
}

def create_group(board_id, group_name):
    query = {
        "query": f'''
        mutation {{
            create_group (board_id: "{board_id}", group_name: "{group_name}") {{
                id
            }}
        }}
        '''
    }
    response = requests.post("https://api.monday.com/v2", json=query, headers=HEADERS)
    return response.json()

def create_item(board_id, group_id, name, start_date, end_date, assignees_ids, status_index):
    column_values = json.dumps({
        "person": {
            "personsAndTeams": [{"id": uid, "kind": "person"} for uid in assignees_ids]
        },
        "status": {"index": status_index},
        "timeline": {"from": start_date, "to": end_date}
    })

    query = {
        "query": '''
        mutation CreateItem($board_id: ID!, $group_id: String!, $item_name: String!, $column_values: JSON!) {
          create_item (
            board_id: $board_id,
            group_id: $group_id,
            item_name: $item_name,
            column_values: $column_values
          ) {
            id
          }
        }
        ''',
        "variables": {
            "board_id": str(board_id),
            "group_id": group_id,
            "item_name": name,
            "column_values": column_values
        }
    }

    response = requests.post("https://api.monday.com/v2", json=query, headers=HEADERS)
    try:
        data = response.json()
        return data.get("data", {}).get("create_item", {}).get("id")
    except Exception as e:
        print("Erreur create_item:", e)
        print("Réponse:", response.text)
        return None

def notify_user_on_slack(user_id, group_name, date_str, first_name, group_id):
    link_browser = f"https://sherlocks-mind-company.monday.com/boards/{MONDAY_BOARD_ID}?openGroup={group_id}"
    link_app = f"https://app.monday.com/boards/{MONDAY_BOARD_ID}/groups/{group_id}"
    text = (
        f"Bonjour {first_name},\n"
        f"🎬 Nouvelle vidéo *{group_name}* (sortie le {date_str}).\n"
        f"👉 Voici le lien direct dans ton navigateur : {link_browser}\n"
        f"👉 Voici le lien direct dans ton appli (si tu es sur ton tel) : {link_app}\n"
        f"Merci de vérifier les dates de tes tâches et de les modifier rapidement si besoin.\n"
        f"Toute modification de planning ou dépassement doit être signalé à Fanny."
        f" (Ceci est particulièrement vraie pour les V1 et VDEF des partenariats)"
    )
    payload = {
        "channel": user_id,
        "text": text
    }
    requests.post("https://slack.com/api/chat.postMessage", headers=SLACK_HEADERS, json=payload)

def comment_on_monday_item(item_id, task_name):
    if not item_id:
        print(f"Impossible de commenter l'item car item_id est None pour la tâche {task_name}")
        return

    base_message = "🔔 Merci de vérifier la date de cette tâche et de la modifier si besoin."
    if "V1" in task_name or "Vdef" in task_name:
        base_message += " Toute dépassement sur cette étape doit être signalé au plus tôt à Fanny."

    query = {
        "query": '''
        mutation ($item_id: Int!, $body: String!) {
          create_update (item_id: $item_id, body: $body) {
            id
          }
        }
        ''',
        "variables": {
            "item_id": int(item_id),
            "body": base_message
        }
    }
    requests.post("https://api.monday.com/v2", json=query, headers=HEADERS)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        title = request.form['title']
        date_str = request.form['date']
        channel = request.form['channel']
        partner = request.form['partner'].startswith("Oui")

        sortie = datetime.strptime(date_str, "%d-%m-%Y")
        group_name = f"{channel} - {title}"

        group_creation = create_group(MONDAY_BOARD_ID, group_name)
        group_id = group_creation.get("data", {}).get("create_group", {}).get("id")

        base_tasks = SET_B if partner else SET_A
        full_task_list = [("Vérification du tableau", ["Fanny"], -30, 2)] + [
            (name, people, delta, 3) for name, people, delta in base_tasks
        ]

        notified_users = set()

        for task_data in full_task_list:
            task, people, delta, status_index = task_data
            date_cible = sortie + timedelta(days=delta)
            start = (date_cible - timedelta(days=1)).strftime("%Y-%m-%d")
            end = date_cible.strftime("%Y-%m-%d")
            ids = [name_to_id[n] for n in people]
            slack_ids = [(n, SLACK_USERS[n]) for n in people if n in SLACK_USERS]

            item_id = create_item(MONDAY_BOARD_ID, group_id, task, start, end, ids, status_index)

            if item_id:
                comment_on_monday_item(item_id, task)

                for name, sid in slack_ids:
                    if sid not in notified_users:
                        notify_user_on_slack(sid, group_name, date_str, name, group_id)
                        notified_users.add(sid)

        slack_message = {
            "text": f"🚀 Nouvelle vidéo programmée sur Monday : *{group_name}* (sortie le {date_str}). Merci aux personnes concernées de valider leurs tâches sur MONDAY."
        }
        requests.post(SLACK_WEBHOOK_URL, json=slack_message)

        return render_template_string('''
            <!doctype html>
            <title>Tableau créé pour cette vidéo</title>
            <h2>✅ La vidéo "{{ group_name }}" possède son tableau !</h2>
            <p>Souhaites-tu créer un tableau pour une autre vidéo ?</p>
            <form method="get" action="/">
                <button type="submit">Oui, maintenant</button>
            </form>
            <form method="get" action="/fin">
                <button type="submit">Non, j'ai terminé</button>
            </form>
        ''', group_name=group_name)

    return render_template_string(TEMPLATE)

@app.route('/fin')
def fin():
    return '''
        <!doctype html>
        <title>Fin du processus</title>
        <h2>👍 Merci, tous les tableaux Monday ont été créés !</h2>
        <p>Tu peux fermer cette page.</p>
        <form method="get" action="/">
            <button type="submit">Oups, j'ai oublié un tableau pour une vidéo</button>
        </form>
    '''

if __name__ == '__main__':
    print("➡️ Flask démarre sur http://0.0.0.0:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)
