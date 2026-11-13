import os
from nacl.encoding import HexEncoder
from nacl.signing import SigningKey


def canonical_roe_bytes(filename: str = "unrestrained.example.yaml") -> bytes:
    """Lê o arquivo YAML de exemplo de RoE, remove a linha 'signature:' e normaliza quebras de linha."""
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

    payload = canonical_roe_bytes("unrestrained.example.yaml")
    signed  = signing_key.sign(payload)
    signature_hex = signed.signature.hex()

    print(f"Chave pública (hex): {public_key}")
    print(f"Chave privada (hex): {private_key}")
    print(f"\nPayload assinado ({len(payload)} bytes)\n")
    #print(f"Signature para o unrestrained.example.yaml: {signature_hex}")  DESNECESSARIO


if __name__ == "__main__":
    main()