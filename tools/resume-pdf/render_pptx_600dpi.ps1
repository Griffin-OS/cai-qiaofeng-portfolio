param(
  [Parameter(Mandatory = $true)][string]$SourcePath,
  [Parameter(Mandatory = $true)][string]$OutputPath,
  [ValidateRange(72, 1200)][int]$Dpi = 600
)

$ErrorActionPreference = 'Stop'
$source = (Resolve-Path -LiteralPath $SourcePath).Path
$output = [System.IO.Path]::GetFullPath($OutputPath)
$outputDirectory = Split-Path -Parent $output
New-Item -ItemType Directory -Force -Path $outputDirectory | Out-Null

$powerPoint = $null
$presentation = $null
try {
  $powerPoint = New-Object -ComObject PowerPoint.Application
  $presentation = $powerPoint.Presentations.Open($source, $true, $false, $false)
  $slide = $presentation.Slides.Item(1)
  # Render using the source slide's own aspect ratio, so its native layout stays intact.
  $width = [Math]::Round(($presentation.PageSetup.SlideWidth / 72) * $Dpi)
  $height = [Math]::Round(($presentation.PageSetup.SlideHeight / 72) * $Dpi)
  $slide.Export($output, 'PNG', $width, $height)
  if (-not (Test-Path -LiteralPath $output)) { throw 'PowerPoint did not create the PNG.' }
  Get-Item -LiteralPath $output | Select-Object FullName, Length, LastWriteTime
}
finally {
  if ($presentation -ne $null) { $presentation.Close() }
  if ($powerPoint -ne $null) { $powerPoint.Quit() }
  if ($presentation -ne $null) { [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($presentation) }
  if ($powerPoint -ne $null) { [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($powerPoint) }
  [GC]::Collect()
  [GC]::WaitForPendingFinalizers()
}
