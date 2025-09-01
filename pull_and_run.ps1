$ErrorActionPreference = "Stop"

# Caminho do projeto
Set-Location C:\metabase-export

# (Opcional) Checar acessibilidade do host antes de rodar (garante VPN)
# Substitua pelo host do seu Metabase (sem https:// se usar Test-Connection):
# if (-not (Test-Connection -ComputerName metabase.suaempresa.com -Quiet -Count 1)) {
#   Write-Host "Metabase inacessível (VPN?). Abortando."
#   exit 1
# }

# Atualizar código
git fetch --all
git reset --hard origin/main  # ajuste a branch se necessário

# Rodar o .bat que ativa a venv e executa o export
& "C:\metabase-export\run_export.bat"
