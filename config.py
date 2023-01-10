import tomllib
from reckon.constants import *

with open(TXNS_TOML, 'rb') as f:
    TXNS_CONFIG = tomllib.load(f)