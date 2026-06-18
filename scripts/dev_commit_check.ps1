<#
.SYNOPSIS
  Windows-first commit validation helper for AI Health Coach.

.DESCRIPTION
  Use this script from the Windows source-of-truth repo at C:\projects\fitness_ai.
  It intentionally separates docs/tooling checks from code checks so docs-only
  commits do not trigger Ruff, Black, or Pytest noise.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts/dev_commit_check.ps1 -Mode docs-only

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts/dev_commit_check.ps1 -Mode code

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts/dev_commit_check.ps1 -Mode full
#>

param(
    [ValidateSet("docs-only", "code", "full")]
    [string]$Mode = "docs-only"
)

$ErrorActionPreference = "Stop"

function Write-Section {
    param([string]$Title)
    Write-Host ""
    Write-Host "============================================================"
    Write-Host $Title
    Write-Host "============================================================"
}

function Invoke-CheckedCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Command,

        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$CommandArgs
    )

    Write-Host "> $Command $($CommandArgs -join ' ')"
    & $Command @CommandArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $Command $($CommandArgs -join ' ')"
    }
}

function Get-RepoRoot {
    $root = (& git rev-parse --show-toplevel).Trim()
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($root)) {
        throw "This script must be run inside the fitness_ai git repository."
    }
    return $root
}

function Get-ChangedFiles {
    $tracked = @(& git diff --name-only --diff-filter=ACMRT HEAD)
    $untracked = @(& git ls-files --others --exclude-standard)

    return @($tracked + $untracked |
        Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
        Sort-Object -Unique)
}

function Get-ChangedPythonFiles {
    $files = Get-ChangedFiles
    return @($files |
        Where-Object { $_ -match '\.py$' } |
        Where-Object { Test-Path $_ } |
        Sort-Object -Unique)
}

function Test-RequiredProjectMemoryDocs {
    $required = @(
        "docs/project_memory/README.md",
        "docs/project_memory/current_state.md",
        "docs/project_memory/product_vision.md",
        "docs/project_memory/architecture_principles.md",
        "docs/project_memory/backend_truth_contract.md",
        "docs/project_memory/ai_boundaries.md",
        "docs/project_memory/section_registry_summary.md",
        "docs/project_memory/development_workflow.md",
        "docs/project_memory/qa_workflow.md",
        "docs/project_memory/open_questions.md",
        "docs/project_memory/handoffs/architecture_handoff_current.md",
        "docs/project_memory/handoffs/backend_handoff_current.md",
        "docs/project_memory/handoffs/qa_handoff_current.md",
        "docs/project_memory/handoffs/ai_provider_handoff_current.md",
        "docs/project_memory/handoffs/codex_handoff_rules.md"
    )

    $missing = @($required | Where-Object { -not (Test-Path $_) })
    if ($missing.Count -gt 0) {
        Write-Host "Missing required project memory docs:" -ForegroundColor Red
        $missing | ForEach-Object { Write-Host "- $_" -ForegroundColor Red }
        throw "Required project memory docs are missing."
    }

    Write-Host "Required project memory docs exist."
}

function Show-GitStatusAndArtifacts {
    Write-Section "Git status"
    & git status --short

    $statusLines = @(& git status --short)
    $visibleArtifacts = @($statusLines | Where-Object {
        $_ -match '^\?\? .*\.(patch|zip)$' -or
        $_ -match '^\?\? artifacts/' -or
        $_ -match '^\?\? _backup_before_' -or
        $_ -match '^\?\? _patched_'
    })

    if ($visibleArtifacts.Count -gt 0) {
        Write-Host ""
        Write-Host "Visible local patch/snapshot artifacts detected:" -ForegroundColor Yellow
        $visibleArtifacts | ForEach-Object { Write-Host "- $_" -ForegroundColor Yellow }
        Write-Host "Consider adding local-only artifact rules to .git/info/exclude." -ForegroundColor Yellow
    }
}

function Invoke-DocsOnlyCheck {
    Write-Section "Docs/tooling-only validation"
    Invoke-CheckedCommand git diff --check
    Test-RequiredProjectMemoryDocs

    $changed = Get-ChangedFiles
    $runtimePython = @($changed | Where-Object {
        $_ -match '\.py$' -and
        $_ -notmatch '^docs/'
    })

    if ($runtimePython.Count -gt 0) {
        Write-Host "Changed Python files detected during docs-only validation:" -ForegroundColor Yellow
        $runtimePython | ForEach-Object { Write-Host "- $_" -ForegroundColor Yellow }
        Write-Host "Use -Mode code when Python/runtime/test files are intentionally changed." -ForegroundColor Yellow
    }

    Show-GitStatusAndArtifacts
}

function Invoke-CodeCheck {
    Write-Section "Changed-code validation"
    Invoke-CheckedCommand git diff --check

    $pythonFiles = Get-ChangedPythonFiles
    if ($pythonFiles.Count -eq 0) {
        Write-Host "No changed Python files detected. Skipping Ruff and Black."
    }
    else {
        Write-Host "Changed Python files:"
        $pythonFiles | ForEach-Object { Write-Host "- $_" }
        Invoke-CheckedCommand ruff check @pythonFiles --fix
        Invoke-CheckedCommand black @pythonFiles
    }

    Write-Section "Focused safety tests"
    $focusedTests = @(
        "tests/test_full_report_section_registry.py",
        "tests/test_nutrition_report_section_boundary.py",
        "tests/test_full_report_composition_boundary.py",
        "tests/test_report_persistence_boundary.py",
        "tests/test_report_status.py",
        "tests/test_api_smoke.py"
    )

    $existingTests = @($focusedTests | Where-Object { Test-Path $_ })
    if ($existingTests.Count -eq 0) {
        Write-Host "No focused safety test files found. Skipping Pytest."
    }
    else {
        Invoke-CheckedCommand .\.venv\Scripts\python.exe -m pytest @existingTests -q
    }

    Show-GitStatusAndArtifacts
}

function Invoke-FullCheck {
    Write-Section "Full validation"
    Invoke-CheckedCommand git diff --check
    Invoke-CheckedCommand ruff check . --fix
    Invoke-CheckedCommand black .
    Invoke-CheckedCommand .\.venv\Scripts\python.exe -m pytest -q
    Show-GitStatusAndArtifacts
}

$repoRoot = Get-RepoRoot
Set-Location $repoRoot

Write-Section "AI Health Coach commit check"
Write-Host "Repo root: $repoRoot"
Write-Host "Mode: $Mode"

switch ($Mode) {
    "docs-only" { Invoke-DocsOnlyCheck }
    "code" { Invoke-CodeCheck }
    "full" { Invoke-FullCheck }
}

Write-Host ""
Write-Host "Commit check completed for mode: $Mode" -ForegroundColor Green
