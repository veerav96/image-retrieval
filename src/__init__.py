import os
from pathlib import Path

import hydra
from semver import Version

__version__: Version = Version.parse('0.1.0-dev')

config_dir = os.getenv('PAPYRUS_APP_CONFIG_DIR', str(Path('config').absolute()))

hydra.initialize_config_dir(config_dir=config_dir, version_base=None)
