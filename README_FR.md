# Moniteur de Prix de Vols Montréal-Lima

Un agent d'IA qui surveille les prix des vols de Montréal (YUL) à Lima (LIM) et vous envoie des notifications lorsqu'ils descendent en dessous de votre seuil cible.

Cet outil utilise l'API Amadeus Flight Offers Search pour vérifier régulièrement les prix des vols et peut vous envoyer des notifications par email lorsqu'il trouve une bonne affaire.

![Bannière de Surveillance de Vols](https://placehold.co/1200x300/EEE/31343C?text=Moniteur+de+Vols+Montr%C3%A9al-Lima&font=montserrat)

## Fonctionnalités

- 🔍 **Suivi Automatisé des Prix**: Vérifie régulièrement les prix des vols de Montréal à Lima
- 📊 **Historique des Prix**: Enregistre les données historiques de prix pour vous aider à comprendre les tendances
- 📧 **Notifications par Email**: Envoie des alertes lorsque les prix descendent sous votre seuil cible
- 📅 **Recherche de Dates Flexibles**: Peut rechercher sur une plage de dates pour trouver les meilleures offres
- 🔄 **Programmation Personnalisable**: Configurez la fréquence des vérifications de prix
- 🛫 **Détails des Compagnies et Itinéraires**: Fournit des informations détaillées sur chaque option de vol
- ✈️ **Filtrage des Correspondances**: Limitez les résultats aux vols directs ou avec un nombre maximum d'escales
- 🗓️ **Plage de Dates Spécifique**: Optimisé pour la fenêtre de voyage du 29 mai au 9 juin 2025
- 🔗 **Liens de Réservation**: Génère automatiquement des liens de recherche pour réserver les vols
- 💰 **Support des Devises**: Demande explicitement les prix en dollars canadiens (CAD)
- 🗣️ **Interface en Langage Naturel**: Utilisez des requêtes en français ou en anglais pour chercher des vols
- 🤖 **Choix de Modèles LLM**: Flexibilité pour utiliser différents fournisseurs et modèles d'IA

## Nouveauté : Assistant de Vol Conversationnel avec Choix de LLM

L'outil intègre maintenant un assistant basé sur différents modèles de langage (LLM) pour permettre des recherches en langage naturel !

### Utilisation de l'Assistant de Vol

```bash
python flight_assistant.py --interactive
```

Cela lancera une interface conversationnelle où vous pourrez poser des questions comme :

- "Trouve-moi des vols de Montréal à Lima en mai 2025"
- "Je cherche un vol de YUL à CUZ fin mai avec maximum 3 escales"
- "Vols pour le Pérou en juin à moins de 900$ CAD"

### Choix du Fournisseur de LLM

Vous pouvez choisir parmi plusieurs fournisseurs de LLM :

```bash
# Visualiser les fournisseurs et modèles disponibles
python flight_assistant.py --list

# Utiliser un fournisseur et modèle spécifique
python flight_assistant.py --provider openai --model gpt-4 --interactive
```

Fournisseurs disponibles :
- **OpenRouter** : Accès à Mistral, Mixtral, Gemma, Llama 3, etc.
- **OpenAI** : Accès aux modèles GPT
- **Anthropic** : Accès aux modèles Claude

En mode interactif, vous pouvez également changer de fournisseur en tapant :
```
use openai model gpt-4
```

### Configuration des API

Pour utiliser les différents fournisseurs de LLM, configurez les variables d'environnement correspondantes :

```bash
# Pour OpenRouter (Mistral, Mixtral, etc.)
export OPENROUTER_API_KEY=votre_clé_api

# Pour OpenAI (GPT)
export OPENAI_API_KEY=votre_clé_api

# Pour Anthropic (Claude)
export ANTHROPIC_API_KEY=votre_clé_api
```

Sous Windows :
```cmd
set OPENROUTER_API_KEY=votre_clé_api
```

## Prérequis

- Python 3.8 ou supérieur
- Un compte Amadeus for Developers (gratuit)
- (Optionnel) Compte email pour les notifications
- (Optionnel) Clé API pour au moins un des fournisseurs de LLM

## Démarrage Rapide

### 1. Clonez le dépôt

```bash
git clone https://github.com/tofunori/montreal-lima-flight-monitor.git
cd montreal-lima-flight-monitor
```

### 2. Installez les dépendances

```bash
pip install -r requirements.txt
```

### 3. Exécutez avec les paramètres par défaut (mode test)

Le script inclut des identifiants d'API de test que vous pouvez utiliser immédiatement :

```bash
python flight_monitor.py --test
```

Cela effectuera une seule vérification de prix et affichera les résultats sans démarrer la surveillance continue.

### 4. Ou utilisez l'assistant conversationnel

```bash
python flight_assistant.py --interactive
```

## Options de Configuration

### Arguments de Ligne de Commande

| Argument | Description | Défaut |
|----------|-------------|---------|
| `--api-key` | Clé API Amadeus | Utilise var d'env ou clé de test incluse |
| `--api-secret` | Secret API Amadeus | Utilise var d'env ou secret de test inclus |
| `--origin` | Code d'aéroport d'origine | YUL (Montréal) |
| `--destination` | Code d'aéroport de destination | LIM (Lima) |
| `--email` | Email pour les notifications | Aucun |
| `--threshold` | Seuil de prix pour les notifications | Aucun |
| `--interval` | Intervalle de vérification en heures | 24 |
| `--flexible` | Vérifier des dates flexibles | False |
| `--range` | Plage de jours pour dates flexibles | 3 |
| `--max-stops` | Nombre maximum d'escales | 2 |
| `--any-dates` | Vérifier n'importe quelles dates (pas seulement 29 mai-9 juin) | False |
| `--currency` | Code de devise | CAD |
| `--debug` | Activer la journalisation de débogage | False |
| `--test` | Exécuter une fois et quitter | False |

### Arguments pour l'Assistant de Vol

| Argument | Description | Défaut |
|----------|-------------|---------|
| `--interactive` | Mode interactif | False |
| `--provider` | Fournisseur de LLM | openrouter |
| `--model` | Modèle de LLM | dépend du fournisseur |
| `--list` | Liste des fournisseurs et modèles | False |

## Licence

Ce projet est publié sous la licence MIT - voir le fichier [LICENSE](LICENSE) pour plus de détails.

## Remerciements

- [Amadeus for Developers](https://developers.amadeus.com/) pour la fourniture de l'API de recherche de vols
- Ce projet a été créé avec l'aide de Claude AI
