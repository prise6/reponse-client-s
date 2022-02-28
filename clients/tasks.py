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
    try:
        pubmeds = read_and_format_pubmed(pubmed_files)
        clinical_trials = read_and_format_clinical_trials(clinical_trials_file)
        journals = create_journal_df(clinical_trials, pubmeds)
        drugs = read_and_format_drugs(drug_file)
    except Exception:
        logger.exception("Une erreur est survenue pendant le formattage des données.")
        return
    try:
        export_dfs_to_json(output_directory, {
            'pubmeds': pubmeds,
            'clinical_trials': clinical_trials,
            'journals': journals,
            'drugs': drugs
        })
    except Exception:
        logger.exception("Une erreur est survenue pendant la sauvegarde des données.")


def export_graph(input_directory: str, json_graph_file: str) -> None:
    try:
        g = Graph()
        g.build_graph(
            drug_file=os.path.join(input_directory, 'drugs.json'),
            journal_file=os.path.join(input_directory, 'journals.json'),
            pubmed_file=os.path.join(input_directory, 'pubmeds.json'),
            clinical_trial_file=os.path.join(input_directory, 'clinical_trials.json')
        )
    except Exception:
        logger.exception("Une erreur est survenue pendant la création des données.\
                          Activer le mode debug pour plus d'informations.")
        return

    try:
        g.to_json(json_graph_file)
    except Exception:
        logger.exception("Une erreur est survenue pendant la sauvegarde du graph.")


def print_drug_mention(json_graph_file: str, drug_names: List[str]) -> None:
    try:
        g = Graph().from_json(json_graph_file)
    except Exception:
        logger.exception("Une erreur est survenue pendant la lecture du graph")
        return
    g.get_drugs_mentions(drug_names, verbose=True)


def export_journals_with_distinct_mention(json_graph_file: str) -> Optional[pd.DataFrame]:
    try:
        g = Graph().from_json(json_graph_file)
    except Exception:
        logger.exception("Une erreur est survenue pendant la lecture du graph")
        return
    journal_mention_links = [dataclasses.asdict(link) for link in g.links
                             if isinstance(link, MentionnedLink) and link.mention_type == MentionnedLink.MENTION_JOURNAL]
    journal_links_df = pd.DataFrame.from_dict(pd.json_normalize(journal_mention_links, sep="_"))
    results = journal_links_df.groupby(['node_b_name', 'node_b_id']).node_a_name.nunique().sort_values(ascending=False)

    return results
