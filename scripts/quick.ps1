# scripts/quick.ps1
# Menú interactivo rápido

function Show-Menu {
    Clear-Host
    Write-Host "🔥 FirefighterAI - Quick Menu" -ForegroundColor Cyan
    Write-Host "=============================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "DESARROLLO LOCAL:" -ForegroundColor Yellow
    Write-Host "  1. Iniciar desarrollo (Docker Compose)" -ForegroundColor White
    Write-Host "  2. Parar desarrollo" -ForegroundColor White
    Write-Host "  3. Ver logs" -ForegroundColor White
    Write-Host "  4. Reconstruir todo" -ForegroundColor White
    Write-Host ""
    Write-Host "SWARM LOCAL (Testing):" -ForegroundColor Yellow
    Write-Host "  5. Inicializar Swarm" -ForegroundColor White
    Write-Host "  6. Iniciar Swarm stack" -ForegroundColor White
    Write-Host "  7. Parar Swarm stack" -ForegroundColor White
    Write-Host "  8. Ver estado Swarm" -ForegroundColor White
    Write-Host ""
    Write-Host "  0. Salir" -ForegroundColor Gray
    Write-Host ""
}

do {
    Show-Menu
    $choice = Read-Host "Selecciona una opción"
    
    switch ($choice) {
        "1" { .\scripts\dev.ps1 start; Pause }
        "2" { .\scripts\dev.ps1 stop; Pause }
        "3" { .\scripts\dev.ps1 logs; Pause }
        "4" { .\scripts\dev.ps1 rebuild; Pause }
        "5" { .\scripts\swarm.ps1 init; Pause }
        "6" { .\scripts\swarm.ps1 start; Pause }
        "7" { .\scripts\swarm.ps1 stop; Pause }
        "8" { .\scripts\swarm.ps1 status; Pause }
        "0" { break }
        default { Write-Host "Opción inválida" -ForegroundColor Red; Pause }
    }
} while ($choice -ne "0")
