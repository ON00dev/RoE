import os
from nacl.encoding import HexEncoder
from nacl.signing import SigningKey


def canonical_roe_bytes(filename: str = "roe.yaml") -> bytes:
    """Lê o roe.yaml, remove a linha 'signature:' e normaliza quebras de linha."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    with open(path, "rb") as f:
        lines = f.read().splitlines()
    return b"\n".join(
        ln for ln in lines if not ln.strip().startswith(b"signature:")
    )


def main():
    signing_key = SigningKey.generate()
    public_key  = signing_key.verify_key.encode(encoder=HexEncoder).decode("ascii")
    private_key = signing_key.encode(encoder=HexEncoder).decode("ascii")

    payload = canonical_roe_bytes("roe.yaml")
    signed  = signing_key.sign(payload)
    signature_hex = signed.signature.hex()

    print(f"Chave pública (hex): {public_key}")
    print(f"Chave privada (hex): {private_key}")
    print(f"\nPayload assinado ({len(payload)} bytes)\n")
    #print(f"Signature para o roe.yaml: {signature_hex}")


if __name__ == "__main__":
    main()