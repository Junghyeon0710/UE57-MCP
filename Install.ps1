param(
    [string]$Project,
    [string]$Engine57,
    [string]$WorkDir = (Join-Path $env:LOCALAPPDATA 'UE57MCP/5.7.4'),
    [int]$Port = 8000
)
$ErrorActionPreference = 'Stop'
try {
    # 런처가 등록한 5.7 설치 경로를 찾으며 사용자 지정 경로가 있으면 우선한다.
    if (-not $Engine57) {
        $record = Get-ItemProperty -LiteralPath 'HKLM:\SOFTWARE\EpicGames\Unreal Engine\5.7' -ErrorAction SilentlyContinue
        if ($record) { $Engine57 = $record.InstalledDirectory }
    }
    if (-not $Engine57) { throw 'UE 5.7 was not found. Run Install.ps1 -Engine57 <engine folder> -Project <project.uproject>.' }
    if (-not $Project) {
        Add-Type -AssemblyName System.Windows.Forms
        $picker = New-Object System.Windows.Forms.OpenFileDialog
        $picker.Title = 'Select the UE 5.7 project that will receive the full MCP backport'
        $picker.Filter = 'Unreal project (*.uproject)|*.uproject'
        if ($picker.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) { exit 1 }
        $Project = $picker.FileName
        $picker.Dispose()
    }
    $python = Join-Path $Engine57 'Engine/Binaries/ThirdParty/Python3/Win64/python.exe'
    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'UE 5.7 bundled Python was not found.' }
    Get-Command git -ErrorAction Stop | Out-Null
    Write-Host 'Installing the full UE 5.8 MCP backport for UE 5.7.4.'
    Write-Host 'Requires Epic-linked GitHub access and Visual Studio C++ build tools. Close the target editor first.'
    & $python -X utf8 (Join-Path $PSScriptRoot 'scripts/full_port.py') --engine57 $Engine57 --work-dir $WorkDir --project $Project --port $Port
    if ($LASTEXITCODE -ne 0) { throw 'Installation failed. Review the error above; no reduced MCP was installed.' }
    Write-Host "Installation complete. Open your project, then connect your MCP client to http://127.0.0.1:$Port/mcp"
} catch {
    Write-Error $_
    exit 1
}
