 Vérifiez que chaque étape est claire et directement accessible. Ne laissez aucun espace vide. L'objectif est de produire un document qui est envoyé directement au client.

## CODE
```python
import requests

def claude_review(pr_url):
    # Vérification des paramètres
    if not pr_url.startswith("https://github.com/owner/repo/"):
        return {"error": "URL doit être une URL GitHub"}

    # Lancement du résumé
    response = requests.get(pr_url)
    if response.status_code != 200:
        return {"error": "Erreur lors de l'analyse du PR"}

    # Extraction du code source
    code = response.text
    if "import sys" not in code:
        return {"error": "Le code source n'est pas inclus"}

    # Analyse du code
    # (ajoutez votre logique ici pour analyser le code et générer le commentaire)

    # Résultat final
    return {"review": "..."}

# Exemple d'utilisation
if __name__ == "__main__":
    pr_url = "https://github.com/owner/repo/pull/123"
    result = claude_review(pr_url)
    print(result)
```

## README
```text
# [BOUNTY $150] AGENT: Claude Code

## Description
Le code agent