# V.I.E Alert Bot (Civiweb)

Ce bot vérifie régulièrement les offres V.I.E sur Civiweb et envoie un email quand de nouvelles offres apparaissent.

## Prérequis

- Python 3.11+
- Un compte email SMTP (Gmail, Outlook, Mailgun, etc.)

## Installation

```zsh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Crée un fichier `.env` à partir de l'exemple :

```zsh
cp .env.example .env
```

Renseigne les variables SMTP dans `.env`.

Tu peux aussi surcharger l'API :

```
OFFERS_API_ENDPOINT=https://civiweb-api-prd.azurewebsites.net/api/Offers/search
```

Activer le debug SMTP (utile pour vérifier l'envoi) :

```
SMTP_DEBUG=true
```

## Lancer un check manuel

```zsh
python run_check.py --dry-run
```

Pour envoyer l'email :

```zsh
python run_check.py
```

Forcer l'envoi d'un email même sans changement :

```zsh
python run_check.py --force-send
```

Envoyer un récap quotidien (toutes les offres + nouvelles) :

```zsh
python run_check.py --daily
```

## Planifier avec cron (macOS)

```zsh
crontab -e
```

Ajoute une ligne (toutes les 30 minutes) :

```zsh
*/30 * * * * /Users/$USER/Documents/dev/vie-alert-bot/.venv/bin/python /Users/$USER/Documents/dev/vie-alert-bot/run_check.py
```

Pour un récap quotidien à 8h :

```zsh
0 8 * * * /Users/$USER/Documents/dev/vie-alert-bot/.venv/bin/python /Users/$USER/Documents/dev/vie-alert-bot/run_check.py --daily
```

Note : le bot ne peut pas tourner si l'ordinateur est éteint ou sans connexion.

## Exécution 24/7 gratuite (GitHub Actions)

1) Pousse le projet sur GitHub.
2) Ajoute les secrets dans **Settings → Secrets and variables → Actions** :

- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASS`
- `SMTP_FROM`
- `SMTP_TO`
- `SMTP_STARTTLS`
- `OFFERS_API_ENDPOINT` (optionnel)

Le workflow `.github/workflows/vie-alert.yml` lance le script **toutes les 15 minutes**.

## Notes

- Les offres sont récupérées via l'API Civiweb pour obtenir la liste complète.
- L'état est enregistré dans `data/state.json` avec les offres vues.

