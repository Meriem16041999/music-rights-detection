# 🎵 Music Rights Detection

Application web d'aide à la détection, l'identification et la déclaration des musiques utilisées dans une émission.

L'application analyse une vidéo, détecte automatiquement les morceaux via **ACRCloud**, enrichit les résultats avec le **répertoire SACEM**, permet une validation manuelle et génère les données nécessaires à la déclaration musicale.

## Fonctionnalités

### 🎧 Détection musicale

* Analyse automatique d'une vidéo
* Reconnaissance musicale avec ACRCloud
* Analyse par segments audio
* Nettoyage et fusion des détections successives
* Détection des occurrences répétées
* Calcul de la durée cumulée
* Conservation du premier TC IN et du dernier TC OUT

### 🎬 Timeline

Timeline interactive synchronisée avec la vidéo.

Elle permet notamment :

* visualisation des morceaux détectés
* navigation dans la vidéo
* déplacement des segments
* modification du TC IN / TC OUT
* redimensionnement des segments
* ajout et suppression manuelle
* zoom temporel
* sélection d'un morceau et affichage de ses propriétés

Les couleurs permettent d'identifier rapidement le statut des résultats :

* 🟢 **Vert** : résultat validé
* 🟠 **Orange** : résultat à vérifier
* 🔴 **Rouge** : résultat SACEM non trouvé
* ⚪ **Gris** : résultat en attente

## 🏛️ Enrichissement SACEM

Les morceaux détectés peuvent être recherchés automatiquement dans le répertoire SACEM.

Les informations récupérées peuvent inclure :

* titre SACEM
* auteur
* compositeur
* éditeur
* sous-éditeur
* interprète
* ISWC
* lien vers le répertoire SACEM

L'utilisateur peut également ouvrir la recherche SACEM correspondante afin de vérifier manuellement un résultat.

## ✅ Validation

Chaque résultat peut être contrôlé manuellement.

Deux états supplémentaires sont disponibles :

* **Validé**
* **À vérifier**

La validation est conservée dans les données du projet et influence le score qualité de l'émission.

## 💾 Cache SACEM

Les résultats SACEM confirmés sont stockés dans une base SQLite locale.

Cela permet d'éviter de refaire une recherche SACEM lorsqu'un morceau déjà connu apparaît dans une nouvelle émission.

Exemple :

```text
ACRCloud
    ↓
Titre détecté
    ↓
Cache SACEM ?
   ↙       ↘
 OUI       NON
  ↓         ↓
Résultat   Recherche SACEM
immédiat       ↓
            Cache
```

Les bases SQLite et le cache local ne sont pas versionnés dans Git.

## 📊 Score qualité

L'application calcule des statistiques pour chaque projet :

* nombre de segments
* nombre de résultats validés
* nombre de résultats à vérifier
* nombre de résultats non validés
* score qualité global

Ces informations sont visibles dans l'historique des émissions.

## 📁 Historique des projets

Une émission peut être sauvegardée puis ouverte ultérieurement.

L'historique permet de :

* retrouver les émissions précédentes
* ouvrir un projet
* reprendre les modifications
* visualiser son score qualité
* connaître le nombre de segments validés ou à vérifier
* supprimer un projet

## 📈 Progression des analyses

Les analyses longues utilisent un système de jobs.

L'interface affiche :

* progression en pourcentage
* chunk actuellement analysé
* nombre total de chunks
* étape en cours
* erreurs éventuelles

Une analyse peut également être interrompue puis reprise grâce aux checkpoints enregistrés localement.

## 📤 Export

L'application permet notamment de générer :

* un fichier Excel de déclaration M6
* un fichier Excel complet du projet

## Modes disponibles

### Émission classique

Pipeline principal :

```text
Vidéo
  ↓
Extraction audio
  ↓
ACRCloud
  ↓
Nettoyage / fusion
  ↓
Timeline
  ↓
SACEM
  ↓
Validation
  ↓
Export Excel
```

### Mot de Passe / MDP

Mode spécifique permettant notamment de travailler avec un conducteur et des éléments musicaux propres à l'émission.

---

# Architecture

```text
music_rights_complete/
│
├── backend_api.py
├── sacem_agent.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── frontend/
│   ├── package.json
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── HistoryPage.jsx
│   └── ...
│
└── cache/
    └── jobs/
```

Le dossier `cache/` est généré localement et ne doit pas être ajouté au dépôt Git.

---

# Installation

## 1. Cloner le projet

```bash
git clone https://github.com/Meriem16041999/music-rights-detection.git
cd music-rights-detection
```

## 2. Créer l'environnement Python

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Installer les dépendances Python

```bash
pip install -r requirements.txt
```

## 4. Installer Playwright

```bash
python -m playwright install chromium
```

## 5. Installer le frontend

```bash
cd frontend
npm install
```

---

# Configuration

Les identifiants et clés API ne doivent jamais être enregistrés directement dans Git.

Créer un fichier `.env` local pour les variables nécessaires, notamment les identifiants ACRCloud.

Exemple :

```text
ACR_HOST=...
ACR_ACCESS_KEY=...
ACR_ACCESS_SECRET=...
```

Ajouter `.env` au `.gitignore`.

---

# Lancement

Deux terminaux sont nécessaires.

## Backend

Depuis la racine :

```bash
source .venv/bin/activate
python -m uvicorn backend_api:app --reload --port 8000
```

Le backend est disponible sur :

```text
http://127.0.0.1:8000
```

La documentation FastAPI est disponible sur :

```text
http://127.0.0.1:8000/docs
```

## Frontend

Dans un deuxième terminal :

```bash
cd frontend
npm run dev
```

Ouvrir ensuite l'adresse affichée par Vite dans le navigateur.

---

# Fichiers locaux à ne pas versionner

Le `.gitignore` doit notamment contenir :

```gitignore
.venv/
__pycache__/
*.pyc

.env

frontend/node_modules/
frontend/dist/

cache/
cache/jobs/

*.sqlite3
*.db

*.mp4
*.mov
*.mkv
*.avi

.DS_Store
```

Les vidéos analysées peuvent dépasser la limite de taille de GitHub et ne doivent jamais être ajoutées au dépôt.

---

# Stack technique

**Frontend**

* React
* Vite
* JavaScript
* CSS

**Backend**

* Python
* FastAPI
* Uvicorn

**Traitement**

* FFmpeg
* ACRCloud
* Playwright
* SACEM

**Stockage**

* SQLite
* JSON
* checkpoints locaux

**Exports**

* Excel

---

# Développement

Avant un commit :

```bash
git status
```

Vérifier notamment qu'aucune vidéo, base SQLite, clé API ou donnée temporaire n'est présente.

Puis :

```bash
git add .
git commit -m "Description des modifications"
git push
```

---

# État du projet

Le projet est en développement actif.

Les prochaines évolutions prévues peuvent notamment inclure :

* sélection manuelle parmi plusieurs résultats SACEM
* mémorisation des validations manuelles dans le cache
* filtres par statut qualité
* amélioration de la timeline
* sauvegarde automatique
* reprise plus complète après interruption
* outils supplémentaires de contrôle et d'export
