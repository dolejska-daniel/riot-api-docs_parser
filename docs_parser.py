import os
import logging.config
from argparse import ArgumentParser

import yaml

import docs_parser


log = logging.getLogger()

if __name__ == '__main__':
    parser = ArgumentParser()

    parser.add_argument("-d", "--download",
                        help="program will first download the latest version of the API docs",
                        action="store_true")

    args = parser.parse_args()

    logging_config_filepath = "config/logging.yaml"
    if not os.path.isfile(logging_config_filepath):
        logging_config_filepath = "config/logging.dist.yaml"

    with open(logging_config_filepath, "r") as fd:
        logging_config = yaml.safe_load(fd)
        logging.config.dictConfig(logging_config)

    docs_parser.run(run_download=args.download)
