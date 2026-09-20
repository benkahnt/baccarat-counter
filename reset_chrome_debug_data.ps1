param([ValidateSet('normal','simulator')][string]$Mode = 'normal')
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-DebugProfilePath([string]$LocalDataRoot) {
    if ([string]::IsNullOrWhiteSpace($LocalDataRoot) -or -not [IO.Path]::IsPathRooted($LocalDataRoot)) {
        throw 'LocalAppData ist kein absoluter Pfad.'
    }
    $base = [IO.Path]::GetFullPath($LocalDataRoot).TrimEnd('\')
    $profile = [IO.Path]::GetFullPath((Join-Path $base 'BaccaratCounterChrome'))
    if ([IO.Path]::GetDirectoryName($profile) -ne $base -or [IO.Path]::GetFileName($profile) -ne 'BaccaratCounterChrome') {
        throw 'Ungueltiger Debug-Profilpfad.'
    }
    return $profile
}

function Assert-NoProfileLink([string]$Path) {
    $cursor = [IO.Path]::GetFullPath($Path)
    while ($cursor) {
        if (Test-Path -LiteralPath $cursor) {
            $entry = Get-Item -LiteralPath $cursor -Force
            if ($entry.Attributes -band [IO.FileAttributes]::ReparsePoint) {
                throw "Profilbereinigung verweigert: Verknuepfung im Pfad $cursor"
            }
        }
        $parent = [IO.Path]::GetDirectoryName($cursor)
        if ($parent -eq $cursor) { break }
        $cursor = $parent
    }
}

function Test-DebugProfileRunning([string]$ProfilePath) {
    foreach ($process in @(Get-CimInstance Win32_Process -Filter "Name = 'chrome.exe'" -ErrorAction Stop)) {
        if (-not $process.CommandLine) { continue }
        $m = [regex]::Match($process.CommandLine, '(?i)(?:^|\s)--user-data-dir(?:=|\s+)(?:"([^"]+)"|([^\s"]+))')
        if (-not $m.Success) { continue }
        $value = if ($m.Groups[1].Success) { $m.Groups[1].Value } else { $m.Groups[2].Value }
        if ([IO.Path]::GetFullPath($value).TrimEnd('\') -eq $ProfilePath.TrimEnd('\')) { return $true }
    }
    return $false
}

function Get-DebugDataTargets([string]$ProfilePath) {
    Assert-NoProfileLink $ProfilePath
    if (-not (Test-Path -LiteralPath $ProfilePath)) { return }
    $rootCaches = @('ShaderCache','GrShaderCache','GraphiteDawnCache','GPUPersistentCache','DawnCache','component_crx_cache','extensions_crx_cache')
    $profileData = @('Cache','Code Cache','GPUCache','DawnGraphiteCache','DawnWebGPUCache','Media Cache',
        'Local Storage','Session Storage','IndexedDB','Service Worker','Storage','WebStorage','File System',
        'blob_storage','Shared Dictionary','Network\Shared Dictionary','Network\Cache')
    foreach ($cookie in @('Cookies','Network\Cookies')) {
        foreach ($suffix in @('','-journal','-wal','-shm')) { $profileData += $cookie + $suffix }
    }
    $candidates = @($rootCaches | ForEach-Object { Join-Path $ProfilePath $_ })
    foreach ($folder in @(Get-ChildItem -LiteralPath $ProfilePath -Directory -Force)) {
        if ($folder.Name -match '^(Default|Profile \d+|Guest Profile|System Profile)$') {
            Assert-NoProfileLink $folder.FullName
            $candidates += @($profileData | ForEach-Object { Join-Path $folder.FullName $_ })
        }
    }
    foreach ($candidate in $candidates) {
        $absolute = [IO.Path]::GetFullPath($candidate)
        if (-not $absolute.StartsWith($ProfilePath.TrimEnd('\')+'\', [StringComparison]::OrdinalIgnoreCase)) {
            throw 'Loeschziel liegt ausserhalb des Debug-Profils.'
        }
        if (Test-Path -LiteralPath $absolute) {
            Assert-NoProfileLink $absolute
            # Walk without following junctions. Validate all entries before deleting any target.
            $queue = New-Object 'System.Collections.Generic.Queue[string]'
            $queue.Enqueue($absolute)
            while ($queue.Count) {
                $entry = Get-Item -LiteralPath $queue.Dequeue() -Force
                if ($entry.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Verknuepfung im Loeschziel: $($entry.FullName)" }
                if ($entry.PSIsContainer) {
                    foreach ($child in @(Get-ChildItem -LiteralPath $entry.FullName -Force)) { $queue.Enqueue($child.FullName) }
                }
            }
            $absolute
        }
    }
}

function Reset-DebugSiteData([string]$LocalDataRoot, [string]$StartMode = 'normal') {
    $profile = Get-DebugProfilePath $LocalDataRoot
    Assert-NoProfileLink $profile
    if (Test-DebugProfileRunning $profile) {
        if ($StartMode -eq 'simulator') {
            Write-Output 'Simulator-Tab in bestehender Debug-Sitzung: keine neue Browser-Sitzung.'
            return
        }
        throw 'Debug-Chrome ist noch offen. Bitte alle Fenster dieses Debug-Browsers schliessen und erneut starten. Es wurden keine Daten geloescht.'
    }
    $targets = @(Get-DebugDataTargets $profile)
    foreach ($target in $targets) {
        # Revalidate immediately before the native PowerShell deletion.
        if (-not $target.StartsWith($profile+'\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Ungueltiges Loeschziel.' }
        Assert-NoProfileLink $target
        Remove-Item -LiteralPath $target -Recurse -Force -ErrorAction Stop
        if (Test-Path -LiteralPath $target) { throw "Bereinigung unvollstaendig: $target" }
    }
    Write-Output "Debug-Profil: Cache, Cookies und Website-Speicher bereinigt ($($targets.Count) Bereiche). Neuer Login erforderlich."
}

if ($MyInvocation.InvocationName -ne '.') {
    try { Reset-DebugSiteData $env:LOCALAPPDATA $Mode; exit 0 }
    catch { Write-Host ('DEBUG-CHROME NICHT GESTARTET: '+$_.Exception.Message) -ForegroundColor Red; exit 1 }
}
