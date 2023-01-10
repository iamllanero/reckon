import tomllib
from reckon.constants import *

with open(TXNS_TOML, 'rb') as f:
    TXNS_CONFIG = tomllib.load(f)

with open(TAGS_FILE, 'rb') as f:
    TAGS = tomllib.load(f)

    with open(TAGS_LOCAL_FILE, 'rb') as g:
        local_tags = tomllib.load(g)

    TAGS.update(local_tags)