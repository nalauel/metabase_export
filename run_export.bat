@echo off
setlocal enabledelayedexpansion
cd /d C:\Alan\Projetos\metabase_export

REM Ajuste o ID do card e parâmetros abaixo:

set PY=C:\Alan\Projetos\metabase_export\.venv\Scripts\python.exe

%PY% export_metabase_csv.py --card-id 331 --no-timestamp --filename modelo__despesas_por_unidade_de_negocio.csv --backup

%PY% export_metabase_csv.py --card-id 34 --no-timestamp --filename modelo__dados_financeiros_dos_projetos_e_dos_clientes.csv --backup

%PY% export_metabase_csv.py --card-id 421 --no-timestamp --filename dia.csv