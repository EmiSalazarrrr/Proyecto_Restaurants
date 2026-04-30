param(
    [switch]$DropDatabase
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

Write-Host "Removing generated migration files and __pycache__ folders..."
Get-ChildItem -Path ".\apps" -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem -Path ".\apps" -Recurse -Directory -Filter "migrations" | ForEach-Object {
    Get-ChildItem -Path $_.FullName -File |
        Where-Object { $_.Name -ne "__init__.py" } |
        Remove-Item -Force
}

if ($DropDatabase) {
    Write-Host "Dropping and recreating MariaDB database 'restaurants'..."
    docker compose exec db mariadb -uroot -e "DROP DATABASE IF EXISTS restaurants; CREATE DATABASE restaurants CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
} else {
    Write-Host "Removing migration history for project apps..."
    docker compose exec db mariadb -uroot restaurants -e "DELETE FROM django_migrations WHERE app IN ('usuarios','menu','promociones','pedidos');"
}

Write-Host "Generating fresh initial migrations..."
docker compose exec web python manage.py makemigrations usuarios menu promociones pedidos

Write-Host "Applying migrations..."
docker compose exec web python manage.py migrate

Write-Host "Done."
