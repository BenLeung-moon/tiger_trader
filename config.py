import os

def load_file_content(filepath):
    try:
        with open(filepath, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Warning: {filepath} not found.")
        return None

def load_properties(filepath):
    props = {}
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    props[key.strip()] = value.strip()
    except FileNotFoundError:
        print(f"Warning: {filepath} not found.")
    return props

# API Keys
DEEPSEEK_API_KEY = load_file_content('credential/ds_api.txt')
# TIGER_TOKEN = load_file_content('tiger_openapi_token.txt')
_token_props = load_properties('credential/tiger_openapi_token.properties')
TIGER_TOKEN = _token_props.get('token')

# Tiger Trade Configuration
PROPS_FILE = 'credential/tiger_openapi_config.properties'
props = load_properties(PROPS_FILE)

TIGER_ID = props.get('tiger_id', os.getenv('TIGER_ID'))
TIGER_ACCOUNT = props.get('account', os.getenv('TIGER_ACCOUNT'))

# Private Key Handling
# Prefer pk1 (PKCS#1)
_pk_content = props.get('private_key_pk1')

if not _pk_content:
    # Try loading from PEM file
    _pk_content = load_file_content('credential/private_key.pem')

if _pk_content:
    # Ensure it has headers
    if not _pk_content.startswith('-----BEGIN'):
        # Wrap it
        PRIVATE_KEY_CONTENT = f"-----BEGIN RSA PRIVATE KEY-----\n{_pk_content}\n-----END RSA PRIVATE KEY-----"
    else:
        PRIVATE_KEY_CONTENT = _pk_content
else:
    PRIVATE_KEY_CONTENT = None

# DeepSeek Configuration
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
