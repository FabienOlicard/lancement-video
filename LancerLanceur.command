#!/bin/bash
cd "$(dirname "$0")"
echo "➡️ Lancement du serveur Flask..."

# Lancement de Flask en tâche de fond
python3 app.py &

# Pause pour laisser le temps à Flask de démarrer
sleep 2

echo "🌐 Ouverture du navigateur..."
open http://127.0.0.1:5000

# Garde le terminal ouvert pour lire les messages
echo ""
read -n 1 -s -r -p "✅ Serveur lancé. Appuie sur une touche pour fermer ce terminal..."