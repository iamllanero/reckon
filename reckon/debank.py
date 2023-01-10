import json
import requests
import tomllib
from reckon.constants import TAGS_FILE, WALLETS_CACHE_DIR
from reckon.secrets import DEBANK_ACCESSKEY
from utils import list_to_csv

TAGS = tomllib.load(open(TAGS_FILE, 'rb'))

FLAT_HEADERS = [
            'number',
            'sub',
            'cate_id',
            'id',
            'other_addr',
            'other_addr.tag',
            'project_id',
            'project.name',
            'project.chain',
            'project.site_url',
            'time_at',
            'receives.amount',
            'receives.from_addr',
            'receives.from_addr.tag',
            'receives.token_id',
            'receives.token.symbol',
            'receives.token.is_verified',
            'sends.amount',
            'sends.to_addr',
            'sends.to_addr.tag',
            'sends.token_id',
            'sends.token.symbol',
            'sends.token.is_verified',
            'token_approve.spender',
            'token_approve.token_id',
            'token_approve.token.symbol',
            'token_approve.token.is_verified',
            'token_approve.value',
            'tx.name',
            'tx.status',
            'tx.from_addr',
            'tx.from_addr.tag',
            'tx.to_addr',
            'tx.to_addr.tag',
            'tx.eth_gas_fee',
            'tx.usd_gas_fee',
            'tx.value',
            'tx.params',
            'url',
            'spam'
        ]


class HistoryList:
    """Wrapper around the Debank User HistoryList object"""

    def __init__(self, wallet_addr, chain_id, data=None):
        """Initialize with an optional dict in HistoryList format"""
        if data is not None:
            self.data = data
        else:
            self.data = {}
            self.data['cate_dict'] = {}
            self.data['project_dict'] = {}
            self.data['token_dict'] = {}
            self.data['history_list'] = []
        self.data['wallet_addr'] = wallet_addr
        self.data['chain_id'] = chain_id

    def max_time_at(self):
        """Max time of the history list"""
        max_entry = max(self.data['history_list'], key=lambda x: x['time_at'])
        return max_entry['time_at']

    def min_time_at(self):
        """Min time of the history list"""
        min_entry = min(self.data['history_list'], key=lambda x: x['time_at'])
        return min_entry['time_at']

    def len(self):
        """Size of the history list"""
        return len(self.data['history_list'])

    def times(self):
        """List of the times in the history list"""
        times = []
        for i in self.data['history_list']:
            times.append(i['time_at'])
        return times

    def history_list(self):
        """The raw history list"""
        return self.data['history_list']

    def raw(self):
        """The raw dict"""
        return self.data

    def add(self, hl):
        """Adds a HistoryList items to the current one"""
        hlraw = hl.raw()
        self.data['cate_dict'].update(hlraw['cate_dict'])
        self.data['project_dict'].update(hlraw['project_dict'])
        self.data['token_dict'].update(hlraw['token_dict'])

        count = 0
        current_ids = [x['id'] for x in self.data['history_list']]
        for h in hlraw['history_list']:
            if not h['id'] in current_ids:
                self.data['history_list'].append(h)
                count += 1

        self.data['history_list'].sort(key=lambda x: x['time_at'])

        return count

    def write(self):
        """Writes the HistoryList as a JSON to file"""
        with open(f'{WALLETS_CACHE_DIR}/{self.get_wallet_addr()}-{self.get_chain_id()}.json', "w") as f:
            json.dump(self.data, f)
    
    def write_flat_csv(self):
        """Writes the HistoryList as a flattend CSV file"""
        flat_hl = [FLAT_HEADERS]
        for i in range(self.get_size()):
            flat_hl.extend(self.get_history_entry_flat(i))
            list_to_csv(flat_hl, f'{WALLETS_CACHE_DIR}/{self.get_wallet_addr()}-{self.get_chain_id()}.csv')

    def get_wallet_addr(self):
        return self.data['wallet_addr']

    def get_chain_id(self):
        return self.data['chain_id']

    def get_token(self, id):
        """Returns a dict of the token"""
        if id in self.data['token_dict']:
            token = self.data['token_dict'][id]
            if 'is_verified' not in token or token['is_verified'] is None:
                token['is_verified'] = False
        else:
            token = {'name': '',
                     'symbol': '',
                     'is_verified': False}
        return token
    
    def get_project(self, id):
        """Returns a dict of the project"""
        if id in self.data['project_dict']:
            project = self.data['project_dict'][id]
            return project
        else:
            return {
                'name': '',
                'chain': self.get_chain_id(),
                'site_url': ''
            }

    def get_size(self):
        return len(self.data['history_list'])

    def get_history_entry_json(self, index):
        return self.data['history_list'][index]

    def get_history_entry_flat(self, index):
        """
        Returns a list of list where the inner list contains the FLAT_HEADERS
        """
        entries = []
        entry = self.data['history_list'][index]
        num_rows = max(len(entry['receives']),
                       len(entry['sends']),
                       1)
        for i in range(num_rows):
            row = [
                index,
                i]

            if entry['cate_id'] is not None:
                row.append(entry['cate_id'])
            else:
                row.append('')
            
            row.extend([
                entry['id'],
                entry['other_addr'],
                get_tag(entry['other_addr'])])
            
            project_id = None
            if entry['project_id'] is not None:
                project_id = entry['project_id']
                row.append(project_id)
            else:
                row.append('')
            
            project = self.get_project(entry['project_id'])
            row.extend([
                project['name'],
                project['chain'],
                project['site_url'],
                entry['time_at']
            ])

            receive_token_id = None
            receive_token_is_verified = None
            if len(entry['receives']) > i:
                row.extend([
                    entry['receives'][i]['amount'],
                    entry['receives'][i]['from_addr'],
                    get_tag(entry['receives'][i]['from_addr']),
                    entry['receives'][i]['token_id']])
                token = self.get_token(entry['receives'][i]['token_id'])
                row.extend([
                    token['symbol'],
                    token['is_verified']
                ])
                receive_token_id = entry['receives'][i]['token_id']
                receive_token_is_verified = token['is_verified']
            else:
                row.extend(['' for x in range(6)])

            sends_token_id = None
            if len(entry['sends']) > i:
                sends_token_id = entry['sends'][i]['token_id']
                row.extend([
                    entry['sends'][i]['amount'],
                    entry['sends'][i]['to_addr'],
                    get_tag(entry['sends'][i]['to_addr']),
                    sends_token_id])
                token = self.get_token(sends_token_id)
                row.extend([
                    token['symbol'],
                    token['is_verified']
                ])
            else:
                row.extend(['' for x in range(6)])

            if entry['token_approve'] is not None:
                row.extend([
                    entry['token_approve']['spender'],
                    entry['token_approve']['token_id']])
                token = self.get_token(entry['token_approve']['token_id'])
                row.extend([
                    token['symbol'],
                    token['is_verified'],
                    entry['token_approve']['value'],
                ])
            else:
                row.extend(['' for x in range(5)])

            tx_name = None
            if entry['tx'] is not None:
                tx_name = entry['tx']['name']
                row.extend([
                    tx_name,
                    entry['tx']['status'],
                    entry['tx']['from_addr'],
                    get_tag(entry['tx']['from_addr']),
                    entry['tx']['to_addr'],
                    get_tag(entry['tx']['to_addr']),
                    entry['tx']['eth_gas_fee'],
                    entry['tx']['usd_gas_fee'],
                    entry['tx']['value'],
                    ':'.join(entry['tx']['params'])
                ])
            else:
                row.extend(['' for x in range(10)])
            row.append(get_id_url(entry['id'], self.get_chain_id()))
            row.append(is_spam(receive_token_id,
                               receive_token_is_verified,
                               project_id,
                               sends_token_id,
                               tx_name))

            entries.append(row)

        return entries
    
def is_spam(receives_token_id,
            receives_token_is_verfied,
            project_id,
            sends_token_id,
            tx_name
            ):
    """
    Spam Detection Algo
        - receives.token_id is not None
        - receives.token.is_verified is not True
        - project == '' or 'None'
        - sends.token_id is None
        - tx.name = is None
    """
    has_receives = False if receives_token_id is None else True
    is_verified = receives_token_is_verfied
    has_project = False if project_id is None else True
    has_sends = False if sends_token_id is None else True
    has_tx = False if tx_name is None else True

    if has_receives and \
        not is_verified and \
        not has_project and \
        not has_sends and \
        not has_tx:
        return True

    return False



def load_history(wallet_addr, chain_id) -> HistoryList:
    """Creates a HistoryList based on an existing file."""

    with open(f'{WALLETS_CACHE_DIR}/{wallet_addr}-{chain_id}.json', 'rb') as f:
        data = json.load(f)
    hlr = HistoryList(wallet_addr, chain_id, data)
    return hlr


def fetch(url):
    """Helper function for API HTTP request."""

    headers = {'Accept': 'application/json',
               'AccessKey': DEBANK_ACCESSKEY}
    response = requests.get(url=url, headers=headers)
    return response


def create_history_list_url(id, chain_id, start_time=None):
    """Helper function to create a URL string for /v1/user/history_list.

    See https://docs.open.debank.com/en/reference/api-pro-reference/user#get-user-history-list
    for more details.
    """

    url = 'https://pro-openapi.debank.com/v1/user/history_list?' \
        f'id={id}&' \
        f'chain_id={chain_id}'
    if start_time is not None:
        url += f'&start_time={int(start_time)}'
    return url


def fetch_history(id, chain_id, start_time=None):
    """Fetches 20 entries from DeBank API.

    Defaults to the 20 most recent entries, but if a start_time is provided,
    will requests the 20 entries earlier than the time.
    """

    response = fetch(create_history_list_url(id, chain_id, start_time))
    hl = HistoryList(id, chain_id, json.loads(response.text))
    return hl


def fetch_all_history(id, chain_id):
    """Fetches the full history from DeBank API for the wallet id. 

    This function will keep calling the DeBank API until there are no more 
    entries left for the wallet id. If fn (a filename) is provided, the 
    function will first load the wallet, and then refresh the wallet with any
    new entries since the minimum time_at entry.
    """

    try:
        all_hl = load_history(id, chain_id)
    except FileNotFoundError:
        all_hl = HistoryList(id, chain_id)

    has_more = True
    start_time = None
    count = 0

    while has_more:
        print(f'Fetch loop {count}')
        hl = fetch_history(id, chain_id, start_time)
        added = all_hl.add(hl)
        print(
            f'All history: {all_hl.len()}. Fetched {hl.len()} history records. Added {added} records.')
        if hl.len() < 20 or added == 0:
            has_more = False
        else:
            start_time = hl.min_time_at()
        count += 1

    return all_hl

def get_tag(id):
    # TODO Need to adjust to be sensitive to chain
    # TODO Need to adjust tags.toml file too
    if id in TAGS:
        return TAGS[id]
    else:
        return ''

def get_id_url(txn_id, chain_id):
    url_map = {
        'eth': 'https://etherscan.io/tx',
        'ftm': 'https://ftmscan.com/tx',
        'avax': 'https://snowtrace.io/tx',
        'arb': 'https://arbiscan.io/tx',
        'matic': 'https://polygonscan.com/tx'
    }
    if chain_id in url_map:
        return f'{url_map[chain_id]}/{txn_id}'
    else:
        return ''

