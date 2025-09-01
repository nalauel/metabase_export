
# Metabase CSV Export — Starter

Este projeto permite **exportar CSV de uma pergunta (card) do Metabase** e salvar localmente. Você vai **desenvolver no macOS** e **executar no Windows** (onde a VPN está).

## 0) Pré-requisitos
- macOS: Python 3.10+ e Git
- Windows: Python 3.10+ e Git
- Acesso ao Metabase (via VPN no Windows)
- Um repositório no GitHub (você já conectou)

---

## 1) Setup no macOS (desenvolvimento)

Abra o Terminal e execute:

```bash
# 1. criar pasta do projeto
mkdir -p ~/metabase-export && cd ~/metabase-export

# 2. criar venv e instalar deps
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. criar .env a partir do exemplo
cp .env.example .env
# edite .env e ajuste METABASE_HOST, OUTPUT_DIR etc.
```

> **IMPORTANTE**: No mac você pode não ter VPN. Use um card do Metabase que não dependa da VPN só para validar o script, ou faça apenas testes de sintaxe. A execução “valendo” vai acontecer no Windows.

### Git/GitHub

Crie um repositório no GitHub (pelo site). Depois:

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/SEU_REPO.git
git push -u origin main
```

> Nunca suba `.env` (já está no `.gitignore`).

---

## 2) Teste local (opcional)
No macOS, rode algo simples (se tiver um card acessível sem VPN):
```bash
source .venv/bin/activate
python export_metabase_csv.py --card-id 123 --no-timestamp --filename teste.csv
```
O arquivo aparecerá em `OUTPUT_DIR` (definido no `.env`).

---

## 3) Setup no Windows (execução com VPN)

Abra o **PowerShell**:

```powershell
cd C:\
git clone https://github.com/SEU_USUARIO/SEU_REPO.git metabase-export
cd C:\metabase-export

py -m venv .venv
C:\metabase-export\.venv\Scripts\activate
pip install -r requirements.txt

# crie o .env local com as credenciais reais e um OUTPUT_DIR no Windows
Copy-Item .env.example .env
notepad .env
```

### Script de execução (já incluído)
- `run_export.bat` — ativa o venv e roda o script
- `pull_and_run.ps1` — dá `git pull` para pegar suas últimas alterações e depois executa

Edite `run_export.bat` e ajuste o(s) `--card-id` e parâmetros.

Teste manualmente (com VPN conectada):
```powershell
C:\metabase-export\.venv\Scripts\activate
python export_metabase_csv.py --card-id 123 --no-timestamp --filename relatorio.csv
```

---

## 4) Agendar no Windows (Task Scheduler)

- Abra **Agendador de Tarefas** → **Criar Tarefa…**
- **Ação**: `powershell.exe`
- **Argumentos**: `-ExecutionPolicy Bypass -File "C:\metabase-export\pull_and_run.ps1"`
- **Disparador**: diário no horário desejado
- Marque **Executar mesmo se o usuário não estiver conectado** (se quiser headless)

Linha de comando equivalente:
```powershell
schtasks /Create /TN "MetabaseCSV" /TR "powershell -ExecutionPolicy Bypass -File C:\metabase-export\pull_and_run.ps1" /SC DAILY /ST 07:30 /RL HIGHEST /F
```

---

## 5) Exemplos de uso
```bash
# múltiplos cards
python export_metabase_csv.py --card-id 123 --card-id 456

# com parâmetros do card
python export_metabase_csv.py --card-id 123 --param start_date=2025-08-01 --param status=active

# usando API Key
python export_metabase_csv.py --card-id 123 --use-api-key
```

- Nome fixo (`--no-timestamp --filename relatorio.csv`) é útil para integrações.
- Com timestamp (padrão) gera histórico.

---

## 6) Dicas
- Salve `OUTPUT_DIR` em OneDrive/Google Drive (Windows) para ver os CSVs no Mac automaticamente.
- Prefira **API Key (PAT)** com permissões mínimas no Metabase.
- Logs: veja `export.log` e `export.err` quando usar os scripts de agendamento.

Boa jornada! ✨
