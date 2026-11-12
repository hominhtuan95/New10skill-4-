from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

base = Path(__file__).resolve().parent
private_path = base / 'PRIVATE_LICENSE_KEY.pem'
source = base / 'Autoskill_Hominhtuan95.py'
if private_path.exists():
    key = serialization.load_pem_private_key(private_path.read_bytes(), password=None)
    print('Su dung khoa rieng da co. Khong tao khoa moi.')
else:
    key = Ed25519PrivateKey.generate()
    private_path.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    print('Da tao khoa rieng moi.')
public_hex = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex()
text = source.read_text(encoding='utf-8')
import re
new_text, count = re.subn(r"^PUBLIC_KEY_HEX = '[^']*'$", f"PUBLIC_KEY_HEX = '{public_hex}'", text, count=1, flags=re.M)
if count != 1:
    raise RuntimeError('Khong tim thay PUBLIC_KEY_HEX trong ma nguon.')
source.write_text(new_text, encoding='utf-8')
print('Da cap nhat khoa cong khai trong Autoskill_Hominhtuan95.py')
print('KHONG TAI PRIVATE_LICENSE_KEY.pem LEN GITHUB!')
