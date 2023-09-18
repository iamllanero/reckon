import tomllib
import os.path
from reckon.constants import *

with open(TXNS_TOML, 'rb') as f:
    TXNS_CONFIG = tomllib.load(f)

with open(TAGS_FILE, 'rb') as f:
    TAGS = tomllib.load(f)

    if os.path.exists(TAGS_LOCAL_FILE):
        with open(TAGS_LOCAL_FILE, 'rb') as g:
            local_tags = tomllib.load(g)

        TAGS.update(local_tags)

if not os.path.exists(TRANSACTION_OVERRIDES_FILE):
    open(TRANSACTION_OVERRIDES_FILE, "w").write("")

with open(TRANSACTION_OVERRIDES_FILE, 'rb') as f:
    TXN_OVERRIDES = tomllib.load(f)