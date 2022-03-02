"""Modules de définition des entités du projet représenant un Graph"""

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
    """Classe abstraite représentant un noeud du graph

    Attributes:
        id (int): identifiant du noeud
        type (int): identifiant du type de noeud (variable de class \\*_NODE)

    |  PUBLICATION_NODE: 1, noeud de type publication
    |  CLINICAL_TRIAL_NODE: 2, noeud de type essais clinique
    |  JOURNAL_NODE: 3, noeud de type journal
    |  DRUG_NODE: 4, noeud de type molécule

    """
    id: int = field(init=True)
    type: int = field(init=False)

    PUBLICATION_NODE: ClassVar[int] = 1
    CLINICAL_TRIAL_NODE: ClassVar[int] = 2
    JOURNAL_NODE: ClassVar[int] = 3
    DRUG_NODE: ClassVar[int] = 4

    def to_dict(self) -> dict:
        """Retourne les attributs de la classe sous forme de dictionnaire

        Returns:
            dict: clés: id, type
        """
        return dataclasses.asdict(self)


@dataclass
class Drug(Node):
    """Noeud représentant une molécule hérité de Node

    Attributes:
        name (str): nom de la molécule
        atccode (str): identifiant d'origine de la molécule
    """
    type: int = field(default=Node.DRUG_NODE, init=False)
    name: str
    atccode: str

    def __post_init__(self) -> None:

        self.name = self.name.lower().strip()

    def is_name_mentionned(self, content: str) -> bool:
        """Permet de tester si le nom de la molécule est
        contenu dans une chaine de caractère

        Args:
            content (str): chaine de caractère à tester

        Returns:
            bool: retour de la valeur du test
        """
        return self.name in content


@dataclass
class Publication(Node):
    """Noeud représentant une Publication hérité de Node

    Attributes:
        title (str): Titre de la publication
        date (str, None): Date de parution de la publication
        base_id (int, None): Identifiant d'origine de la publication
    """
    type: int = field(default=Node.PUBLICATION_NODE, init=False)
    title: str
    date: Optional[str] = None
    base_id: Optional[int] = None


@dataclass
class ClinicalTrial(Node):
    """Noeud représentant un ClinicalTrial hérité de Node

    Attributes:
        title (str): Titre de l'essai clinique
        date (str, optional): Date de parution de l'essai clinique
        base_id (str, optional): Identifiant d'origine de l'essai clinique
    """
    type: int = field(default=Node.CLINICAL_TRIAL_NODE, init=False)
    title: str
    date: Optional[str] = None
    base_id: Optional[str] = None


@dataclass
class Journal(Node):
    """Noeud représentant un Journal hérité de Node

    Attributes:
        name (str): Titre du journal
    """
    type: int = field(default=Node.JOURNAL_NODE, init=False)
    name: str


@dataclass
class Link(ABC):
    """Classe abstraite représentant une liaison entre deux noeuds

    Attributes:
        id (str): Identifiant unique du lien
        type (int): Identifiant du type de liaison (variable de class \\*_LINK)
        node_a (Node): Noeud A
        node_b (Node): Noeud B
        date (str, optional): Date du lien (pratique pour le cas d'usage)

    |  PUBLISHED_LINK: 1, liaison de type B est publié dans le journal A
    |  MENTIONNED_LINK: 2, liaison de type la molécule A est mentionné dans B

    """
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
        """Construction de l'id de liaison en concaténant
        l'identifiant du noeud A et du noeud B
        """
        self.id = str(self.node_a.id) + "_" + str(self.node_b.id)

    def to_dict(self):
        """Retourne les attributs de la classe sous forme de dictionnaire

        Returns:
            dict: clés: id, type, node_a, node_b, date
        """
        return dataclasses.asdict(self)


class PublishedLink(Link):
    """Liaison représentant la publication d'un essai clinique
    ou d'une publication dans un journal

    Attributes:
        node_a (Journal): Journal
        node_b (Union[ClinicalTrial, Publication]): essai clinique ou publication

    Raises:
        TypeError: node_a must be instance of Journal
        TypeError: node_b must be instance of Publication or ClinicalTrial

    """
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
    """Liaison représentant la mention d'une molécule dans un essai clinique,
    une publication ou un journal

    Attributes:
        node_a (Drug): Noeud représentant la molécule mentionnée
        node_b (Union[ClinicalTrial, Publication, Journal]): Noeud de la mention
        mention_type (str): détails de la mention (MENTION_*)

    |  MENTION_CLINICAL_TRIAL: clinical_trial, la molécule est mentionnée dans un essai clinique
    |  MENTION_PUBLICATION: publication, la molécule est mentionnée dans une publication
    |  MENTION_JOURNAL: journal, la molécule est mentionnée dans un journal

    Raises:
        TypeError: node_a must be instance of Drug
        TypeError: node_b must be instance of Publication, ClinicalTrial or Journal

    """
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
    """Classe représentant un graph composé de noeuds et de liaisons

    Attributes:
        id_state (int): valeur de l'identifiant interne
        nodes (list): ensembe des noeuds du graph
        links (list): ensemble des liaisons du graph
        _journal_lookup (dict): attribut facilitant l'accès aux journaux par titre
        _links_id (list): attribut listant les identifiants des liaisons

    """
    id_state: int = field(default=0, init=False)
    nodes: List[Union[Drug, Journal, Publication, ClinicalTrial]] = field(default_factory=list, init=False)
    links: List[Union[MentionnedLink, PublishedLink]] = field(default_factory=list, init=False)
    _journals_lookup: Dict[str, Journal] = field(default_factory=dict, init=False, repr=False)
    _links_id: List[str] = field(default_factory=list, init=False, repr=False)

    @property
    def journals_lookup(self) -> dict:
        """Getter de l'attribut journals_lookup.
        Construit le dictionnaire si None.

        Returns:
            dict: dictionnaire des journaux (valeur) par titre (clé)
        """
        if not self._journals_lookup:
            self.journals_lookup = {node.name: node for node in self.nodes if node.type == Node.JOURNAL_NODE}
        return self._journals_lookup

    @journals_lookup.setter
    def journals_lookup(self, journals_lookup: Dict[str, Journal]) -> None:
        """Setter de l'attribut journals_lookup.

        Args:
            journals_lookup (dict): dictionnaire des journaux (valeur) par titre (clé)

        Raises:
            TypeError: journals_lookup must be instance of dict of Journal
        """
        if not isinstance(journals_lookup, dict):
            raise TypeError('journals_lookup must be instance of dict of Journal')
        self._journals_lookup = journals_lookup

    def look_for_drug_by_names(self, names: List[str]) -> List[Drug]:
        """Retrouve les noeuds molécule par nom de molécule

        Args:
            names (List[str]): liste des noms de molécule

        Returns:
            List[Drug]: list des objets Drug
        """
        return [drug for drug in self.nodes if drug.type == Node.DRUG_NODE and drug.name in names]

    def look_for_links_by_nodes(self, nodes: List[Node], link_type: int = None) -> List[Link]:
        """Retrouve les liaisons incluant les noeuds en paramètres

        Args:
            nodes (List[Node]): list des noeuds pour la recherche de liaison
            link_type (int, optional): type de liaison à retrouver. Defaults to None.

        Returns:
            List[Link]: list des liaisons retrouvées
        """
        nodes_ids = [node.id for node in nodes]
        results_links: List[Link] = []
        results_links = [link for link in self.links if (link.node_a.id in nodes_ids or link.node_b.id in nodes_ids)]
        if link_type:
            results_links = [link for link in results_links if link.type == link_type]
        return results_links

    def look_for_journal(self, name: str) -> Optional[Journal]:
        """Retrouve un journal par son nom

        Args:
            name (str): nom du journal

        Returns:
            Optional[Journal]: le noeud Journal ou None si non retrouvé
        """
        if not isinstance(name, str):
            return
        if name in self.journals_lookup:
            return self.journals_lookup[name]
        return

    def look_for_journal_link(self, node_b: Union[Publication, ClinicalTrial]) -> Optional[Journal]:
        """Retrouve un journal par sa liaison de publication avec le noeud B,
        autrement dit, si une publication ou un essai clinique est publié dans un journal,
        ce dernier est renvoyé. Recherche non optimisée.

        Args:
            node_b (Union[Publication, ClinicalTrial]): noeud publication ou essai clinique

        Returns:
            Optional[Journal]: le journal ou None sinon
        """
        for journal_link in self.links:
            if journal_link.type == Link.PUBLISHED_LINK:
                if journal_link.node_b.id == node_b.id:
                    return journal_link
        return

    def get_id_and_increment(self) -> int:
        """Retourne l'identifiant interne et l'incrémente ensuite.
        L'identifiant permet d'associer aux noeuds ou liaisons un identifiant unique.

        Returns:
            int: valeur de l'identifiant
        """
        self.id_state += 1
        return self.id_state - 1

    def build_graph(self, drug_file: str, journal_file: str, pubmed_file: str,
                    clinical_trial_file: str) -> "Graph":
        """Methode principale pour construire l'objet graph depuis les fichiers
        json formatté depuis l'étape data et en particulier la fonction :func:`~clients.data.export_dfs_to_json`.
        L'ordre de construction est important pour prendre en compte les liaisons avec les journaux.

        Args:
            drug_file (str): fichier json des molécules
            journal_file (str): fichier json des journaux
            pubmed_file (str): fichier json des publications pubmeds
            clinical_trial_file (str): fichier json des essais cliniqquqes

        Returns:
            Graph: objet graph complet
        """
        logger.info("Construction du graph...")

        logger.info("Construction des noeuds.")
        # build nodes
        # -> Drug
        drug_nodes: List[Drug] = self._build_nodes_from_json_file_(drug_file, Drug)
        # -> Journal
        journal_nodes: List[Journal] = self._build_nodes_from_json_file_(journal_file, Journal) # noqa
        # -> Publication
        publication_nodes: List[Publication] = self._build_nodes_from_json_file_(pubmed_file, Publication)
        # -> ClinicalTrial
        clinical_trial_nodes: List[ClinicalTrial] = self._build_nodes_from_json_file_(clinical_trial_file, ClinicalTrial)

        self._build_mentions(drug_nodes, publication_nodes, clinical_trial_nodes)

        return self

    def _build_nodes_from_json_file_(self, filename: str, cls) -> List[Node]:
        """Methode privée pour construire les noeuds à partir d'un fichier json

        Args:
            filename (str): chemin du fichier json
            cls (__class__): classe du type de noeud (Drug, Publication, ClinicalTrial, Journal)

        Returns:
            List[Node]: list des noeuds construits
        """
        with open(filename, 'r') as f:
            json_content = json.load(f)
        return self._build_nodes_from_list(json_content, cls)

    def _build_nodes_from_list(self, content: List[dict], cls) -> List[Node]:
        """Methode privée pour construire les noeuds à partir d'un dictionnaire.
        Les liens de publications sont également construits en même temps.

        Args:
            content (List[dict]): list de dictionnaire
            cls (__class__): classe du type de noeud (Drug, Publication, ClinicalTrial, Journal)

        Returns:
            List[Node]: list des noeuds construits
        """
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
        """Methode construisant les liens de mention des molécules.

        Args:
            drug_nodes (List[Drug]): liste des noeuds des molécules
            publication_nodes (List[Publication]): liste des noeuds des publications
            clinical_trial_nodes (List[ClinicalTrial]): liste des noeuds des essais cliniques
        """
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
                journal_link = self.look_for_journal_link(link.node_b)
                if not journal_link:
                    continue
                self._build_link(link.node_a, journal_link.node_a, journal_link.node_b.date, MentionnedLink)
        return

    def _build_link(self, node_a: Node, node_b: Node, date: str, cls) -> None:
        """Methode générique pour construire une liaison entre deux noeuds sachant la classe

        Args:
            node_a (Node): noeud A de la liaison
            node_b (Node): noeud B de la liaison
            date (str): date de la liaison
            cls (__class__): PublishedLink, MentionnedLink
        """

        current_link = cls(node_a, node_b, date)
        logger.debug(f'Création du lien {current_link}')
        if current_link.id not in self._links_id:
            self.links.append(current_link)
            self._links_id.append(current_link.id)
        return

    def get_drugs_mentions(self, drug_names: List[str], verbose: bool = True) -> Dict[str, List[MentionnedLink]]:
        """Retourne les liaisons de mention d'une liste de molécule.
        Le format de retour correspond à un dictionnaire:

        |  {
        |      'drug_name': [MentionnedLink, ..., MentionnedLink],
        |      ...
        |  }

        En revanche si verbose = True, ce qui est affiché a le format suivant:

        |  {
        |     'drug_name': [{
        |          'type': ..., # attributs type du noeud qui mentionne la molécule
        |          'date': ...,
        |          'title': ...,
        |          'name': ...,
        |          'id': ...
        |      }, ..., {
        |         'type': ..., # attributs type du noeud qui mentionne la molécule
        |          'date': ...,
        |          'title': ...,
        |          'name': ...,
        |          'id': ...
        |      }],
        |      ...
        |  }

        Args:
            drug_names (List[str]): liste des molécules
            verbose (bool, optional): Defaults to True.

        Returns:
            Dict[str, MentionnedLink]: retourne le dictionnaire de résultats
        """
        drug_mentions: Dict[str, List[MentionnedLink]] = {}
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
        """Convertir l'objet graph en dictionnaire en utilisant dataclasses.asdict()

        Returns:
            List[dict]: dictionnaire
        """
        return dataclasses.asdict(self)

    def to_json(self, output_file: str) -> None:
        """Sauvegarde l'objet graph en json

        Args:
            output_file (str): chemin du fichier json de sortie
        """
        with open(output_file, 'w') as f:
            json.dump(self.to_dict(), f, indent=True)

    @staticmethod
    def from_dict(graph_dict: dict) -> "Graph":
        """Instancier l'objet graph à partir d'un dictionnaire

        Args:
            graph_dict (dict): dictionnaire du graph

        Returns:
            Graph: objet graph instancié
        """
        return dacite.from_dict(Graph, graph_dict)

    @staticmethod
    def from_json(input_file: str) -> "Graph":
        """Instancier l'objet graph à partir d'un fichier json

        Args:
            input_file (str): chemin du fichier json d'entrée

        Returns:
            Graph: obket graph instancié
        """
        graph_dict = {}
        with open(input_file, 'r') as f:
            graph_dict = json.load(f)
        return Graph.from_dict(graph_dict)
