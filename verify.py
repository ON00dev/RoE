import sys
from pathlib import Path

from nacl.signing import VerifyKey

from roe import canonical_payload, load_document

path = Path(sys.argv[1])
public_key_hex = sys.argv[2]

document = load_document(path)
signature = bytes.fromhex(document.pop("signature"))

VerifyKey(bytes.fromhex(public_key_hex)).verify(
    canonical_payload(document), signature
)
print("Assinatura valida.")