# Install AI Health Coach repo-owned PowerShell command menu.
$ErrorActionPreference = "Stop"
$fitnessCommands = if ($env:FITNESS_WINDOWS_REPO) { Join-Path $env:FITNESS_WINDOWS_REPO "scripts\fitness_commands.ps1" } else { "C:\projects\fitness_ai\scripts\fitness_commands.ps1" }
if (-not (Test-Path $fitnessCommands)) { throw "Command script not found: $fitnessCommands" }
$profilePath = $PROFILE
$profileDir = Split-Path -Parent $profilePath
if (-not (Test-Path $profileDir)) { New-Item -ItemType Directory -Path $profileDir -Force | Out-Null }
if (Test-Path $profilePath) { $backup = "$profilePath.fitness-backup-$(Get-Date -Format yyyyMMddHHmmss)"; Copy-Item $profilePath $backup; Write-Host "Backed up PowerShell profile to: $backup" } else { New-Item -ItemType File -Path $profilePath -Force | Out-Null }
$block = @"

# AI Health Coach command menu
`$fitnessCommands = "C:\projects\fitness_ai\scripts\fitness_commands.ps1"
if (Test-Path `$fitnessCommands) {
    . `$fitnessCommands
}
"@
$current = Get-Content $profilePath -Raw -ErrorAction SilentlyContinue
if ($current -notmatch [regex]::Escape("AI Health Coach command menu")) { Add-Content -Path $profilePath -Value $block; Write-Host "Added AI Health Coach command menu loader to profile." } else { Write-Host "AI Health Coach command menu loader already present. No duplicate added." }
Write-Host "Reload your profile with: . `$PROFILE"
