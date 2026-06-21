# AI Health Coach repo-owned local command menu.
# Dot-source from PowerShell: . "C:\projects\fitness_ai\scripts\fitness_commands.ps1"

$script:FitnessWindowsRepo = if ($env:FITNESS_WINDOWS_REPO) { $env:FITNESS_WINDOWS_REPO } else { "C:\projects\fitness_ai" }
$script:FitnessLinuxRepo = if ($env:FITNESS_LINUX_REPO) { $env:FITNESS_LINUX_REPO } else { "~/projects/fitness-ai-platform" }
$script:FitnessLinuxSsh = if ($env:FITNESS_LINUX_SSH) { $env:FITNESS_LINUX_SSH } else { "dusty@itsAlwaysDNS" }
$script:FitnessWindowsOllamaUrl = if ($env:FITNESS_WINDOWS_OLLAMA_URL) { $env:FITNESS_WINDOWS_OLLAMA_URL } else { "http://127.0.0.1:11434" }
$script:FitnessLinuxOllamaUrl = if ($env:FITNESS_LINUX_OLLAMA_URL) { $env:FITNESS_LINUX_OLLAMA_URL } else { "http://192.168.1.104:11434" }
$script:FitnessFastApiPort = if ($env:FITNESS_FASTAPI_PORT) { [int]$env:FITNESS_FASTAPI_PORT } else { 8000 }
$script:FitnessStreamlitPort = if ($env:FITNESS_STREAMLIT_PORT) { [int]$env:FITNESS_STREAMLIT_PORT } else { 8510 }

function Assert-FitnessRepo { if (-not (Test-Path $script:FitnessWindowsRepo)) { throw "Repo missing: $script:FitnessWindowsRepo" }; Set-Location $script:FitnessWindowsRepo; if (-not (Test-Path ".git")) { throw "Not repo root: $script:FitnessWindowsRepo" } }
function Invoke-FitnessLinux { param([Parameter(Mandatory=$true)][string]$Command); Write-Host "SSH target: $script:FitnessLinuxSsh"; $Command | ssh $script:FitnessLinuxSsh "bash -s"; if ($LASTEXITCODE -ne 0) { throw "Linux command failed: $LASTEXITCODE" } }
function Test-FitnessPort { param([int]$Port); try { return [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) } catch { return $false } }
function Show-FitnessPort { param([int]$Port); Write-Host "`nPort $Port"; try { $c=Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue; if(-not $c){Write-Host "  none";return}; $c|ForEach-Object{ $p=Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue; Write-Host "  PID=$($_.OwningProcess) Process=$($p.ProcessName)" } } catch { Write-Host "  unable to inspect" } }

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
    Write-Host "  app       Open FastAPI + Streamlit"
    Write-Host ""
    Write-Host "Windows safety/workflow:"
    Write-Host "  fpull     Safe Windows main pull"
    Write-Host "  fbranch   Create feature branch from clean origin/main"
    Write-Host "  fmerge    Merge branch with accepted-final-commit ancestry check"
    Write-Host "  fsnap     Create standard snapshot"
    Write-Host "  fsweep    Artifact contamination sweep"
    Write-Host "  fmem      Run project-memory checks"
    Write-Host "  fports    Show Windows app/Ollama ports"
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
    Write-Host "Windows repo: $script:FitnessWindowsRepo"
    Write-Host "Linux repo: $script:FitnessLinuxRepo"
    Write-Host "Linux SSH: $script:FitnessLinuxSsh"
    Write-Host "Windows Ollama: $script:FitnessWindowsOllamaUrl"
    Write-Host "Linux-to-Windows Ollama: $script:FitnessLinuxOllamaUrl"
    Write-Host "FastAPI: http://127.0.0.1:$script:FitnessFastApiPort"
    Write-Host "Streamlit: http://127.0.0.1:$script:FitnessStreamlitPort"
}

function cdf { Assert-FitnessRepo; Write-Host "Current directory: $(Get-Location)" }
function fpull { Assert-FitnessRepo; git fetch origin --prune; if($LASTEXITCODE){throw "fetch failed"}; git switch main; if($LASTEXITCODE){throw "switch main failed"}; git pull --ff-only origin main; if($LASTEXITCODE){throw "pull failed"}; git status -sb; git log --oneline -5 }
function gsync { fpull }
function gstate { Assert-FitnessRepo; Write-Host "Branch: $(git branch --show-current)"; git status -sb; git log --oneline -1; git fetch origin --prune; Write-Host "main:"; git rev-parse --short main; Write-Host "origin/main:"; git rev-parse --short origin/main; git branch -vv; git ls-files --others --exclude-standard }
function gcheck { Assert-FitnessRepo; git diff --check; if($LASTEXITCODE){throw "diff check failed"}; .\scripts\dev_commit_check.ps1 -Mode code; if($LASTEXITCODE){throw "dev check failed"}; pytest tests/test_project_memory_check.py -q; if($LASTEXITCODE){throw "tests failed"}; python tools/dev_assistant.py memory-check; if($LASTEXITCODE){throw "memory failed"}; python tools/dev_assistant.py stale-doc-check; if($LASTEXITCODE){throw "stale failed"} }
function gacp { param([Parameter(Mandatory=$true)][string]$Message,[switch]$AllowMain); Assert-FitnessRepo; $branch=git branch --show-current; git status -sb; $staged=git diff --cached --name-only; if(-not $staged){throw "No staged files. Stage explicit expected files first."}; $staged; if($branch -eq "main" -and -not $AllowMain){throw "Refusing to commit on main."}; git commit -m $Message; if($LASTEXITCODE){throw "commit failed"}; git push -u origin $branch; if($LASTEXITCODE){throw "push failed"} }

function app { Assert-FitnessRepo; $env:OLLAMA_BASE_URL=$script:FitnessWindowsOllamaUrl; if(Test-FitnessPort $script:FitnessFastApiPort){Write-Warning "FastAPI port busy"} else { Start-Process powershell -ArgumentList @("-NoExit","-ExecutionPolicy","Bypass","-Command","cd '$script:FitnessWindowsRepo'; `$env:PYTHONPATH='$script:FitnessWindowsRepo'; `$env:OLLAMA_BASE_URL='$script:FitnessWindowsOllamaUrl'; python -m uvicorn api.main:app --host 127.0.0.1 --port $script:FitnessFastApiPort --reload") }; if(Test-FitnessPort $script:FitnessStreamlitPort){Write-Warning "Streamlit port busy"} else { Start-Process powershell -ArgumentList @("-NoExit","-ExecutionPolicy","Bypass","-Command","cd '$script:FitnessWindowsRepo'; `$env:PYTHONPATH='$script:FitnessWindowsRepo'; `$env:OLLAMA_BASE_URL='$script:FitnessWindowsOllamaUrl'; python -m streamlit run ui/streamlit_app.py --server.address 127.0.0.1 --server.port $script:FitnessStreamlitPort") }; Start-Process "http://127.0.0.1:$script:FitnessStreamlitPort" }
function fsnap { Assert-FitnessRepo; $commit=git rev-parse --short HEAD; $date=Get-Date -Format "yyyy-MM-dd"; $msg=git log -1 --pretty=%s; $safe=($msg -replace '[^a-zA-Z0-9]+','-').ToLower().Trim('-'); $zipName="..\fitness_ai_snapshot_${date}_${commit}_${safe}.zip"; git archive --format=zip --output=$zipName HEAD; if($LASTEXITCODE){throw "archive failed"}; Write-Host "Created snapshot:"; Write-Host $zipName; Get-Item $zipName }
function fbranch { param([Parameter(Mandatory=$true)][string]$BranchName); Assert-FitnessRepo; git fetch origin --prune; git switch main; git pull --ff-only origin main; if((git rev-parse main) -ne (git rev-parse origin/main)){throw "STOP: local main does not match origin/main"}; if(git status --porcelain){throw "STOP: working tree is dirty"}; git switch -c $BranchName; git status -sb }
function fmerge { param([Parameter(Mandatory=$true)][string]$BranchName,[Parameter(Mandatory=$true)][string]$AcceptedFinalCommit); Assert-FitnessRepo; git fetch origin --prune; git switch main; git pull --ff-only origin main; if((git rev-parse main) -ne (git rev-parse origin/main)){throw "STOP: local main does not match origin/main"}; git merge --no-ff $BranchName; if($LASTEXITCODE){throw "merge failed"}; git merge-base --is-ancestor $AcceptedFinalCommit main; if($LASTEXITCODE){throw "STOP: accepted final feature commit is not an ancestor of main"}; Write-Host "Merge ancestry verification passed. Run validation before pushing." }
function fsweep { Assert-FitnessRepo; $markers=@("content"+"Reference","oai"+"cite","file"+"cite","turn"+"[0-9]+","utm_source="+"chatgpt","chatgpt"+".com","<paste latest commit>","<paste snapshot filename>"); $pattern=$markers -join "|"; git grep -n -E $pattern -- .; if($LASTEXITCODE -eq 1){$global:LASTEXITCODE=0; Write-Host "Artifact sweep clean."} elseif($LASTEXITCODE -ne 0){throw "Artifact sweep failed"} else {throw "Artifact sweep found matches"} }
function fmem { Assert-FitnessRepo; python tools/dev_assistant.py memory-check; if($LASTEXITCODE){throw "memory failed"}; python tools/dev_assistant.py stale-doc-check; if($LASTEXITCODE){throw "stale failed"}; pytest tests/test_project_memory_check.py -q; if($LASTEXITCODE){throw "tests failed"} }
function fports { Show-FitnessPort 8000; Show-FitnessPort 8501; Show-FitnessPort 8510; Show-FitnessPort 11434 }
function fkill { foreach($port in @($script:FitnessFastApiPort,$script:FitnessStreamlitPort)){ $listeners=Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue; foreach($listener in $listeners){ $proc=Get-CimInstance Win32_Process -Filter "ProcessId=$($listener.OwningProcess)" -ErrorAction SilentlyContinue; if($proc.CommandLine -match "uvicorn api\.main:app|streamlit run ui/streamlit_app\.py|$([regex]::Escape($script:FitnessWindowsRepo))"){Stop-Process -Id $listener.OwningProcess -Force} else {Write-Warning "Skipping non-project process $($listener.OwningProcess)"} } }; fports }
function fdoctor { Assert-FitnessRepo; gstate; python --version; python -m pip --version; foreach($p in @("scripts/dev_commit_check.ps1","scripts/fitness_commands.ps1","tools/dev_assistant.py")){Write-Host "$p : $(Test-Path $p)"}; fports; try{Invoke-WebRequest -Uri "$script:FitnessWindowsOllamaUrl/api/tags" -UseBasicParsing -TimeoutSec 3|Out-Null; Write-Host "Windows Ollama reachable"}catch{Write-Warning "Windows Ollama not reachable"} }

function lpull { Invoke-FitnessLinux "set -e`ncd $script:FitnessLinuxRepo`ngit fetch origin --prune`ngit switch main`ngit pull --ff-only origin main`ngit status -sb`ngit log --oneline -5" }
function lstatus { Invoke-FitnessLinux "set -e`ncd $script:FitnessLinuxRepo`npwd`ngit status -sb`ngit log --oneline -3`nps -ef | grep -E 'uvicorn api.main:app|streamlit run ui/streamlit_app.py' | grep -v grep || true`n(ss -ltnp 2>/dev/null || netstat -ltnp 2>/dev/null || true) | grep -E ':8000|:8501|:8510' || true`nfind . -maxdepth 3 -type f \\( -name '*.db' -o -name '*.sqlite' -o -name '*.sqlite3' \\) -print || true" }
function lsetup { Invoke-FitnessLinux "set -e`ncd $script:FitnessLinuxRepo`nsource .venv/bin/activate`ngit fetch origin --prune`ngit switch main`ngit pull --ff-only origin main`npython -m pip install -r requirements.txt`ngit status -sb" }
function lstop { Invoke-FitnessLinux "set -e`ncd $script:FitnessLinuxRepo`npkill -f 'uvicorn api.main:app' || true`npkill -f 'streamlit run ui/streamlit_app.py' || true`nps -ef | grep -E 'uvicorn api.main:app|streamlit run ui/streamlit_app.py' | grep -v grep || true" }
function lrestart { Invoke-FitnessLinux "set -e`ncd $script:FitnessLinuxRepo`nsource .venv/bin/activate`nexport PYTHONPATH=\`pwd\``nexport OLLAMA_BASE_URL=$script:FitnessLinuxOllamaUrl`npkill -f 'uvicorn api.main:app' || true`npkill -f 'streamlit run ui/streamlit_app.py' || true`nnohup python -m uvicorn api.main:app --host 0.0.0.0 --port $script:FitnessFastApiPort >/tmp/fitness_ai_fastapi.log 2>&1 &`nnohup python -m streamlit run ui/streamlit_app.py --server.address 0.0.0.0 --server.port $script:FitnessStreamlitPort >/tmp/fitness_ai_streamlit.log 2>&1 &`nsleep 2`nps -ef | grep -E 'uvicorn api.main:app|streamlit run ui/streamlit_app.py' | grep -v grep || true" }
function lupdate { lpull; lrestart }
function lsh { ssh -t $script:FitnessLinuxSsh "cd $script:FitnessLinuxRepo && source .venv/bin/activate && echo 'AI Health Coach Linux project ready.' && git status -sb && exec bash -i" }
function lvalidate { Invoke-FitnessLinux "set -e`ncd $script:FitnessLinuxRepo`nsource .venv/bin/activate`npytest tests/test_project_memory_check.py -q`npython tools/dev_assistant.py memory-check`npython tools/dev_assistant.py stale-doc-check" }
function lollama { Invoke-FitnessLinux "set -e`nprintf 'Checking Windows Ollama from Linux: $script:FitnessLinuxOllamaUrl/api/tags\\n'`ncurl -fsS --max-time 5 $script:FitnessLinuxOllamaUrl/api/tags >/dev/null`necho 'Windows Ollama reachable from Linux.'" }
