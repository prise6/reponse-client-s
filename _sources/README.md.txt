# Reponse Client S

> Projet Reponse Client S de Fvieille

## Jobs

1. Nettoyer et formater les données
    raw layer -> data layer
2. Structurer les données proche d'un objectif métier
    data layer -> graph
3. Exploiter les données pour une problématique
    graph -> requête


## Pratique python

Voici la liste des pratiques de dev python abordés dans ce projet. Chaque point n'est pas forcément extrêmement développé, c'est dans un but de demonstration.

* structure de package
* découpage en méthode / classes
* CLI
* Logging
* Tests unitaires
* Conteneurisation
* Documentation
* Environnement de dev sous docker
* CI/CD: github actions


## Les répertoires

```bash
.
├── reponse-client-s       # module principal
├── requirements/       # dossier contenant les requirements python
├── tests/              # dossier contenant les tests du package
├── docs/               # documentations générées par sphinx
├── .devcontainer/      # dossier contenant les configurations vscode docker
```

## Les fichiers importants

```bash
.
├── Reponse Client
│   ├── __init__.py                 # top level package
│   ├── cli.py                      # CLI
│   ├── data.py                     # module data
│   ├── graph.py                    # module graph
│   ├── tasks.py                    # module task (jobs)
├── .devcontainer/                  # (optionnel)
│   ├── devcontainer.json           # configuration du remote docker pour vscode
│   ├── Dockerfile-dev              # Dockerfile de dev
├── README.md                       # this file
├── Makefile                        # Makefile: aide à la compilation
├── .gitignore                      # Liste des éléments que git doit ignorer lors du commit
├── requirements.txt                # Contient les dépendances (=packages) pyhton du projet
├── setup.cfg                       # aide au setup.py
├── setup.py                        # setup.py pour créer un package python
├── tox.ini                         # aide pour les tests
├── docker-compose-dev.yaml         # docker-compose de dev du projet
├── Dockerfile                      # construction de l'image
├── .env                            # variable d'environnement (optionnel)
```

## Tester

En utilisant `tox.ini`:

```bash
# dans le projet:
tox
# ou 
tox -e py37
```

## Credits

This package structure was inspired by Cookiecutter and Lincoln
