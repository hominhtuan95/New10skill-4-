import json
import re
import sys
from pathlib import Path
from cryptography.hazmat.primitives import serialization

if len(sys.argv) != 2 or not re.fullmatch(r'[0-9A-Fa-f]{32}', sys.argv[1]):
    print('Cach dung: python issue_license.py MA_HWID_32_KY_TU')
    sys.exit(1)
path = Path(__file__).resolve().parent / 'PRIVATE_LICENSE_KEY.pem'
key = serialization.load_pem_private_key(path.read_bytes(), password=None)
payload = json.dumps({'app': 'Autoskill-Hominhtuan95', 'hwid': sys.argv[1].upper()}, separators=(',', ':'), sort_keys=True).encode()
print('MA KICH HOAT:\n' + payload.hex() + '.' + key.sign(payload).hex())
