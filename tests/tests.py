#!/usr/bin/env python

"""Tests pour les classes entities dans le package clients"""

import unittest
from clients.graph import ClinicalTrial, Drug, Graph, Journal, MentionnedLink, Publication, PublishedLink


class TestNode(unittest.TestCase):
    """Exemples de tests unitaires sur les classes clients.graph"""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_drug_node(self):
        node = Drug(id=0, name="drug A ", atccode="atccode A")
        self.assertEqual(node.name, "drug a")

    def test_publish_link_node_a(self):
        node_1 = Drug(id=1, name="drug A ", atccode="atccode A")
        node_2 = Journal(id=2, name="journal A")
        node_3 = Publication(id=3, title="publication A", date="2022/03/01")
        with self.assertRaises(TypeError):
            PublishedLink(node_1, node_2)
        with self.assertRaises(TypeError):
            PublishedLink(node_2, node_1)

        publish_link = PublishedLink(node_2, node_3)
        self.assertEqual(publish_link.id, '2_3')


class GraphTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:

        drug_infos = [{"atccode": "A04AD", "name": "diphenhydramine"}, {"atccode": "S03AA", "name": "tetracycline"}]
        pubmed_infos = [{"base_id":"1","title":"a 44-year-old man with erythema of the face diphenhydramine, neck, and chest, weakness, and palpitations","date":"2019-01-01T00:00:00.000Z","journal":"journal of emergency nursing"}] # noqa
        clinical_trials_infos = [{"base_id":"NCT01967433","title":"use of diphenhydramine as an adjunctive sedative for colonoscopy in patients chronically on opioids","date":"2020-01-01T00:00:00.000Z","journal":"journal of emergency nursing"},{"base_id":"NCT04189588","title":"phase 2 study iv quzyttir\u2122 (cetirizine hydrochloride injection) vs v diphenhydramine","date":"2020-01-01T00:00:00.000Z","journal":"journal of emergency nursing"}] # noqa
        journal_infos = [{"name":"journal of emergency nursing"}] # noqa

        g = Graph()
        drug_nodes = g._build_nodes_from_list(drug_infos, Drug)
        g._build_nodes_from_list(journal_infos, Journal)
        publication_nodes = g._build_nodes_from_list(pubmed_infos, Publication)
        clinical_trial_nodes = g._build_nodes_from_list(clinical_trials_infos, ClinicalTrial)

        g._build_mentions(drug_nodes, publication_nodes, clinical_trial_nodes)
        cls.graph = g
        return super().setUpClass()

    def test_drugs_mentions(self):
        res = self.graph.get_drugs_mentions(drug_names=['diphenhydramine'])
        self.assertEqual(len(res['diphenhydramine']), 4)

        # une mention journal
        tmp = [link for link in res['diphenhydramine'] if link.mention_type == MentionnedLink.MENTION_JOURNAL]
        self.assertEqual(len(tmp), 1)

        # une mention publication
        tmp = [link for link in res['diphenhydramine'] if link.mention_type == MentionnedLink.MENTION_PUBLICATION]
        self.assertEqual(len(tmp), 1)

        # deux mentions clinical_trials
        tmp = [link for link in res['diphenhydramine'] if link.mention_type == MentionnedLink.MENTION_CLINICAL_TRIAL]
        self.assertEqual(len(tmp), 2)
