"""Console script for clients."""
import argparse
import sys
import logging.config
import logging

from clients.tasks import (export_graph,
                           export_journals_with_distinct_mention,
                           print_drug_mention,
                           read_and_format_data)


logger = logging.getLogger(__name__)


def setup_logging():
    dict_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
        },
        'handlers': {
            'default': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'standard'
            }
        },
        'loggers': {
            'clients': {
                'handlers': ['default'],
                'level': 'DEBUG',
                'propagate': True
            }
        }
    }

    logging.config.dictConfig(dict_config)
    pass


def main():
    """Console script for clients."""
    setup_logging()
    parser = argparse.ArgumentParser()

    subparser = parser.add_subparsers(dest="task")

    parser_data = subparser.add_parser('data')
    parser_data.add_argument('--pubmed-files', type=str, required=True, nargs='+')
    parser_data.add_argument('--clinical-trials-file', type=str, required=True)
    parser_data.add_argument('--drug-file', type=str, required=True)
    parser_data.add_argument('-o', '--output-directory', type=str, required=True)
    parser_data.set_defaults(func=read_and_format_data)

    parser_build_graph = subparser.add_parser('build_graph')
    parser_build_graph.add_argument('-i', '--input-directory', type=str, required=True)
    parser_build_graph.add_argument('-g', '--json-graph-file', type=str, required=True)
    parser_build_graph.set_defaults(func=export_graph)

    parser_mentions = subparser.add_parser('mentions')
    parser_mentions.add_argument('-g', '--json-graph-file', type=str, required=True)
    parser_mentions.add_argument('-d', '--drug-names', type=str, required=True, nargs='+')
    parser_mentions.set_defaults(func=print_drug_mention)

    parser_query = subparser.add_parser('query')
    parser_query.add_argument('-g', '--json-graph-file', type=str, required=True)
    parser_query.set_defaults(func=export_journals_with_distinct_mention)

    args, _ = parser.parse_known_args()
    res = None
    if args.task:
        dict_args = vars(args).copy()
        dict_args.pop('func')
        dict_args.pop('task')
        try:
            res = args.func(**dict_args)
        except KeyboardInterrupt:
            logger.info("Le script a été interrompu.")
            return 1
        except Exception:
            logger.exception("Une erreur est survenue.")
            return 1
    else:
        parser.print_help()

    if res:
        print(res)

    return 0


if __name__ == "__main__":
    sys.exit(main())
