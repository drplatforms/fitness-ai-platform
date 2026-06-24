# AI Health Coach repo-owned local command menu.
# Dot-source from PowerShell: . "C:\projects\fitness_ai\scripts\fitness_commands.ps1"

$script:FitnessWindowsRepo = if ($env:FITNESS_WINDOWS_REPO) { $env:FITNESS_WINDOWS_REPO } else { "C:\projects\fitness_ai" }
$script:FitnessLinuxRepo = if ($env:FITNESS_LINUX_REPO) { $env:FITNESS_LINUX_REPO } else { "~/projects/fitness-ai-platform" }
$script:FitnessLinuxSsh = if ($env:FITNESS_LINUX_SSH) { $env:FITNESS_LINUX_SSH } else { "dusty@itsAlwaysDNS" }
$script:FitnessWindowsOllamaUrl = if ($env:FITNESS_WINDOWS_OLLAMA_URL) { $env:FITNESS_WINDOWS_OLLAMA_URL } else { "http://127.0.0.1:11434" }
$script:FitnessLinuxOllamaUrl = if ($env:FITNESS_LINUX_OLLAMA_URL) { $env:FITNESS_LINUX_OLLAMA_URL } else { "http://192.168.1.104:11434" }
$script:FitnessFastApiPort = if ($env:FITNESS_FASTAPI_PORT) { [int]$env:FITNESS_FASTAPI_PORT } else { 8000 }
$script:FitnessWindowsPython = if ($env:FITNESS_WINDOWS_PYTHON) { $env:FITNESS_WINDOWS_PYTHON } else { Join-Path $script:FitnessWindowsRepo ".venv\Scripts\python.exe" }
$script:FitnessStreamlitPort = if ($env:FITNESS_STREAMLIT_PORT) { [int]$env:FITNESS_STREAMLIT_PORT } else { 8510 }
$script:FitnessLinuxStreamlitPort = if ($env:FITNESS_LINUX_STREAMLIT_PORT) { [int]$env:FITNESS_LINUX_STREAMLIT_PORT } else { 8501 }
$script:FitnessLinuxStreamlitUrl = if ($env:FITNESS_LINUX_STREAMLIT_URL) { $env:FITNESS_LINUX_STREAMLIT_URL } else { $linuxHost = $script:FitnessLinuxSsh; if ($linuxHost -match "@(.+)$") { $linuxHost = $Matches[1] }; "http://${linuxHost}:$script:FitnessLinuxStreamlitPort" }

function Assert-FitnessRepo { if (-not (Test-Path $script:FitnessWindowsRepo)) { throw "Repo missing: $script:FitnessWindowsRepo" }; Set-Location $script:FitnessWindowsRepo; if (-not (Test-Path ".git")) { throw "Not repo root: $script:FitnessWindowsRepo" } }
function ConvertTo-FitnessLinuxSshScript {
    param([Parameter(Mandatory=$true)][string]$Command)
    $normalized = $Command -replace "`r`n", "`n"
    $normalized = $normalized -replace "`r", "`n"
    return $normalized.TrimEnd("`n") + "`n"
}

function Invoke-FitnessLinux {
    param([Parameter(Mandatory=$true)][string]$Command)
    Write-Host "SSH target: $script:FitnessLinuxSsh"
    $normalized = ConvertTo-FitnessLinuxSshScript $Command
    $payload = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($normalized))
    ssh $script:FitnessLinuxSsh "printf '%s' '$payload' | base64 -d | bash -s"
    if ($LASTEXITCODE -ne 0) { throw "Linux command failed: $LASTEXITCODE" }
}
function Test-FitnessPort { param([int]$Port); try { return [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) } catch { return $false } }
function Show-FitnessPort { param([int]$Port); Write-Host "`nPort $Port"; try { $c=Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue; if(-not $c){Write-Host "  none";return}; $c|ForEach-Object{ $p=Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue; Write-Host "  PID=$($_.OwningProcess) Process=$($p.ProcessName)" } } catch { Write-Host "  unable to inspect" } }

function Get-FitnessWindowsPython {
    $root = Get-FitnessProjectRoot

    if ($env:FITNESS_WINDOWS_PYTHON) {
        return $env:FITNESS_WINDOWS_PYTHON
    }

    $pythonExe = Join-Path $root ".venv\Scripts\python.exe"

    if (-not (Test-Path $pythonExe)) {
        throw "Windows-local Python was not found at $pythonExe. Activate or create the repo .venv first."
    }

    return $pythonExe
}

function fitness {
    Write-Host "AI Health Coach commands"
    Write-Host ""
    Write-Host "Daily:"
    Write-Host "  cdf       Go to Windows project"
    Write-Host "  gsync     Pull latest on Windows"
    Write-Host "  gstate    Show Windows Git status"
    Write-Host "  gcheck    Run pre-commit + pytest"
    Write-Host "  gacp      Commit and push staged files"
    Write-Host "  lupdate   Pull latest on Linux + restart app"
    Write-Host "  app       Start Linux FastAPI + Streamlit and open app"
    Write-Host "  wapp      Start Windows-local FastAPI + Streamlit"
    Write-Host "  wstatus   Show Windows-local FastAPI + Streamlit status"
    Write-Host "  wstop     Stop Windows-local FastAPI + Streamlit"
    Write-Host ""
    Write-Host "Windows safety/workflow:"
    Write-Host "  fpull     Safe Windows main pull"
    Write-Host "  fbranch   Create feature branch from clean origin/main"
    Write-Host "  fmerge    Merge branch with accepted-final-commit ancestry check"
    Write-Host "  fsnap     Create standard snapshot"
    Write-Host "  fsweep    Artifact contamination sweep"
    Write-Host "  fmem      Run project-memory checks"
    Write-Host "  fports    Show Windows-side app/Ollama ports only"
    Write-Host "  fkill     Stop Windows FastAPI/Streamlit project processes"
    Write-Host "  fdoctor   Full local environment sanity check"
    Write-Host ""
    Write-Host "Linux:"
    Write-Host "  lstatus   Linux Git/app/DB status"
    Write-Host "  lsetup    Pull latest on Linux + install requirements"
    Write-Host "  lpull     Linux pull only, no restart"
    Write-Host "  lvalidate Run Linux project-memory validation"
    Write-Host "  lollama   Check Linux can reach Windows Ollama"
    Write-Host "  lrestart  Restart Linux FastAPI + Streamlit"
    Write-Host "  lstop     Stop Linux FastAPI + Streamlit"
    Write-Host "  lsh       SSH into Linux project with venv active"
    Write-Host ""
    Write-Host "Windows repo: C:\projects\fitness_ai"
    Write-Host "Linux repo: ~/projects/fitness-ai-platform"
    Write-Host "Linux SSH: dusty@itsAlwaysDNS"
    Write-Host "Windows Ollama: $FitnessWindowsOllamaUrl"
    Write-Host "Linux-to-Windows Ollama: $FitnessLinuxOllamaUrl"
    Write-Host "Linux Streamlit: $FitnessLinuxStreamlitUrl"
    Write-Host "Windows-local FastAPI: http://127.0.0.1:8000"
    Write-Host "Windows-local Streamlit: http://127.0.0.1:8510"
}

function cdf { Assert-FitnessRepo; Write-Host "Current directory: $(Get-Location)" }
function fpull { Assert-FitnessRepo; git fetch origin --prune; if($LASTEXITCODE){throw "fetch failed"}; git switch main; if($LASTEXITCODE){throw "switch main failed"}; git pull --ff-only origin main; if($LASTEXITCODE){throw "pull failed"}; git status -sb; git log -5 --oneline --decorate }
function gsync { fpull }
function gstate { Assert-FitnessRepo; Write-Host "Branch: $(git branch --show-current)"; git status -sb; git log --oneline -1; git fetch origin --prune; Write-Host "main:"; git rev-parse --short main; Write-Host "origin/main:"; git rev-parse --short origin/main; git branch -vv; git ls-files --others --exclude-standard }
function gcheck { Assert-FitnessRepo; git diff --check; if($LASTEXITCODE){throw "diff check failed"}; .\scripts\dev_commit_check.ps1 -Mode code; if($LASTEXITCODE){throw "dev check failed"}; pytest tests/test_project_memory_check.py -q; if($LASTEXITCODE){throw "tests failed"}; python tools/dev_assistant.py memory-check; if($LASTEXITCODE){throw "memory failed"}; python tools/dev_assistant.py stale-doc-check; if($LASTEXITCODE){throw "stale failed"} }
function gacp { param([Parameter(Mandatory=$true)][string]$Message,[switch]$AllowMain); Assert-FitnessRepo; $branch=git branch --show-current; git status -sb; $staged=git diff --cached --name-only; if(-not $staged){throw "No staged files. Stage explicit expected files first."}; $staged; if($branch -eq "main" -and -not $AllowMain){throw "Refusing to commit on main."}; git commit -m $Message; if($LASTEXITCODE){throw "commit failed"}; git push -u origin $branch; if($LASTEXITCODE){throw "push failed"} }

function app {
    lrestart
    Write-Host "Opening Linux Streamlit: $script:FitnessLinuxStreamlitUrl"
    Start-Process $script:FitnessLinuxStreamlitUrl
}

function wapp {
    Write-Host "Windows-local FastAPI + Streamlit"

    $root = Get-FitnessProjectRoot
    $python = Get-FitnessWindowsPython

    $env:PYTHONPATH = $root
    $env:FITNESS_API_BASE_URL = "http://127.0.0.1:8000"
    $env:FITNESS_WINDOWS_OLLAMA_URL = $FitnessWindowsOllamaUrl

    $apiCommand = "cd '$root'; `$env:PYTHONPATH = '$root'; & '$python' -m uvicorn api.main:app --host 127.0.0.1 --port 8000"
    $streamlitCommand = "cd '$root'; `$env:PYTHONPATH = '$root'; `$env:FITNESS_API_BASE_URL = 'http://127.0.0.1:8000'; `$env:FITNESS_WINDOWS_OLLAMA_URL = '$FitnessWindowsOllamaUrl'; & '$python' -m streamlit run ui/streamlit_app.py --server.address 127.0.0.1 --server.port 8510"

    Write-Host "Starting Windows-local FastAPI on http://127.0.0.1:8000"
    Start-Process powershell -ArgumentList @("-NoExit", "-Command", $apiCommand)

    Start-Sleep -Seconds 2

    Write-Host "Starting Windows-local Streamlit on http://127.0.0.1:8510"
    Start-Process powershell -ArgumentList @("-NoExit", "-Command", $streamlitCommand)

    Write-Host ""
    Write-Host "Windows-local FastAPI:   http://127.0.0.1:8000"
    Write-Host "Windows-local Streamlit: http://127.0.0.1:8510"
    Write-Host "Windows Ollama: $FitnessWindowsOllamaUrl"
    Write-Host "Linux Streamlit remains canonical validation: $FitnessLinuxStreamlitUrl"

    Start-Process "http://127.0.0.1:8510"
}

function wstatus {
    Write-Host "Windows-local FastAPI / Streamlit status"
    Write-Host "Windows-side port inspection via fports:"
    fports
    Write-Host ""
    Write-Host "Linux status remains available separately through lstatus; wstatus uses Windows-local checks only."

    foreach ($port in @(8000, 8510)) {
        $listeners = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue

        if (-not $listeners) {
            Write-Host "Port ${port}: not listening"
            continue
        }

        foreach ($listener in $listeners) {
            $proc = Get-Process -Id $listener.OwningProcess -ErrorAction SilentlyContinue
            $procName = if ($proc) { $proc.ProcessName } else { "unknown" }
            Write-Host "Port ${port}: listening pid=$($listener.OwningProcess) process=$procName"
        }
    }
}

function wstop {
    Write-Host "Stopping Windows-local FastAPI / Streamlit project processes"
    fkill
    wstatus
}

function fsnap { Assert-FitnessRepo; $commit=git rev-parse --short HEAD; $date=Get-Date -Format "yyyy-MM-dd"; $msg=git log -1 --pretty=%s; $safe=($msg -replace '[^a-zA-Z0-9]+','-').ToLower().Trim('-'); $zipName="..\fitness_ai_snapshot_${date}_${commit}_${safe}.zip"; git archive --format=zip --output=$zipName HEAD; if($LASTEXITCODE){throw "archive failed"}; Write-Host "Created snapshot:"; Write-Host $zipName; Get-Item $zipName }
function fbranch { param([Parameter(Mandatory=$true)][string]$BranchName); Assert-FitnessRepo; git fetch origin --prune; git switch main; git pull --ff-only origin main; if((git rev-parse main) -ne (git rev-parse origin/main)){throw "STOP: local main does not match origin/main"}; if(git status --porcelain){throw "STOP: working tree is dirty"}; git switch -c $BranchName; git status -sb }
function fmerge { param([Parameter(Mandatory=$true)][string]$BranchName,[Parameter(Mandatory=$true)][string]$AcceptedFinalCommit); Assert-FitnessRepo; git fetch origin --prune; git switch main; git pull --ff-only origin main; if((git rev-parse main) -ne (git rev-parse origin/main)){throw "STOP: local main does not match origin/main"}; git merge --no-ff $BranchName; if($LASTEXITCODE){throw "merge failed"}; git merge-base --is-ancestor $AcceptedFinalCommit main; if($LASTEXITCODE){throw "STOP: accepted final feature commit is not an ancestor of main"}; Write-Host "Merge ancestry verification passed. Run validation before pushing." }
function fsweep { Assert-FitnessRepo; $markers=@("content"+"Reference","oai"+"cite","file"+"cite","turn"+"[0-9]+","utm_source="+"chat"+"gpt","chat"+"gpt"+"."+"com","<paste latest"+" commit>","<paste snapshot"+" filename>"); $pattern=$markers -join "|"; git grep -n -E $pattern -- .; if($LASTEXITCODE -eq 1){$global:LASTEXITCODE=0; Write-Host "Artifact sweep clean."} elseif($LASTEXITCODE -ne 0){throw "Artifact sweep failed"} else {throw "Artifact sweep found matches"} }
function fmem { Assert-FitnessRepo; python tools/dev_assistant.py memory-check; if($LASTEXITCODE){throw "memory failed"}; python tools/dev_assistant.py stale-doc-check; if($LASTEXITCODE){throw "stale failed"}; pytest tests/test_project_memory_check.py -q; if($LASTEXITCODE){throw "tests failed"} }

function fports {
    Write-Host "Windows-side ports only - app/Ollama"
    Write-Host "  FastAPI:        http://127.0.0.1:8000"
    Write-Host "  Streamlit:      http://127.0.0.1:8510"
    Write-Host "  Windows Ollama: $FitnessWindowsOllamaUrl"
    Write-Host ""

    foreach ($port in @(8000, 8510, 11434)) {
        $listeners = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue

        if (-not $listeners) {
            Write-Host "Port ${port}: not listening"
            continue
        }

        foreach ($listener in $listeners) {
            $proc = Get-Process -Id $listener.OwningProcess -ErrorAction SilentlyContinue
            $procName = if ($proc) { $proc.ProcessName } else { "unknown" }
            Write-Host "Port ${port}: listening pid=$($listener.OwningProcess) process=$procName"
        }
    }
}

function fkill { foreach($port in @($script:FitnessFastApiPort,$script:FitnessStreamlitPort)){ $listeners=Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue; foreach($listener in $listeners){ $proc=Get-CimInstance Win32_Process -Filter "ProcessId=$($listener.OwningProcess)" -ErrorAction SilentlyContinue; if($proc.CommandLine -match "uvicorn api\.main:app|streamlit run ui/streamlit_app\.py|$([regex]::Escape($script:FitnessWindowsRepo))"){Stop-Process -Id $listener.OwningProcess -Force} else {Write-Warning "Skipping non-project process $($listener.OwningProcess)"} } }; fports }
function fdoctor { Assert-FitnessRepo; gstate; python --version; python -m pip --version; foreach($p in @("scripts/dev_commit_check.ps1","scripts/fitness_commands.ps1","tools/dev_assistant.py")){Write-Host "$p : $(Test-Path $p)"}; fports; try{Invoke-WebRequest -Uri "$script:FitnessWindowsOllamaUrl/api/tags" -UseBasicParsing -TimeoutSec 3|Out-Null; Write-Host "Windows Ollama reachable"}catch{Write-Warning "Windows Ollama not reachable"} }

function Join-FitnessLinuxLines {
    param([Parameter(Mandatory=$true)][string[]]$Lines)
    return ($Lines -join "`n")
}

function lpull {
    $cmd = Join-FitnessLinuxLines @(
        "set -e",
        "cd $script:FitnessLinuxRepo",
        "git fetch origin --prune",
        "git switch main",
        "git pull --ff-only origin main",
        "git status -sb",
        "git log --oneline --decorate -n 5"
    )
    Invoke-FitnessLinux $cmd
}

function lstatus {
    $cmd = Join-FitnessLinuxLines @(
        "set -e",
        "cd $script:FitnessLinuxRepo",
        "printf '%s\n' 'Linux project:'",
        "pwd",
        "printf '%s\n' 'Git status:'",
        "git status -sb",
        "printf '%s\n' 'Recent commits:'",
        "git log --oneline --decorate -n 5",
        "printf '%s\n' 'Project app processes:'",
        "ps -ef | grep -E 'uvicorn api.main:app|streamlit run ui/streamlit_app.py' | grep -v grep || true",
        "printf '%s\n' 'Project ports:'",
        "if command -v ss >/dev/null 2>&1; then",
        "  ss -ltnp 2>/dev/null | grep -E ':8000|:8501|:8510' || true",
        "elif command -v netstat >/dev/null 2>&1; then",
        "  netstat -ltnp 2>/dev/null | grep -E ':8000|:8501|:8510' || true",
        "else",
        "  printf '%s\n' 'No ss or netstat command available.'",
        "fi",
        "printf '%s\n' 'DB files:'",
        "find . -maxdepth 3 -type f -name '*.db' -print || true",
        "find . -maxdepth 3 -type f -name '*.sqlite' -print || true",
        "find . -maxdepth 3 -type f -name '*.sqlite3' -print || true"
    )
    Invoke-FitnessLinux $cmd
}

function lsetup {
    $cmd = Join-FitnessLinuxLines @(
        "set -e",
        "cd $script:FitnessLinuxRepo",
        "source .venv/bin/activate",
        "git fetch origin --prune",
        "git switch main",
        "git pull --ff-only origin main",
        "python -m pip install -r requirements.txt",
        "git status -sb"
    )
    Invoke-FitnessLinux $cmd
}

function lstop {
    $cmd = Join-FitnessLinuxLines @(
        "set -e",
        "cd $script:FitnessLinuxRepo",
        "tmux kill-session -t fitness-api 2>/dev/null || true",
        "tmux kill-session -t fitness-ui 2>/dev/null || true",
        "pkill -f 'uvicorn api.main:app' || true",
        "pkill -f 'streamlit run ui/streamlit_app.py' || true",
        "if command -v fuser >/dev/null 2>&1; then",
        "  fuser -k $script:FitnessFastApiPort/tcp 2>/dev/null || true",
        "  fuser -k $script:FitnessLinuxStreamlitPort/tcp 2>/dev/null || true",
        "  fuser -k $script:FitnessStreamlitPort/tcp 2>/dev/null || true",
        "fi",
        "ps -ef | grep -E 'uvicorn api.main:app|streamlit run ui/streamlit_app.py' | grep -v grep || true"
    )
    Invoke-FitnessLinux $cmd
}

function lrestart {
    $cmd = Join-FitnessLinuxLines @(
        "set -e",
        "cd $script:FitnessLinuxRepo",
        "source .venv/bin/activate",
        "tmux kill-session -t fitness-api 2>/dev/null || true",
        "tmux kill-session -t fitness-ui 2>/dev/null || true",
        "pkill -f 'uvicorn api.main:app' || true",
        "pkill -f 'streamlit run ui/streamlit_app.py' || true",
        "if command -v fuser >/dev/null 2>&1; then",
        "  fuser -k $script:FitnessFastApiPort/tcp 2>/dev/null || true",
        "  fuser -k $script:FitnessLinuxStreamlitPort/tcp 2>/dev/null || true",
        "  fuser -k $script:FitnessStreamlitPort/tcp 2>/dev/null || true",
        "fi",
        "tmux new -d -s fitness-api bash -lc 'cd $script:FitnessLinuxRepo && source .venv/bin/activate && export PYTHONPATH=$script:FitnessLinuxRepo && export OLLAMA_BASE_URL=$script:FitnessLinuxOllamaUrl && exec python -m uvicorn api.main:app --host 0.0.0.0 --port $script:FitnessFastApiPort'",
        "tmux new -d -s fitness-ui bash -lc 'cd $script:FitnessLinuxRepo && source .venv/bin/activate && exec python -m streamlit run ui/streamlit_app.py --server.address 0.0.0.0 --server.port $script:FitnessLinuxStreamlitPort'",
        "sleep 3",
        "tmux ls || true",
        "ps -ef | grep -E 'uvicorn api.main:app|streamlit run ui/streamlit_app.py' | grep -v grep || true"
    )
    Invoke-FitnessLinux $cmd
}

function lupdate {
    lpull
    lrestart
}

function lsh {
    ssh -t $script:FitnessLinuxSsh "cd $script:FitnessLinuxRepo && source .venv/bin/activate && echo 'AI Health Coach Linux project ready.' && git status -sb && exec bash -i"
}

function lvalidate {
    $cmd = Join-FitnessLinuxLines @(
        "set -e",
        "cd $script:FitnessLinuxRepo",
        "source .venv/bin/activate",
        "pytest tests/test_project_memory_check.py -q",
        "python tools/dev_assistant.py memory-check",
        "python tools/dev_assistant.py stale-doc-check"
    )
    Invoke-FitnessLinux $cmd
}

function lollama {
    $cmd = Join-FitnessLinuxLines @(
        "set -e",
        "printf '%s\n' 'Checking Windows Ollama from Linux: $script:FitnessLinuxOllamaUrl/api/tags'",
        "curl -fsS --max-time 5 $script:FitnessLinuxOllamaUrl/api/tags >/dev/null",
        "printf '%s\n' 'Windows Ollama reachable from Linux.'"
    )
    Invoke-FitnessLinux $cmd
}

function Get-FitnessProjectRoot {
    if ($PSScriptRoot) {
        return (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
    }

    return (Get-Location).Path
}

function Get-FitnessWindowsPython {
    $root = Get-FitnessProjectRoot
    $pythonExe = Join-Path $root ".venv\Scripts\python.exe"

    if (-not (Test-Path $pythonExe)) {
        throw "Windows-local Python was not found at $pythonExe. Activate or create the repo .venv first."
    }

    return $pythonExe
}
