"""Modules de définition des entités du projet"""

from typing import ClassVar, Optional, Union, List, Dict
import json
from abc import ABC
from dataclasses import dataclass, field
import dataclasses
import dacite
from pprint import pprint
import logging


logger = logging.getLogger(__name__)


@dataclass
class Node(ABC):
    id: int = field(init=True)
    type: int = field(init=False)

    PUBLICATION_NODE: ClassVar[int] = 1
    CLINICAL_TRIAL_NODE: ClassVar[int] = 2
    JOURNAL_NODE: ClassVar[int] = 3
    DRUG_NODE: ClassVar[int] = 4

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    def to_json(self):
        raise NotImplementedError


@dataclass
class Drug(Node):
    type: int = field(default=Node.DRUG_NODE, init=False)
    name: str
    atccode: str

    def __post_init__(self) -> None:
        self.name = self.name.lower().strip()

    def is_name_mentionned(self, content: str) -> bool:
        return self.name in content


@dataclass
class Publication(Node):
    type: int = field(default=Node.PUBLICATION_NODE, init=False)
    title: str
    date: Optional[str] = None
    base_id: Optional[int] = None


@dataclass
class ClinicalTrial(Node):
    type: int = field(default=Node.CLINICAL_TRIAL_NODE, init=False)
    title: str
    date: Optional[str] = None
    base_id: Optional[str] = None


@dataclass
class Journal(Node):
    type: int = field(default=Node.JOURNAL_NODE, init=False)
    name: str


@dataclass
class Link(ABC):
    id: str = field(init=False)
    type: int = field(init=False)
    node_a: Node
    node_b: Node
    date: Optional[str] = None

    PUBLISHED_LINK: ClassVar[int] = 1
    MENTIONNED_LINK: ClassVar[int] = 2

    def __post_init__(self):
        self.build_id()

    def build_id(self) -> None:
        self.id = str(self.node_a.id) + "_" + str(self.node_b.id)

    def to_dict(self):
        return dataclasses.asdict(self)

    def to_json(self):
        raise NotImplementedError


class PublishedLink(Link):
    node_a: Journal
    node_b: Union[ClinicalTrial, Publication]

    def __post_init__(self) -> None:
        if not isinstance(self.node_a, Journal):
            raise TypeError("node_a must be instance of Journal")
        if not isinstance(self.node_b, ClinicalTrial) and not isinstance(self.node_b, Publication):
            raise TypeError("node_b must be instance of Publication or ClinicalTrial")
        self.type = Link.PUBLISHED_LINK
        self.date = self.node_b.date
        return super().__post_init__()


class MentionnedLink(Link):
    node_a: Drug
    node_b: Union[ClinicalTrial, Publication, Journal]
    mention_type: str = field(init=False)

    MENTION_CLINICAL_TRIAL: ClassVar[str] = "clinical_trial"
    MENTION_PUBLICATION: ClassVar[str] = "publication"
    MENTION_JOURNAL: ClassVar[str] = "journal"

    def __post_init__(self):
        if not isinstance(self.node_a, Drug):
            raise TypeError("node_a must be instance of Drug")

        if isinstance(self.node_b, Publication):
            self.mention_type = MentionnedLink.MENTION_PUBLICATION
        elif isinstance(self.node_b, ClinicalTrial):
            self.mention_type = MentionnedLink.MENTION_CLINICAL_TRIAL
        elif isinstance(self.node_b, Journal):
            self.mention_type = MentionnedLink.MENTION_JOURNAL
        else:
            raise TypeError("node_b must be instance of Publication, ClinicalTrial or Journal")
        self.type = Link.MENTIONNED_LINK
        return super().__post_init__()


@dataclass
class Graph():
    id_state: int = field(default=0, init=False)
    nodes: List[Union[Drug, Journal, Publication, ClinicalTrial]] = field(default_factory=list, init=False)
    links: List[Union[MentionnedLink, PublishedLink]] = field(default_factory=list, init=False)
    _journals_lookup: Dict[str, Journal] = field(default_factory=dict, init=False, repr=False)
    _links_id: List[str] = field(default_factory=list, init=False, repr=False)

    @property
    def journals_lookup(self) -> dict:
        if not self._journals_lookup:
            self.journals_lookup = {node.name: node for node in self.nodes if node.type == Node.JOURNAL_NODE}
        return self._journals_lookup

    @journals_lookup.setter
    def journals_lookup(self, journals_lookup: Dict[int, Journal]) -> None:
        if not isinstance(journals_lookup, dict):
            raise TypeError('journal_lookup must be instance of dict of Journal')
        self._journals_lookup = journals_lookup

    def look_for_drug_by_names(self, names: List[str]) -> List[Drug]:
        return [drug for drug in self.nodes if drug.type == Node.DRUG_NODE and drug.name in names]

    def look_for_links_by_nodes(self, nodes: List[Node], link_type: int = None) -> List[Link]:
        nodes_ids = [node.id for node in nodes]
        results_links: List[Link] = []
        results_links = [link for link in self.links if (link.node_a.id in nodes_ids or link.node_b.id in nodes_ids)]
        if link_type:
            results_links = [link for link in results_links if link.type == link_type]
        return results_links

    def look_for_journal(self, name: str) -> Optional[Journal]:
        if not isinstance(name, str):
            return
        if name in self.journals_lookup:
            return self.journals_lookup[name]
        return

    def look_for_journal_link(self, node_b_id: int) -> Optional[Journal]:
        for journal_link in self.links:
            if journal_link.type == Link.PUBLISHED_LINK:
                if journal_link.node_b.id == node_b_id:
                    return journal_link
        return

    def get_id_and_increment(self) -> int:
        self.id_state += 1
        return self.id_state - 1

    def build_graph(self, drug_file: str, journal_file: str, pubmed_file: str, clinical_trial_file: str) -> "Graph":
        logger.info("Construction du graph...")

        logger.info("Construction des noeuds.")
        # build nodes
        # -> Drug
        drug_nodes: List[Drug] = self.build_nodes_from_json_file_(drug_file, Drug)
        # -> Journal
        journal_nodes: List[Journal] = self.build_nodes_from_json_file_(journal_file, Journal) # noqa
        # -> Publication
        publication_nodes: List[Publication] = self.build_nodes_from_json_file_(pubmed_file, Publication)
        # -> ClinicalTrial
        clinical_trial_nodes: List[ClinicalTrial] = self.build_nodes_from_json_file_(clinical_trial_file, ClinicalTrial)

        self._build_mentions(drug_nodes, publication_nodes, clinical_trial_nodes)

        return self

    def build_nodes_from_json_file_(self, filename: str, cls) -> List[Node]:
        with open(filename, 'r') as f:
            json_content = json.load(f)
        return self._build_nodes_from_list(json_content, cls)

    def _build_nodes_from_list(self, content: List[dict], cls) -> List[Node]:
        current_nodes: List[Node] = []

        for infos in content:
            journal_node = None
            journal_name = None
            if cls.__name__ in ['Publication', 'ClinicalTrial'] and 'journal' in infos:
                journal_name = infos.pop('journal')
                # /!\ don't create journal node if doesn't exist
                journal_node = self.look_for_journal(journal_name)

            node = cls(
                id=self.get_id_and_increment(),
                **infos
            )
            logger.debug(f"Construction du noeud {node}.")

            if journal_node:
                self._build_link(journal_node, node, node.date, PublishedLink)

            current_nodes.append(node)

        self.nodes += current_nodes

        return current_nodes

    def _build_mentions(self, drug_nodes: List[Drug], publication_nodes: List[Publication],
                        clinical_trial_nodes: List[ClinicalTrial]) -> None:
        logger.info("Construction des mentions.")
        # build links with publications and clinical trials
        for d_node in drug_nodes:
            for node_with_title in publication_nodes + clinical_trial_nodes:
                if d_node.is_name_mentionned(node_with_title.title):
                    self._build_link(d_node, node_with_title, node_with_title.date, MentionnedLink)

        # build links with journals
        for link in self.links:
            if link.type != Link.MENTIONNED_LINK:
                continue
            if link.mention_type == MentionnedLink.MENTION_CLINICAL_TRIAL or \
               link.mention_type == MentionnedLink.MENTION_PUBLICATION:
                journal_link = self.look_for_journal_link(link.node_b.id)
                if not journal_link:
                    continue
                self._build_link(link.node_a, journal_link.node_a, journal_link.node_b.date, MentionnedLink)
        return

    def _build_link(self, node_a: Node, node_b: Node, date: str, cls) -> None:
        current_link = cls(node_a, node_b, date)
        logger.debug(f'Création du lien {current_link}')
        if current_link.id not in self._links_id:
            self.links.append(current_link)
            self._links_id.append(current_link.id)
        return

    def get_drugs_mentions(self, drug_names: List[str], verbose: bool = True) -> Dict[str, MentionnedLink]:
        drug_mentions: Dict[str, MentionnedLink] = {}
        pretty_drug_mentions = {}

        drug_nodes = self.look_for_drug_by_names(drug_names)
        for drug_node in drug_nodes:
            links = self.look_for_links_by_nodes([drug_node], Link.MENTIONNED_LINK)
            drug_mentions.update({drug_node.name: links})

        if verbose:
            for drug_name, drug_links in drug_mentions.items():
                pretty_drug_mentions.update({
                    drug_name: [{**dataclasses.asdict(drug_mention.node_b), **{'date': drug_mention.date}} for drug_mention in drug_links]
                })
            pprint(pretty_drug_mentions)

        return drug_mentions

    def to_dict(self) -> List[dict]:
        return dataclasses.asdict(self)

    def to_json(self, output_file: str) -> None:
        with open(output_file, 'w') as f:
            json.dump(self.to_dict(), f, indent=True)

    @staticmethod
    def from_dict(graph_dict: dict) -> "Graph":
        return dacite.from_dict(Graph, graph_dict)

    @staticmethod
    def from_json(input_file: str) -> "Graph":
        graph_dict = {}
        with open(input_file, 'r') as f:
            graph_dict = json.load(f)
        return Graph.from_dict(graph_dict)
