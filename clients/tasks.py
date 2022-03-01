"""Module des jobs pour le cli"""

from typing import List, Optional
import logging
import os
from clients.data import (read_and_format_pubmed, read_and_format_clinical_trials,
                          read_and_format_drugs, create_journal_df, export_dfs_to_json)
from clients.graph import Graph, MentionnedLink
import dataclasses
import pandas as pd

logger = logging.getLogger(__name__)


def read_and_format_data(pubmed_files: List[str], clinical_trials_file: str, drug_file: str,
                         output_directory: str) -> None:
    """Job data de lecture et format des données à partir des fichiers bruts.
    Sauvegarde les données sous format json dans `output_directory`:

    * pubmeds.json
    * clinical_trials.json
    * drugs.json
    * journals.json

    Cette étape peut être découpée si besoin. L'hypothèse est que les données bruts doivent
    être nettoyées et consolider afin d'être exploitées par la suite.
    Dans la réalité, les données bruts sont souvent déversés dans un datalake puis structurer
    (nettoyage, création d'identifiant, base relationnel, ...) dans un stockage adapté et requêtable.

    Args:
        pubmed_files (List[str]): chemins des données bruts
        clinical_trials_file (str): chemin des données bruts
        drug_file (str): chemin des données bruts
        output_directory (str): répertoire de sauvegarde des données json
    """
    try:
        pubmeds = read_and_format_pubmed(pubmed_files)
        clinical_trials = read_and_format_clinical_trials(clinical_trials_file)
        journals = create_journal_df(clinical_trials, pubmeds)
        drugs = read_and_format_drugs(drug_file)
    except Exception:
        logger.error("Une erreur est survenue pendant le formattage des données.")
        raise
    try:
        export_dfs_to_json(output_directory, {
            'pubmeds': pubmeds,
            'clinical_trials': clinical_trials,
            'journals': journals,
            'drugs': drugs
        })
    except Exception:
        logger.error("Une erreur est survenue pendant la sauvegarde des données.")
        raise


def export_graph(input_directory: str, json_graph_file: str) -> None:
    """Job de création et export du graph des liaisons entre les différentes entités
    (molécules, publications, essais cliniques, journaux).

    Cette étape correspond à la manipulation métier des données structurées dans un but précis.
    Ici, il est nécessaire de retravailler les données pour les stocker sous un format de graph.
    Idéalement, on devrait s'appuyer sur une base de données orientée graph (Neo4j par ex.) et donc
    modéliser les noeuds et les liaisons dans cette base.

    Ici, j'ai voulu apprendre à utiliser les dataclasses de python, j'en ai profiter avec ce projet
    pour créer une classe Graph et des classes Nodes simples.
    La complexité des recherches de liaisons est forcément impactée si les données sont volumineuses.

    L'object Graph grâce à dataclasses peut être exporté et importé facilement sous forme de dictionnaire
    (et donc json)

    Args:
        input_directory (str): répertoire de sauvegarde des données json du job :func:`~read_and_format_data`
        json_graph_file (str): chemin du fichier json du graph
    """
    try:
        g = Graph()
        g.build_graph(
            drug_file=os.path.join(input_directory, 'drugs.json'),
            journal_file=os.path.join(input_directory, 'journals.json'),
            pubmed_file=os.path.join(input_directory, 'pubmeds.json'),
            clinical_trial_file=os.path.join(input_directory, 'clinical_trials.json')
        )
    except Exception:
        logger.error("Une erreur est survenue pendant la création des données.\
                          Activer le mode debug pour plus d'informations.")
        raise

    try:
        g.to_json(json_graph_file)
    except Exception:
        logger.error("Une erreur est survenue pendant la sauvegarde du graph.")
        raise


def print_drug_mention(json_graph_file: str, drug_names: List[str]) -> None:
    """Afficher les liaisons d'une molécule. Voir :func:`~clients.graph.Graph.get_drugs_mentions`.

    Cette étape correspond à l'exploitation d'une base graph. C'est à dire l'usage de python pour
    requêter en un language adapté la base de données graph (ex cypher pour Neo4j, comme SQL pour le relationnel)

    Args:
        json_graph_file (str): chemin du fichier json du graph
        drug_names (List[str]): liste des molécules
    """
    try:
        g = Graph().from_json(json_graph_file)
    except Exception:
        logger.error("Une erreur est survenue pendant la lecture du graph")
        raise
    g.get_drugs_mentions(drug_names, verbose=True)


def export_journals_with_distinct_mention(json_graph_file: str) -> Optional[pd.DataFrame]:
    """Retourne une tableau de données des journaux avec le nombre distinct de molécules mentionnées.

    Correspond à une étape d'exploitation d'une base prête à l'emploi également.

    Args:
        json_graph_file (str): chemin du fichier json du graph

    Returns:
        Optional[pd.DataFrame]: Tableau de données
    """
    try:
        g = Graph().from_json(json_graph_file)
    except Exception:
        logger.exception("Une erreur est survenue pendant la lecture du graph")
        raise
    journal_mention_links = [dataclasses.asdict(link) for link in g.links
                             if isinstance(link, MentionnedLink) and link.mention_type == MentionnedLink.MENTION_JOURNAL]
    journal_links_df = pd.DataFrame.from_dict(pd.json_normalize(journal_mention_links, sep="_"))
    results = journal_links_df.groupby(['node_b_name', 'node_b_id']).node_a_name.nunique().sort_values(ascending=False)

    return results
