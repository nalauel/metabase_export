@echo off
setlocal enabledelayedexpansion
cd /d C:\metabase-export
call .venv\Scripts\activate
REM Ajuste o ID do card e parâmetros abaixo:
python export_metabase_csv.py --card-id 123 --no-timestamp --filename relatorio.csv >> export.log 2>> export.err
