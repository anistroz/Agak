# ClipKontrast - one-click start for Windows.
# First run: installs Python and ffmpeg if missing (with winget), sets up a private Python folder (.venv)
# and the packages. Every run: starts ClipKontrast and opens it in your browser.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Say($msg, $color = "White") { Write-Host "  $msg" -ForegroundColor $color }
function Fail($msg) { Write-Host ""; Say $msg "Red"; Write-Host ""; exit 1 }
function Refresh-Path {
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
}
function Has-Winget { [bool](Get-Command winget -ErrorAction SilentlyContinue) }

Write-Host ""
Say "=== ClipKontrast ===" "Green"
Write-Host ""

# ---- Long folder paths break the speech model on Windows (260 character limit)
if ($Root.Length -gt 80) {
    Say "This folder's path is long:" "Yellow"
    Say "  $Root" "Yellow"
    Say "If the speech model fails to load, move the folder to C:\ClipKontrast and run this again." "Yellow"
    Write-Host ""
}

# ---- Python 3.10+
function Find-Python {
    foreach ($cand in @("py -3.12", "py -3.11", "py -3.10", "py -3", "python")) {
        $parts = $cand -split " "
        $exe = $parts[0]; $args_ = @($parts | Select-Object -Skip 1)
        if (-not (Get-Command $exe -ErrorAction SilentlyContinue)) { continue }
        try {
            $ok = & $exe @args_ -c "import sys; print(1 if (3,10) <= sys.version_info[:2] < (3,14) else 0)" 2>$null
            if ($LASTEXITCODE -eq 0 -and "$ok".Trim() -eq "1") { return @($exe) + $args_ }
        } catch { }
    }
}

$Py = @(Find-Python)
if ($Py.Count -eq 0) {
    Say "Python 3.10-3.13 not found. Installing Python 3.12..." "Cyan"
    if (-not (Has-Winget)) {
        Start-Process "https://www.python.org/downloads/release/python-3129/"
        Fail "winget is not available. Install Python 3.12 from the page that just opened (tick 'Add python.exe to PATH'), then run this again."
    }
    winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements
    Refresh-Path
    $Py = @(Find-Python)
    if ($Py.Count -eq 0) { Fail "Python was installed but Windows has not picked it up yet. Close this window and double-click Start-ClipKontrast-Windows.bat again." }
}
$PyExe = $Py[0]; $PyArgs = @($Py | Select-Object -Skip 1)
Say ("Python: " + (& $PyExe @PyArgs --version)) "Gray"

# ---- ffmpeg (ClipKontrast also finds winget's install folder by itself, so no PATH refresh is needed)
$haveFfmpeg = [bool](Get-Command ffmpeg -ErrorAction SilentlyContinue) -or
    (Test-Path "$env:LOCALAPPDATA\Microsoft\WinGet\Links\ffmpeg.exe") -or
    [bool](Get-ChildItem "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" -Filter "Gyan.FFmpeg*" -Directory -ErrorAction SilentlyContinue)
if (-not $haveFfmpeg) {
    Say "ffmpeg not found. Installing it..." "Cyan"
    if (Has-Winget) {
        winget install -e --id Gyan.FFmpeg --accept-package-agreements --accept-source-agreements
        Refresh-Path
    } else {
        Say "winget is not available: ClipKontrast will show how to install ffmpeg in the dashboard." "Yellow"
    }
}

# ---- Private Python folder + packages (only reinstalled when requirements.txt changes)
$Venv = Join-Path $Root ".venv"
$VPy = Join-Path $Venv "Scripts\python.exe"
if (-not (Test-Path $VPy)) {
    Say "Setting up (one time)..." "Cyan"
    & $PyExe @PyArgs -m venv $Venv
    if ($LASTEXITCODE -ne 0) { Fail "Could not create the Python environment." }
}
$Stamp = Join-Path $Venv "requirements.sha"
$Hash = (Get-FileHash (Join-Path $Root "requirements.txt") -Algorithm SHA256).Hash
if (-not (Test-Path $Stamp) -or (Get-Content $Stamp -Raw).Trim() -ne $Hash) {
    Say "Installing packages (one time, a few minutes)..." "Cyan"
    & $VPy -m pip install --upgrade pip --disable-pip-version-check -q
    & $VPy -m pip install -r requirements.txt --disable-pip-version-check
    if ($LASTEXITCODE -ne 0) { Fail "Installing packages failed. Check your internet connection and run this again." }
    Set-Content -Path $Stamp -Value $Hash
}

# ---- Start
Write-Host ""
Say "Starting ClipKontrast. The first start downloads the speech model (about 480 MB, once)." "Green"
Say "Your browser opens by itself. Keep this window open while you use ClipKontrast; close it to stop." "Green"
Write-Host ""
$env:CLIPKONTRAST_OPEN_BROWSER = "1"
$env:PYTHONWARNINGS = "ignore::DeprecationWarning"

# ---- Already running? Then just open it. Port taken by another program? Then use the next free one.
function Port-Free($p) {
    try { $l = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $p); $l.Start(); $l.Stop(); return $true }
    catch { return $false }
}
function Is-ClipKontrast($p) {
    try {
        $r = Invoke-WebRequest -UseBasicParsing -TimeoutSec 3 -Uri "http://127.0.0.1:$p/app"
        return ($r.Content -match "ClipKontrast")
    } catch { return $false }
}
$Port = 8765
if ($env:CLIPKONTRAST_PORT) { $Port = [int]$env:CLIPKONTRAST_PORT }
for ($p = $Port; $p -lt $Port + 10; $p++) {
    if (Is-ClipKontrast $p) {
        Say "ClipKontrast is already running (in another window). Opening it in your browser." "Green"
        Start-Process "http://127.0.0.1:$p/app"
        exit 0
    }
}
while (-not (Port-Free $Port)) {
    Say "Port $Port is used by another program, trying $($Port + 1)..." "Yellow"
    $Port++
    if ($Port -gt 8800) { Fail "No free port found between 8765 and 8800. Restart the computer and try again." }
}
$env:CLIPKONTRAST_PORT = "$Port"
& $VPy -m studio.server
