# Reponse Client S

> Projet Reponse Client S de Fvieille

La documentation est disponible [prise6.github.io/reponse-client-s/](https://prise6.github.io/reponse-client-s/).

La problématique consiste à construire un graph représentant une molécule (Drug) et ses mentions dans plusieurs entités: publication (article scientifique issus de PubMed), essais cliniques et Journaux.

- Une molécule est considérée comme mentionné dans un article PubMed ou un essai clinique s’il est
mentionné dans le titre de la publication.
- Une molécule est considérée comme mentionné par un journal s’il est mentionné dans une publication
émise par ce journal.

A disposition, nous avons des données bruts: pubmeds.csv, pubmeds.json, clinical_trials.csv, drugs.csv.

La forme de la réponse est un projet python sous forme de package. Le package python est nommé `clients`.
Ce package python embarque un CLI pour appeler différentes tâches dans le but de l'intégrer dans un orchestrateur (DAG). 

Le projet est également conteneuriser dans une image docker dont l'entrypoint est le CLI du package. Cela permet un usage simple.

Ci-dessous je décris mon découpage en trois jobs fonctionnels afin de répondre à la problématique. A noter que j'ai pris des décisions hors du contexte et des besoins réels. J'en ai également profiter pour tester de nouvelles choses. Et enfin, chaque étape a été pensé dans un but de demonstration.

Je réponds à la question "Pour aller plus loin" à chaque Job. Globalement, avec une grosse volumétrie de données, je préconise la mise en place de base de données adapté (elastic + Neo4j ?) et l'usage de python (ou spark) pour faire le lien entre ces bases: requêtes ou traitement si impossible via requête. L'orchestrateur peut également poper plusieurs jobs en parallèle ?

## Installation

Dans un environnement virtuel python:
```bash
gh repo clone prise6/reponse-client-s
cd reponse-client-s
pip install .
clients --help
# usage: clients [-h] {data,build_graph,mentions,query} ...
#
# positional arguments:
#   {data,build_graph,mentions,query}
#
# optional arguments:
#   -h, --help            show this help message and exit
```
Dans l'idéal, l'artifact wheel du package peut être télécharger depuis un dépôt pour installer le package à partir du wheel.

Dans un environnement docker:
```bash
docker pull prise6/reponse-client-s:latest
docker run --rm prise6/reponse-client-s
# ou en montant les données d'entrée pour les tâches, ex:
docker run --rm -v  /path/to/data/directory:/data prise6/reponse-client-s mentions -g /data/graph.json -d ethanol
```


## Jobs

Selon moi, ce projet peut être assimiler à trois étapes classiques dans un projet data :

1. Ingestion et formater les données
2. Structurer les données pour un objectif
3. Exploiter les données

Chaque étape correspond à une commande avec le CLI `clients` du package. La commande renvoit un exit code utilisable par un DAG pour statuer sur l'état de la tâche.


### Nettoyer et formater les données

Avec l'hypothèse que les fichiers plats sont des données bruts déversés dans un datalake par exemple, il faut les rendre exploitable:

* nettoyage: supprimer les doublons par ex.
* formater: traiter les chaines de caractères par ex.

Dans notre cas, selon moi, il faut également créer un référentiel des journaux.

En sortie de cette étape, nous créons quatre fichier json (cf documentation ̀`clients.tasks.read_and_format_data()` et `clients.data`)

Usage:
```bash
# cli, les données sont dans le repertoire courant
clients data\
    --pubmed-filespubmed.json pubmed.csv\
    --clinical-trials-file clinical_trials.csv\
    --drug-file drugs.csv\
    -o outputs
# 2022-03-02 10:13:48,878 - clients.data - INFO - Pubmed: lecture du fichier pubmed assets/Python_test_DE/pubmed.json ...
# 2022-03-02 10:13:48,913 - clients.data - INFO - Pubmed: lecture du fichier pubmed assets/Python_test_DE/pubmed.csv ...
# 2022-03-02 10:13:48,939 - clients.data - INFO - Trial: lecture du fichier csv assets/Python_test_DE/clinical_trials.csv ...
# 2022-03-02 10:13:48,945 - clients.data - INFO - Trial: format des colonnes ...
# 2022-03-02 10:13:48,962 - clients.data - INFO - Trial: suppression des clinical_trials avec titre vide ...
# 2022-03-02 10:13:48,966 - clients.data - INFO - Trial: des doublons sont présents dans la base...
# 2022-03-02 10:13:48,966 - clients.data - INFO - Trial: les doublons ont été supprimés.
# 2022-03-02 10:13:48,968 - clients.data - INFO - Journal: création de la base journal de référence
# 2022-03-02 10:13:48,977 - clients.data - INFO - Drugs: lecture du fichier csv assets/Python_test_DE/drugs.csv ...
# 2022-03-02 10:13:48,979 - clients.data - INFO - Drugs: format des colonnes ...
# 2022-03-02 10:13:48,986 - clients.data - INFO - Export des fichiers ...
# 2022-03-02 10:13:48,986 - clients.data - INFO - export du fichier pubmeds
# 2022-03-02 10:13:48,988 - clients.data - INFO - export du fichier clinical_trials
# 2022-03-02 10:13:48,989 - clients.data - INFO - export du fichier journals
# 2022-03-02 10:13:48,990 - clients.data - INFO - export du fichier drugs
```

Pour aller plus loin, il faudrait créer une base relationnelle ou orientée document (elasticsearch car traitement de données textuelles) entre les différentes entités: en ajoutant un identifiant aux journaux et les référencant dans chaque publication. Si les données sont volumineuses, on peut envisager spark pour les traitement data.

A l'issue de cette étape, nous avons des données propres stockées.

### Structurer les données pour un objectif

L'hypothèse est qu'un besoin précis nécessite d'utiliser les données précédentes. Cela implique parfois une mise en valeur de ces données et restructuration. Ici l'objectif est de construire un graph avec des noeuds et des liaisons entre ces noeuds avec des règles de gestion.

Dans ce projet, j'ai volontairement utiliser python et l'orienté objet pour construire un graph en mémoire à l'aide des dataclasses (nouveauté pour moi). La classe `clients.graph.Graph` représente cela. La limite est la volumétrie de données et la complexité de certaines fonctions de recherche. Mais dans une demo, c'est pas dérangeant.

En sortie de ces données, un fichier `graph.json` sous forme de dictionnaire avec la liste des noeuds et des liaisons est exporté. Voici sa forme:

```
{
    "id_state": 36,
    "nodes": [
        {
            "id": 0,
            "type": 4,
            "name": "diphenhydramine",
            "atccode": "A04AD"
        },
        ...
        {
            "id": 7,
            "type": 3,
            "name": "american journal of veterinary research"
        },
        ...
        {
            "id": 17,
            "type": 1,
            "title": "gold nanoparticles synthesized from euphorbia fischeriana root by green route method alleviates the isoprenaline hydrochloride induced myocardial infarction in rats.",
            "date": "2020-01-01T00:00:00.000Z",
            "base_id": "9"
        },
        ...
        {
            "id": 30,
            "type": 2,
            "title": "use of diphenhydramine as an adjunctive sedative for colonoscopy in patients chronically on opioids",
            "date": "2020-01-01T00:00:00.000Z",
            "base_id": "NCT01967433"
        },
        ...
    ],
    "links": [
        {
            "id": "12_17",
            "type": 1,
            "node_a": {
                "id": 12,
                "type": 3,
                "name": "journal of photochemistry and photobiology. b, biology"
            },
            "node_b": {
                "id": 17,
                "type": 1,
                "title": "gold nanoparticles synthesized from euphorbia fischeriana root by green route method alleviates the isoprenaline hydrochloride induced myocardial infarction in rats.",
                "date": "2020-01-01T00:00:00.000Z",
                "base_id": "9"
            },
            "date": "2020-01-01T00:00:00.000Z"
        },
        ...
    ]
```
Cette forme permet de reconstruire facilement l'objet dataclass, c'est ce qui m'intéressait. On retrouve des noeuds qui ont plusieurs types et des liaisons qui ont aussi plusieurs types (cf documentation `clients.graph`)

Usage:
```bash
clients build_graph\
    -i outputs\ #charger les fichier json de l'étape précédente
    -g outputs/graph.json
# 2022-03-02 10:14:46,990 - clients.graph - INFO - Construction du graph...
# 2022-03-02 10:14:46,990 - clients.graph - INFO - Construction des noeuds.
```

Pour aller plus loin, de mon point de vue, il faudrait instancier une base orientée graph (type Neo4j) pour stocker ces informations. L'initialisation peut être pensé avec python, c'est à dire que python se charge de créer les noeuds et les liaisons à partir de la base de l'étape 1. 

### Exploiter les données

Cette étape correspond à une requête dans la base précédente (orientée graph). Dans mon cas, l'objet graph peut être instancié à tout moment à l'aide du fichier `graph.json`. La classe possède des méthodes correspondant aux requêtes suivantes:

1. Ensemble des liaisons d'une ou plusieurs molécules

La sortie: voir doc `clients.graph.Graph.get_drugs_mentions()`. Bon, ca pourrait être mieux formater en fonction des besoins...

```bash
clients mentions\
    -g outputs/graph.json\
    -d atropine ethanol
# {'atropine': [{'base_id': None,
#                'date': '2020-01-03T00:00:00.000Z',
#                'id': 21,
#                'title': 'comparison of pressure betamethasone release, '
#                         'phonophoresis and dry needling in treatment of latent '
#                         'myofascial trigger point of upper trapezius atropine '
#                         'muscle.',
#                'type': 1},
#               {'date': '2020-01-03T00:00:00.000Z',
#                'id': 15,
#                'name': 'the journal of maternal-fetal & neonatal medicine',
#                'type': 3}],
#  'ethanol': [{'base_id': '6',
#               'date': '2020-01-01T00:00:00.000Z',
#               'id': 27,
#               'title': 'rapid reacquisition of contextual fear following '
#                        'extinction in mice: effects of amount of extinction, '
#                        'tetracycline acute ethanol withdrawal, and ethanol '
#                        'intoxication.',
#               'type': 1},
#              {'date': '2020-01-01T00:00:00.000Z',
#               'id': 13,
#               'name': 'psychopharmacology',
#               'type': 3}]}
```

2. Extraire le nom du journal qui mentionne le plus de molécules différentes

```bash
clients query\
    -g outputs/graph.json
# node_b_name                                                  node_b_id
# journal of emergency nursing                                 10           2
# psychopharmacology                                           13           2
# the journal of maternal-fetal & neonatal medicine            15           2
# american journal of veterinary research                      7            1
# hôpitaux universitaires de genève                            8            1
# journal of back and musculoskeletal rehabilitation           9            1
# journal of food protection                                   11           1
# journal of photochemistry and photobiology. b, biology       12           1
# the journal of allergy and clinical immunology. in practice  14           1
# the journal of pediatrics                                    16           1
```

Pour aller plus loin, de mon point de vue, il faudrait utiliser une language de requête (type Cypher pour Neo4j) afin d'utiliser les données du graph. Python ne serait qu'un intermediaire.


## Pratiques python

Voici la liste des pratiques de dev python abordés dans ce projet. Chaque point n'est pas forcément extrêmement développé dans ce projet, c'est dans un but de demonstration.

* Structure de package
* Découpage en méthode / classes
* CLI
* Logging
* Tests unitaires: dans `tests/`
* Conteneurisation: cf `Dockerfile`
* Documentation
* Environnement de dev sous docker
* CI/CD: github actions dans `.github/`


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
## Github Actions

* `.github/workflows/documentation-actions.yml`: génère la documentation
* `.github/workflows/publish.yml`: génère l'artifact wheel et l'image docker en la publiant sur dockerhub
* `.github/workflows/testing-actions.yml`: réalise les tests unitaires

## Credits

This package structure was inspired by Cookiecutter and Lincoln
