from argparse import ArgumentParser


def parse_args():
    parser = ArgumentParser()
    parser.add_argument(
        '-c', '--config',
        required=True,
        help='Path to the config YAML file'
    )

    return parser.parse_args()
