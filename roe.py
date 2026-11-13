#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

import yaml
from nacl.encoding import HexEncoder
from nacl.signing import SigningKey
from yaml.constructor import ConstructorError


REQUIRED_ALGORITHM = "Ed25519"
REQUIRED_CANONICALIZATION = "yaml-safe-dump-sorted"
DEFAULT_TEMPLATE = Path(__file__).resolve().with_name("unrestrained.example.yaml")


class UniqueKeyLoader(yaml.SafeLoader):
    """Idêntico ao do validador — detecta chaves duplicadas antes de assinar."""
    def construct_mapping(self, node, deep=False):
        mapping = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str) or key in mapping:
                raise ConstructorError(
                    None, None, "Chave YAML duplicada ou não textual.", key_node.start_mark
                )
            mapping[key] = self.construct_object(value_node, deep=deep)
        return mapping


def canonical_payload(document: dict) -> bytes:
    # Exatamente a mesma chamada do validador. Não mexa nos argumentos.
    return yaml.safe_dump(document, sort_keys=True).encode("utf-8")


def load_document(path: Path) -> dict:
    document = yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
    if not isinstance(document, dict):
        raise ValueError("O documento YAML deve ser um mapa.")
    return document


def prepare_document(document: dict) -> dict:
    document.pop("signature", None)

    alg = document.get("signature_algorithm")
    if alg not in (None, REQUIRED_ALGORITHM):
        raise ValueError(f"signature_algorithm incompatível: {alg!r}")
    canon = document.get("canonicalization")
    if canon not in (None, REQUIRED_CANONICALIZATION):
        raise ValueError(f"canonicalization incompatível: {canon!r}")

    document["signature_algorithm"] = REQUIRED_ALGORITHM
    document["canonicalization"] = REQUIRED_CANONICALIZATION
    return document


def sign_file(path: Path, private_key_hex: str) -> str:
    return write_signed_document(path, load_document(path), private_key_hex)


def write_signed_document(path: Path, document: dict, private_key_hex: str) -> str:
    document = prepare_document(document)
    payload = canonical_payload(document)

    signing_key = SigningKey(bytes.fromhex(private_key_hex))
    signature_hex = signing_key.sign(payload).signature.hex()

    # Grava o documento canonicalizado com a assinatura dentro do próprio YAML
    document["signature"] = signature_hex
    path.write_text(yaml.safe_dump(document, sort_keys=True), encoding="utf-8")

    # Autoverificação: relê o arquivo, remove assinatura, recomputa e verifica
    reloaded = load_document(path)
    reloaded_sig = bytes.fromhex(reloaded.pop("signature"))
    signing_key.verify_key.verify(canonical_payload(reloaded), reloaded_sig)

    return signature_hex


def main():
    parser = argparse.ArgumentParser(
        description="Assina um YAML com Ed25519 no formato esperado pelo validador."
    )
    parser.add_argument("file", type=Path, help="Caminho do arquivo YAML")
    parser.add_argument("--private-key",
                        help="Chave privada Ed25519 em hexadecimal (64 hex chars)")
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE,
                        help="YAML de exemplo usado quando o arquivo ainda não existe "
                             f"(padrão: {DEFAULT_TEMPLATE.name})")
    args = parser.parse_args()

    try:
        if not args.file.exists():
            if args.private_key is None:
                parser.error("--private-key é obrigatória para criar e assinar o arquivo")
            document = load_document(args.template)
            signature_hex = write_signed_document(args.file, document, args.private_key)
            print(f"OK. {args.file} criado a partir de {args.template} "
                  f"com assinatura Ed25519: {signature_hex}")
            return 0

        if args.private_key is None:
            parser.error("--private-key é obrigatória para assinar um arquivo existente")
        signature_hex = sign_file(args.file, args.private_key)
    except (OSError, ValueError, yaml.YAMLError) as error:
        print(f"Erro na assinatura: {error}", file=sys.stderr)
        return 2

    print(f"OK. Assinatura gravada em {args.file}: {signature_hex}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
