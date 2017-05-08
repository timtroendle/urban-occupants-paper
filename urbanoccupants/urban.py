import os
import sys
from pathlib import Path

import click
import pytus2000

module_path = os.path.abspath(os.path.join('./'))
if module_path not in sys.path:
    sys.path.append(module_path)

from urbanoccupants.tus.individuals import read_seed

CACHE_FOLDER_PATH = Path('../build/cache')


@click.group()
def cli():
    pass


if __name__ == '__main__':
    cli.add_command(read_seed)
    pytus2000.set_cache_location(CACHE_FOLDER_PATH)
    cli()
