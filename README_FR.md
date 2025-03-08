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

## Nouveauté : Assistant de Vol Conversationnel

L'outil intègre maintenant un assistant basé sur un LLM (Large Language Model) pour permettre des recherches en langage naturel !

### Utilisation de l'Assistant de Vol

```bash
python flight_assistant.py --interactive
```

Cela lancera une interface conversationnelle où vous pourrez poser des questions comme :

- "Trouve-moi des vols de Montréal à Lima en mai 2025"
- "Je cherche un vol de YUL à CUZ fin mai avec maximum 3 escales"
- "Vols pour le Pérou en juin à moins de 900$ CAD"

L'assistant va :
1. Analyser votre demande en langage naturel
2. Extraire les paramètres de recherche pertinents
3. Exécuter la recherche de vols
4. Vous répondre avec les résultats dans un langage naturel

### Configuration de l'Assistant

Pour utiliser toutes les fonctionnalités de l'assistant, vous aurez besoin d'une clé API pour un LLM. Par défaut, le script est configuré pour utiliser l'API Claude d'Anthropic.

Définissez votre clé API comme variable d'environnement :

```bash
export ANTHROPIC_API_KEY=votre_clé_api
```

Sous Windows :
```cmd
set ANTHROPIC_API_KEY=votre_clé_api
```

Si aucune clé API n'est configurée, l'assistant utilise une méthode d'extraction de paramètres plus basique basée sur des mots-clés, qui est moins précise mais fonctionne sans dépendances externes.

## Prérequis

- Python 3.8 ou supérieur
- Un compte Amadeus for Developers (gratuit)
- (Optionnel) Compte email pour les notifications
- (Optionnel) Clé API Anthropic pour l'assistant conversationnel

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

## Sécurité et Considérations

- Ne codez pas en dur vos identifiants API réels ou mots de passe SMTP dans le script
- Utilisez des variables d'environnement ou un gestionnaire d'identifiants sécurisé
- Les identifiants de test inclus sont uniquement à des fins de démonstration et ont des fonctionnalités limitées

## Licence

Ce projet est publié sous la licence MIT - voir le fichier [LICENSE](LICENSE) pour plus de détails.

## Remerciements

- [Amadeus for Developers](https://developers.amadeus.com/) pour la fourniture de l'API de recherche de vols
- Ce projet a été créé avec l'aide de Claude AI
