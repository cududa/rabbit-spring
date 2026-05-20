param(
    [string]$FreeCadRoot = $env:RABBIT_SPRING_FREECAD_ROOT,
    [string]$VenvPath = ".\.venv"
)

$ErrorActionPreference = "Stop"

function Resolve-RequiredPath {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Required path does not exist: $Path"
    }
    return (Resolve-Path -LiteralPath $Path).Path
}

if (-not $FreeCadRoot) {
    $candidateRoots = @(
        "$env:LOCALAPPDATA\Programs\FreeCAD 1.1",
        "$env:LOCALAPPDATA\Programs\FreeCAD",
        "$env:ProgramFiles\FreeCAD 1.1",
        "$env:ProgramFiles\FreeCAD"
    )
    foreach ($candidate in $candidateRoots) {
        if ($candidate -and (Test-Path -LiteralPath (Join-Path $candidate "bin\FreeCAD.pyd"))) {
            $FreeCadRoot = $candidate
            break
        }
    }
}

if (-not $FreeCadRoot) {
    throw "FreeCAD root was not found. Set RABBIT_SPRING_FREECAD_ROOT or pass -FreeCadRoot."
}

$freeCadRootPath = Resolve-RequiredPath $FreeCadRoot
$freeCadBin = Resolve-RequiredPath (Join-Path $freeCadRootPath "bin")
$freeCadLib = Resolve-RequiredPath (Join-Path $freeCadRootPath "lib")
Resolve-RequiredPath (Join-Path $freeCadBin "FreeCAD.pyd") | Out-Null
Resolve-RequiredPath (Join-Path $freeCadLib "Part.pyd") | Out-Null
Resolve-RequiredPath (Join-Path $freeCadLib "MeshPart.pyd") | Out-Null

$pythonExe = Resolve-RequiredPath (Join-Path $VenvPath "Scripts\python.exe")
$sitePackages = & $pythonExe -c "import site; print(site.getsitepackages()[0])"
if ($LASTEXITCODE -ne 0 -or -not $sitePackages) {
    throw "Could not resolve site-packages for $pythonExe"
}

$pthPath = Join-Path $sitePackages "freecad_local_paths.pth"
$escapedBin = $freeCadBin.Replace("\", "\\")
$escapedLib = $freeCadLib.Replace("\", "\\")
$pth = "import os, sys; paths = [r`"$escapedBin`", r`"$escapedLib`"]; [sys.path.append(path) for path in paths if path not in sys.path]; [os.add_dll_directory(path) for path in paths if hasattr(os, `"add_dll_directory`")]; os.environ[`"PATH`"] = os.pathsep.join(paths + [os.environ.get(`"PATH`", `"`")])"
Set-Content -LiteralPath $pthPath -Value $pth -Encoding UTF8

& $pythonExe -c "import FreeCAD, Part, MeshPart; print(FreeCAD.Version())"
if ($LASTEXITCODE -ne 0) {
    throw "FreeCAD import validation failed"
}

Write-Host "Configured FreeCAD paths for $pythonExe"
