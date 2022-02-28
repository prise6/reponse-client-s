"""Module pour ingérer les données et les formater"""

from typing import Dict, List, Union
import logging
import re
import os
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def _clean_json(string):
    """
    from https://stackoverflow.com/questions/23705304/can-json-loads-ignore-trailing-commas
    """
    string = re.sub(r",[ \t\r\n]+}", "}", string)
    string = re.sub(r",[ \t\r\n]+\]", "]", string)

    return string


def _clean_str_col(col: pd.Series):
    return col.str.lower()\
        .str.strip()\
        .str.replace(r'\\x\w{2}', '', regex=True)\
        .replace(r'^\s*$', np.NaN, regex=True)


def read_and_format_drugs(drug_filename: str) -> pd.DataFrame:
    logger.info(f'Drugs: lecture du fichier csv {drug_filename} ...')
    drugs = pd.read_csv(drug_filename)

    logger.info('Drugs: format des colonnes ...')
    drugs.drug = _clean_str_col(drugs.drug)
    drugs = drugs.rename(columns={'drug': 'name'})
    drugs_deduplicated = drugs.drop_duplicates('name')
    if drugs_deduplicated.shape != drugs.shape:
        logger.info('Drugs: des doublons sont présents dans la base...')
        drugs = drugs_deduplicated
        logger.info('Drugs: les doublons ont été supprimés.')

    return drugs


def read_and_format_pubmed(pubmed_filename: Union[str, List[str]]) -> pd.DataFrame:
    dtypes_args = {'id': str, 'title': str, 'journal': str}
    str_cols = ['id', 'title', 'journal']
    if isinstance(pubmed_filename, list):
        pubmed_data = pd.concat([read_and_format_pubmed(f) for f in pubmed_filename])
    else:
        logger.info(f'Pubmed: lecture du fichier pubmed {pubmed_filename} ...')
        if pubmed_filename.endswith('.json'):
            with open(pubmed_filename, "r") as f:
                content = f.read()
                pubmed_data = pd.read_json(_clean_json(content), dtype=dtypes_args, convert_dates='date')
        elif pubmed_filename.endswith('.csv'):
            pubmed_data = pd.read_csv(pubmed_filename, dtype=dtypes_args, parse_dates=['date'])
        else:
            raise ValueError("Pubmed: l'extension du fichier est inconnu")
        pubmed_data[str_cols] = pubmed_data[str_cols].apply(_clean_str_col, axis=1)

    pubmed_data_deduplicated = pubmed_data.drop_duplicates('title')
    if pubmed_data_deduplicated.shape != pubmed_data.shape:
        logger.info('Pubmed: des doublons par titre sont présents dans la base...')
        pubmed_data = pubmed_data_deduplicated
        logger.info('Pubmed: les doublons ont été supprimés.')

    pubmed_data = pubmed_data.rename(columns={'id': 'base_id'})

    return pubmed_data


def read_and_format_clinical_trials(clinical_trial_filename: str) -> pd.DataFrame:
    logger.info(f'Trial: lecture du fichier csv {clinical_trial_filename} ...')
    clinical_trials = pd.read_csv(clinical_trial_filename, dtype={'id': str, 'scientific_title': str, 'journal': str}, parse_dates=['date'])
    clinical_trials = clinical_trials.rename(columns={'scientific_title': 'title'})

    logger.info('Trial: format des colonnes ...')
    clinical_trials[['title', 'journal']] = clinical_trials[['title', 'journal']].apply(_clean_str_col, axis=1)

    logger.info('Trial: suppression des clinical_trials avec titre vide ...')
    clinical_trials = clinical_trials[(clinical_trials.title != "") & (~clinical_trials.title.isnull())]

    clinical_trials_deduplicated = clinical_trials.drop_duplicates('title')
    if clinical_trials_deduplicated.shape != clinical_trials.shape:
        logger.info('Trial: des doublons sont présents dans la base...')
        clinical_trials = clinical_trials_deduplicated
        logger.info('Trial: les doublons ont été supprimés.')

    clinical_trials = clinical_trials.rename(columns={'id': 'base_id'})

    return clinical_trials


def create_journal_df(clinical_trials: pd.DataFrame, pubmeds: pd.DataFrame) -> pd.DataFrame:
    logger.info("Journal: création de la base journal de référence")
    return pd.concat([clinical_trials[['journal']], pubmeds[['journal']]])\
        .drop_duplicates()\
        .dropna()\
        .sort_values(by='journal')\
        .rename(columns={'journal': 'name'})


def export_dfs_to_json(output_directory: str, dict_name_df: Dict[str, pd.DataFrame]) -> None:
    logger.info("Export des fichiers ...")
    for name, df in dict_name_df.items():
        logger.info(f"export du fichier {name}")
        df.to_json(os.path.join(output_directory, f"{name}.json"), orient='records', date_format='iso')
    return
