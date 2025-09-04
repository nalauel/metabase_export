#!/usr/bin/env python3
"""
Export CSV from a Metabase saved question (card) and save to a local folder.

Usage examples:
  - Single card:  python export_metabase_csv.py --card-id 123
  - Multiple:     python export_metabase_csv.py --card-id 123 --card-id 456
  - With params:  python export_metabase_csv.py --card-id 123 --param status=active --param start_date=2025-08-01

Auth options (choose one):
  1) Personal Access Token (PAT): set METABASE_API_KEY in env and --use-api-key
  2) Username/Password session: set METABASE_USERNAME and METABASE_PASSWORD in env

Required env vars:
  METABASE_HOST  -> e.g. https://metabase.suaempresa.com
  OUTPUT_DIR     -> absolute path to a local folder, e.g. C:\metabase-export\out or /Users/alan/Exports/metabase
  (Optional) FILE_PREFIX -> prefix for filenames

Notes:
  - If your card has parameters, pass them using --param name=value (repeatable).
  - Filenames include a timestamp by default. Use --no-timestamp to disable.
  - To overwrite to a fixed filename, pass --filename meu_relatorio.csv
"""
import argparse
import os
import sys
import time
from datetime import datetime
from urllib.parse import urlencode
import requests
from dotenv import load_dotenv
from pathlib import Path
import shutil
import csv, io, re


_num_re = re.compile(r"""
    ^\s*
    (?P<sign>[-+])?
    (?P<int>\d{1,3}(?:,\d{3})*|\d+)
    (?P<dec>\.\d+)?                # .56
    (?P<pct>\%)?                   # opcional '%'
    \s*$
""", re.X)

def _en_to_pt_number(txt: str) -> str:
    """
    Converte '1,234.56' -> '1.234,56'
    Preserva sinal e '%' no fim.
    """
    m = _num_re.match(txt)
    if not m:
        return txt
    sign = m.group('sign') or ''
    pct  = m.group('pct') or ''
    # remove vírgulas de milhar en-US
    base = (m.group('int') or '') + (m.group('dec') or '')
    base = base.replace(',', '')
    try:
        val = float(base)
    except ValueError:
        return txt
    # 2 casas decimais por padrão para CSV "financeiro"
    s = f"{val:,.2f}"               # 1,234.56
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")  # 1.234,56
    return f"{sign}{s}{pct}"

def rewrite_csv_bytes(csv_bytes: bytes, quote_all: bool, decimal_comma: bool, delimiter: str, add_bom: bool) -> bytes:
    """
    Regrava CSV: aspas (QUOTE_ALL), vírgula decimal, delimitador e BOM.
    """
    text = csv_bytes.decode("utf-8", errors="replace")
    rows = list(csv.reader(io.StringIO(text)))  # lê no formato original

    if decimal_comma:
        for r_i, row in enumerate(rows):
            new_row = []
            for cell in row:
                c = cell.strip()
                # tenta converter números puros e percentuais
                new_cell = _en_to_pt_number(c)
                new_row.append(new_cell)
            rows[r_i] = new_row

    out_io = io.StringIO()
    quoting = csv.QUOTE_ALL if quote_all else csv.QUOTE_MINIMAL
    writer = csv.writer(out_io, delimiter=delimiter, quoting=quoting, lineterminator="\n")
    for r in rows:
        writer.writerow(r)

    data = out_io.getvalue().encode("utf-8")
    if add_bom:
        data = b"\xef\xbb\xbf" + data
    return data

load_dotenv()  # load .env if present

def die(msg: str, code: int = 1):
    print(msg, file=sys.stderr)
    sys.exit(code)

def get_env(var, required=True, default=None):
    val = os.getenv(var, default)
    if required and not val:
        die(f"Missing required env var: {var}")
    return val

def login_with_password(host: str, username: str, password: str) -> str:
    url = f"{host.rstrip('/')}/api/session"
    try:
        resp = requests.post(url, json={"username": username, "password": password}, timeout=30)
    except Exception as e:
        die(f"Login request failed: {e}")
    if resp.status_code != 200:
        die(f"Login failed: {resp.status_code} {resp.text[:300]}")
    data = resp.json()
    token = data.get("id")
    if not token:
        die("Login response missing session id.")
    return token  # session token

def fetch_csv(host: str, auth_headers: dict, card_id: int, params: dict | None, format_rows: bool | None) -> bytes:
    base = f"{host.rstrip('/')}/api/card/{card_id}/query/csv"
    q = {}
    if params:
        # params do card vão no corpo (POST) em algumas versões; mas como você já usa POST sem body,
        # aqui vamos só tratar format_rows via query string:
        pass
    if format_rows is not None:
        q["format_rows"] = "true" if format_rows else "false"

    from urllib.parse import urlencode
    url = f"{base}?{urlencode(q)}" if q else base
    try:
        resp = requests.post(url, headers=auth_headers, timeout=300)
    except Exception as e:
        die(f"CSV export request failed: {e}")
    if resp.status_code != 200:
        die(f"CSV export failed: {resp.status_code} {resp.text[:400]}")
    return resp.content

def safe_filename(name: str) -> str:
    return "".join(c if c.isalnum() or c in ("-","_",".") else "_" for c in name)

def backup_existing(out_path: str, backup_dir: str | None = None) -> str | None:
    """Se out_path existir, move para <nome>_backup_YYYYmmdd-HHMMSS<ext>.
       Retorna o caminho do backup criado (ou None se não havia o arquivo)."""
    p = Path(out_path)
    if not p.exists():
        return None

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    target_dir = Path(backup_dir) if backup_dir else p.parent
    target_dir.mkdir(parents=True, exist_ok=True)

    backup_name = f"{p.stem}_backup_{ts}{p.suffix}"
    backup_path = target_dir / backup_name
    shutil.move(str(p), str(backup_path))
    print(f"Backup criado: {backup_path}")
    return str(backup_path)


def main():
    parser = argparse.ArgumentParser(description="Export CSVs from Metabase cards.")
    parser.add_argument("--card-id", type=int, action="append", required=True, help="Metabase card (question) ID. Repeatable.")
    parser.add_argument("--param", action="append", help="Card parameter in the form name=value. Repeatable.")
    parser.add_argument("--filename", help="Fixed filename to write (only valid when a single --card-id is used).")
    parser.add_argument("--no-timestamp", action="store_true", help="Do not include timestamp in filenames.")
    parser.add_argument("--use-api-key", action="store_true", help="Use METABASE_API_KEY auth instead of username/password.")
    parser.add_argument("--retries", type=int, default=2, help="Number of retries on failure.")
    parser.add_argument("--backup", action="store_true", help="Se o arquivo de saída existir, faz backup com timestamp antes de sobrescrever.")
    parser.add_argument("--backup-dir", help="Diretório para backups (padrão: mesma pasta do arquivo). Será criado se não existir.")
    parser.add_argument("--format-rows", dest="format_rows", action="store_true", help="Exporta com formatação do Metabase")
    parser.add_argument("--raw", dest="format_rows", action="store_false", help="Valores brutos (0.12 em vez de 12%).")
    parser.set_defaults(format_rows=None)
    parser.add_argument("--quote-all", action="store_true", help="Regrava o CSV com aspas em todos os campos.")
    parser.add_argument("--decimal-comma", action="store_true",help="Converte 1234.56 -> 1.234,56 ao regravar o CSV (inclui números com %).")
    parser.add_argument("--delimiter", default=",",help="Separador ao regravar o CSV (padrão: ,). Use ';' para Excel PT-BR.")
    parser.add_argument("--bom", action="store_true",help="Adiciona BOM UTF-8 no início do arquivo (Excel PT-BR).")
    parser.add_argument("--locale", default=None, help="Locale para formatação no Metabase (ex.: pt-BR).")
    

    args = parser.parse_args()

    host = get_env("METABASE_HOST")
    out_dir = get_env("OUTPUT_DIR")
    file_prefix = os.getenv("FILE_PREFIX", "metabase_export")

    os.makedirs(out_dir, exist_ok=True)

    # Build params dict
    params = {}
    if args.param:
        for p in args.param:
            if "=" not in p:
                die(f"Invalid --param '{p}'. Use name=value.")
            k, v = p.split("=", 1)
            params[k] = v

    # Auth headers
    headers = {}
    if args.use_api_key or os.getenv("METABASE_API_KEY"):
        api_key = get_env("METABASE_API_KEY")
        headers = {"X-Metabase-API-Key": api_key}
    else:
        username = get_env("METABASE_USERNAME", required=False)
        password = get_env("METABASE_PASSWORD", required=False)
        if not (username and password):
            die("Provide METABASE_USERNAME & METABASE_PASSWORD or use --use-api-key with METABASE_API_KEY set.")
        session_token = login_with_password(host, username, password)
        headers = {"X-Metabase-Session": session_token}
        if args.locale:
            headers["Accept-Language"] = args.locale      # ajuda o servidor a formatar números/datas
            headers["X-Metabase-Locale"] = args.locale 

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")

    for idx, card_id in enumerate(args.card_id, start=1):
        # Fetch with simple retry
        last_err = None
        for attempt in range(args.retries + 1):
            try:
                content = fetch_csv(host, headers, card_id, params or None, args.format_rows)
                break
            except SystemExit:
                raise
            except Exception as e:
                last_err = e
                time.sleep(2 * (attempt + 1))
        else:
            die(f"Failed after retries: {last_err}")

        # Decide filename
        if len(args.card_id) == 1 and args.filename:
            fname = safe_filename(args.filename)
        else:
            base = f"{file_prefix}_card{card_id}"
            if not args.no_timestamp:
                base += f"_{ts}"
            fname = f"{safe_filename(base)}.csv"

        out_path = os.path.join(out_dir, fname)

        if args.backup:
            backup_existing(out_path, args.backup_dir)

        
        data_to_write = content
        if args.quote_all or args.decimal_comma or args.delimiter != "," or args.bom:
            data_to_write = rewrite_csv_bytes(
                content,
                quote_all=args.quote_all,
                decimal_comma=args.decimal_comma,
                delimiter=args.delimiter,
                add_bom=args.bom,
            )
        
        with open(out_path, "wb") as f:
            f.write(content)
        print(f"Saved: {out_path}")

    print("Done.")

if __name__ == "__main__":
    main()
