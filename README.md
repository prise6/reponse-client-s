# Reponse Client

> Projet Reponse Client de Fvieille

* Auteur: Fvieille
* Date de création: 2022-02-23
* voir [AUTHORS.md](./AUTHORS.md)

## Table des matières

1. [Les répertoires](#les-répertoires)
2. [Les fichiers importants](#les-fichiers-importants)
3. [To-Do](#to-do)
3. [Tester](#tester)
4. [Contribuer](#contribuer)
5. [Historique](#historique)

## Les répertoires

```bash
.
├── reponse-client-s       # module principal
├── requirements/       # dossier contenant les requirements python
├── tests/              # dossier contenant les tests du package
├── logs/               # dossier contenant les logs : dev specific
├── scripts/            # dossier contenant les scripts utilisant le package
├── docs/               # documentations générées par sphinx
├── .devcontainer/      # dossier contenant les configurations docker
```

## Les fichiers importants

```bash
.
├── Reponse Client
│   ├── __init__.py                 # topc level package
├── .devcontainer/                  # (optionnel)
│   ├── devcontainer.json           # configuration du remote docker pour vscode
│   ├── Dockerfile-dev              # Dockerfile de dev
├── README.md                       # this file
├── HISTORY.md                      # historique des version et les modifications
├── CONTRIBUTING.md                 # comment contribuer au projet
├── LICENSE                         # license si besoin
├── Makefile                        # Makefile: aide à la compilation
├── .gitignore                      # Liste des éléments que git doit ignorer lors du commit
├── requirements.txt                # Contient les dépendances (=packages) pyhton du projet
├── setup.cfg                       # aide au setup.py
├── setup.py                        # setup.py pour créer un package python
├── tox.ini                         # aide pour les tests
├── docker-compose.yaml             # docker-compose du projet (optionnel)
├── docker-compose-dev.yaml         # docker-compose de dev du projet (optionnel)
├── Dockerfile                      # construction de l'image (optionnel)
├── .env                            # variable d'environnement (optionnel)
```

## To-Do

* _Rédiger la documentation_
* ...


## Tester

En utilisant `tox.ini`:

```bash
# dans le projet:
tox
```

## Contribuer

Voir [CONTRIBUTING.md](./CONTRIBUTING.md)


## Historique

Voir [HISTORY.md](./HISTORY.md)


## Credits

This package was inspired by Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

*  _Cookiecutter: https://github.com/audreyr/cookiecutter
*  _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage

