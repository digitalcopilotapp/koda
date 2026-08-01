#!/usr/bin/env python3
"""
Cria a estrutura curricular da Funeral Academy numa instância rodando.

Lê `curriculo.json` (ao lado deste arquivo) e cria, via API, um curso por
entrada e um capítulo por módulo. É idempotente: cursos já existentes com o
mesmo código são pulados, então rodar duas vezes não duplica nada.

O que este script NÃO faz: criar o conteúdo das lições. Ele monta o esqueleto
navegável — cursos, capítulos, objetivos de aprendizagem. O conteúdo de cada
lição precisa de produção e de validação por responsável técnico e assessoria
jurídica antes de ir ao ar. Ver docs/funeral-academy/curriculo.md.

Uso:
    python seed_curriculo.py
    python seed_curriculo.py --dry-run
    API_URL=http://localhost:1338/api/v1 ADMIN_EMAIL=... ADMIN_PASSWORD=... python seed_curriculo.py

Só depende da biblioteca padrão.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

API_URL = os.environ.get("API_URL", "http://localhost:1338/api/v1").rstrip("/")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@funeralacademy.com.br")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")
ORG_SLUG = os.environ.get("ORG_SLUG", "funeral-academy")

CURRICULO = Path(__file__).parent / "curriculo.json"


def request(method, path, token=None, data=None, form=None, timeout=60):
    url = f"{API_URL}{path}"
    headers = {}
    body = None

    if token:
        headers["Authorization"] = f"Bearer {token}"

    if form is not None:
        # multipart/form-data — a criação de curso não aceita JSON
        boundary = f"----FA{uuid.uuid4().hex}"
        parts = []
        for key, value in form.items():
            parts.append(f"--{boundary}\r\n")
            parts.append(f'Content-Disposition: form-data; name="{key}"\r\n\r\n')
            parts.append(f"{value}\r\n")
        parts.append(f"--{boundary}--\r\n")
        body = "".join(parts).encode()
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    elif data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        detail = e.read().decode()[:400]
        raise RuntimeError(f"{method} {path} -> HTTP {e.code}: {detail}") from None


def login():
    if not ADMIN_PASSWORD:
        sys.exit("Defina ADMIN_PASSWORD (a senha do administrador da instância).")

    payload = urllib.parse.urlencode(
        {"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    ).encode()
    req = urllib.request.Request(
        f"{API_URL}/auth/login",
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())["tokens"]["access_token"]
    except urllib.error.HTTPError as e:
        sys.exit(f"Login falhou (HTTP {e.code}). Confira ADMIN_EMAIL e ADMIN_PASSWORD.")


def existing_course_codes(token):
    """
    Códigos (FA-xxx) dos cursos que já existem, lidos do início do nome.

    Sem tratamento de erro de propósito: se a listagem falhar, o script precisa
    abortar. Engolir a falha aqui faz o seed rodar como se a instância estivesse
    vazia e duplicar o currículo inteiro.
    """
    courses = request(
        "GET", f"/courses/org_slug/{ORG_SLUG}/page/1/limit/500", token=token
    )
    items = courses if isinstance(courses, list) else (courses or {}).get("courses", [])
    codes = set()
    for c in items:
        name = (c or {}).get("name", "")
        if name.startswith("FA-"):
            codes.add(name.split(" ", 1)[0].strip())
    return codes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="mostra o que seria criado, sem tocar na instância",
    )
    args = parser.parse_args()

    curriculo = json.loads(CURRICULO.read_text(encoding="utf-8"))
    trilhas = curriculo["trilhas"]

    total_cursos = sum(len(t["cursos"]) for t in trilhas)
    total_modulos = sum(len(c["modulos"]) for t in trilhas for c in t["cursos"])

    if args.dry_run:
        for trilha in trilhas:
            print(f"\n{trilha['nome']}")
            for curso in trilha["cursos"]:
                print(f"  {curso['codigo']} — {curso['nome']} ({len(curso['modulos'])} módulos)")
        print(f"\n{len(trilhas)} trilhas · {total_cursos} cursos · {total_modulos} módulos")
        return

    token = login()
    org = request("GET", f"/orgs/slug/{ORG_SLUG}", token=token)
    org_id = org["id"]
    print(f"Organização: {org['name']} (id {org_id})")

    ja_existem = existing_course_codes(token)
    if ja_existem:
        print(f"Cursos já presentes: {len(ja_existem)} — serão pulados")

    criados = pulados = 0

    for trilha in trilhas:
        print(f"\n=== {trilha['nome']} ===")

        for curso in trilha["cursos"]:
            codigo = curso["codigo"]
            if codigo in ja_existem:
                print(f"  · {codigo} já existe, pulando")
                pulados += 1
                continue

            nome = f"{codigo} — {curso['nome']}"
            novo = request(
                "POST",
                f"/courses/?org_id={org_id}",
                token=token,
                form={
                    "name": nome,
                    "description": curso["descricao"],
                    "about": f"Trilha: {trilha['nome']}. {trilha['descricao']}",
                    "learnings": json.dumps(curso["aprendizados"], ensure_ascii=False),
                    "tags": f"{trilha['codigo']},{codigo.lower()}",
                    "public": "false",
                    "thumbnail_type": "image",
                },
            )
            course_id = novo["id"]
            print(f"  ✓ {nome}")

            for modulo in curso["modulos"]:
                request(
                    "POST",
                    "/chapters/",
                    token=token,
                    data={
                        "name": modulo,
                        "description": "",
                        "org_id": org_id,
                        "course_id": course_id,
                    },
                )
            print(f"      {len(curso['modulos'])} módulos")
            criados += 1

    print(f"\nCriados: {criados} cursos · Pulados: {pulados}")
    if criados:
        print("Os cursos entram como NÃO públicos. Publique pelo painel quando o conteúdo estiver validado.")


if __name__ == "__main__":
    main()
