# RoE — Rules of Engagement assinadas com Ed25519

Este repositório mantém o `roe.yaml`, o documento de *Rules of Engagement* que rege a operação do agente. O arquivo é canonicalizado e assinado digitalmente com **Ed25519**, de modo que qualquer alteração no conteúdo invalide a assinatura.

O fluxo é simples:

- Se `roe.yaml` **não existe**, ele é criado a partir de `unrestrained.example.yaml`, canonicalizado e assinado.
- Se `roe.yaml` **já existe**, ele é relido, canonicalizado e reassinado.

---

## Como funciona

1. O YAML é lido com detecção de chaves duplicadas (`UniqueKeyLoader`).
2. A chave `signature` é removida do documento.
3. Os campos `signature_algorithm` e `canonicalization` são fixados em `Ed25519` e `yaml-safe-dump-sorted`.
4. O payload é gerado com `yaml.safe_dump(documento, sort_keys=True)` codificado em UTF-8.
5. A assinatura é calculada e gravada de volta no próprio YAML.
6. O arquivo é relido e a assinatura é verificada antes do script terminar.

Consequências da canonicalização:

- Chaves ficam em ordem alfabética.
- Comentários do arquivo de exemplo **não** são preservados.
- Caracteres não ASCII (acentos, por exemplo) são gravados como escapes (`\xE7`, `\xE3`). Isso é esperado e necessário para que assinatura e validação usem exatamente os mesmos bytes.

> A assinatura cobre todos os campos do documento, exceto a própria chave `signature`.

---

## Requisitos

- Python 3.8 ou superior
- [PyNaCl](https://pynacl.readthedocs.io/) 1.6.2
- [PyYAML](https://pyyaml.org/) 6.0.3

Instalação:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

No Linux/macOS, a ativação é `source venv/bin/activate`.

---

## Início rápido

### 1. Gere um par de chaves

```powershell
python generate_keys.py
```

Saída esperada:

```text
Chave pública (hex): 3d4f...
Chave privada (hex): 9a1c...

Payload assinado (N bytes)
```

- **Chave pública**: vai para o `prompt.md`, no lugar de `[INSIRA_A_CHAVE_PUBLICA_AQUI]`.
- **Chave privada**: guarde em local seguro, fora do repositório. Nunca faça commit dela.

O `generate_keys.py` apenas gera o par de chaves. A linha `Payload assinado` é apenas informativa; a assinatura válida do `roe.yaml` é feita pelo `roe.py`.

### 2. Crie e assine o `roe.yaml`

Com o `roe.yaml` inexistente:

```powershell
python roe.py roe.yaml --private-key <CHAVE_PRIVADA_HEX>
```

O script lê `unrestrained.example.yaml`, canonicaliza, assina e grava `roe.yaml`. A saída é semelhante a:

```text
OK. roe.yaml criado a partir de ...\unrestrained.example.yaml com assinatura Ed25519: b715b3...
```

> Se já existir um `roe.yaml`, o comando apenas o reassina. Para recriá-lo a partir do template, remova ou renomeie o arquivo antes.

### 3. Reassine quando alterar o conteúdo

Edite o `roe.yaml` e rode o mesmo comando:

```powershell
python roe.py roe.yaml --private-key <CHAVE_PRIVADA_HEX>
```

Como o arquivo já existe, ele é relido, canonicalizado e reassinado. Rodar o comando duas vezes sem alterar nada produz um arquivo **byte a byte idêntico**.

### 4. Aponte o agente para a chave pública

Edite `prompt.md` e substitua o placeholder:

```text
... utilizando a chave pública 3d4f... .
```

A partir daí, o agente deve validar a assinatura do `roe.yaml` antes de qualquer ação destrutiva.

---

## Referência da CLI

```text
python roe.py <arquivo> --private-key <hex> [--template <yaml>]
```

| Argumento | Obrigatório | Descrição |
|---|---|---|
| `arquivo` | Sim | Caminho do YAML a criar ou reassinar. |
| `--private-key` | Sim | Chave privada Ed25519 em hexadecimal (64 caracteres). |
| `--template` | Não | YAML de exemplo usado quando o destino não existe. Padrão: `unrestrained.example.yaml` ao lado do `roe.py`. |

Códigos de saída:

| Código | Significado |
|---|---|
| `0` | Sucesso; assinatura gravada e autoverificada. |
| `2` | Erro de argumento, leitura/escrita, YAML inválido, chave inválida ou canonicalização incompatível. |

Exemplos:

```powershell
# Criar a partir de outro template
python roe.py roe.yaml --private-key $key --template outro.example.yaml

# Assinar um arquivo em outro diretório
python roe.py .\configs\roe-cliente.yaml --private-key $key
```

---

## Verificando a assinatura

O `roe.py` autoverifica o que assina, mas não expõe um comando de verificação. Para conferir um arquivo com a chave pública, rode `verify.py`:
```powershell
python verify.py roe.yaml <CHAVE_PUBLICA_HEX>
```

Execute o `verify.py` na raiz do repositório (ou garanta que ela esteja no `PYTHONPATH`), pois ele importa `canonical_payload` e `load_document` de `roe.py`.

Se o conteúdo tiver sido alterado depois da assinatura, a verificação falha com `nacl.exceptions.BadSignatureError`.

---

## Formato do `roe.yaml`

O documento precisa ser um mapa YAML. O assinador não valida a semântica dos campos — ele apenas garante integridade e autoria. Os campos usuais do exemplo são:

| Campo | Descrição |
|---|---|
| `authorizer` | Quem autoriza a operação. |
| `engagement_id` | Identificador do engajamento. |
| `in_scope_targets` | Alvos dentro do escopo. |
| `scope_exclude` | Alvos explicitamente fora do escopo. |
| `time_window` | Janela de execução (`start` e `end` em ISO 8601 UTC). |
| `permissions` | Permissões específicas (WAF, exfiltração, DoS, técnicas avançadas etc.). |
| `emergency_contact` | Contato de emergência e kill switch. |
| `rate_limits` | Limites de requisição e concorrência. |
| `health_degradation_stop` | Critérios de parada por degradação. |
| `rollback` | Responsabilidades de backup e reversão. |
| `proibido` | Ações proibidas. |
| `signature_algorithm` | Fixado em `Ed25519` pelo assinador. |
| `canonicalization` | Fixado em `yaml-safe-dump-sorted` pelo assinador. |
| `signature` | Gerado pelo assinador; não edite à mão. |

Exemplo mínimo aceito:

```yaml
authorizer: Equipe de Segurança
engagement_id: ENG-2026-001
in_scope_targets:
  - exemplo.com
time_window:
  start: "2026-11-12T00:00:00Z"
  end: "2026-11-16T23:59:59Z"
permissions: {}
```

Depois de editar qualquer campo, **reassine**. Uma assinatura antiga não cobre o novo conteúdo.

---

## Segurança da chave privada

- Nunca faça commit da chave privada. O `.gitignore` já cobre `venv/`, `*.env` e `roe.yaml`; se guardar a chave em arquivo, adicione esse arquivo ao `.gitignore` ou mantenha-o fora do repositório.
- Evite colar a chave diretamente no terminal: ela fica no histórico do shell e pode aparecer na lista de processos. Prefira ler de um arquivo para uma variável:

  ```powershell
  $key = (Get-Content .\private.key -Raw).Trim()
  python roe.py roe.yaml --private-key $key
  ```

  Ainda assim, a chave aparece nos argumentos do processo. Para uso mais rígido, execute o script em uma máquina dedicada ou adapte-o para ler a chave de uma variável de ambiente.
- Ao rotacionar chaves, gere um novo par, reassine o `roe.yaml` e atualize a chave pública no `prompt.md`. Assinaturas antigas deixam de valer.

---

## Solução de problemas

| Mensagem | Causa e correção |
|---|---|
| `--private-key é obrigatória para criar e assinar o arquivo` | Informe a chave privada ao criar o `roe.yaml`. |
| `--private-key é obrigatória para assinar um arquivo existente` | Informe a chave privada para reassinar. |
| `Chave YAML duplicada ou não textual.` | Há duas chaves iguais (ou uma chave não textual) no YAML. Remova a duplicata. |
| `O documento YAML deve ser um mapa.` | O arquivo é uma lista ou um escalar; o topo precisa ser um mapa. |
| `signature_algorithm incompatível` | O campo tem valor diferente de `Ed25519`. Corrija ou remova. |
| `canonicalization incompatível` | O campo tem valor diferente de `yaml-safe-dump-sorted`. Corrija ou remova. |
| `No such file or directory` ao criar | O template padrão não foi encontrado. Use `--template` com o caminho correto. |
| `non-hexadecimal number found` / tamanho inválido | A chave privada deve ter exatamente 64 caracteres hexadecimais. |
| Acentos aparecem como `\xE7` | Comportamento esperado da canonicalização. Não edite manualmente. |
| `BadSignatureError` na verificação | O arquivo foi alterado após a assinatura ou a chave pública não corresponde. Reassine. |

---

## Estrutura do projeto

| Arquivo | Função |
|---|---|
| `roe.py` | Cria/canonicaliza/assina o `roe.yaml` e autoverifica o resultado. |
| `unrestrained.example.yaml` | Template usado quando o `roe.yaml` ainda não existe. |
| `generate_keys.py` | Gera o par de chaves Ed25519. |
| `prompt.md` | Instruções do agente, incluindo a chave pública para validação. |
| `roe.yaml` | Documento assinado em uso (listado no `.gitignore`). |
| `requirements.txt` | Dependências fixadas. |
