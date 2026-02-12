param(
  [int]$Port = 9090
)

$ErrorActionPreference = "Stop"

function Get-ReadyCondition {
  param([object]$Item)
  if (-not $Item.status -or -not $Item.status.conditions) {
    return [pscustomobject]@{ status = "Unknown"; reason = "NoStatus"; message = "No condition data yet" }
  }
  $ready = $Item.status.conditions | Where-Object { $_.type -eq "Ready" } | Select-Object -First 1
  if (-not $ready) {
    return [pscustomobject]@{ status = "Unknown"; reason = "NoReadyCondition"; message = "Ready condition not found" }
  }
  return [pscustomobject]@{
    status = "$($ready.status)"
    reason = "$($ready.reason)"
    message = "$($ready.message)"
  }
}

function Safe-KubectlJson {
  param(
    [string[]]$Args
  )
  try {
    $raw = & kubectl @Args 2>$null
    if (-not $raw) { return $null }
    return $raw | ConvertFrom-Json
  } catch {
    return $null
  }
}

function Build-StatusPayload {
  $gitRepo = Safe-KubectlJson -Args @("-n", "flux-system", "get", "gitrepository", "nkp-rx-demo", "-o", "json")
  $kustomizations = Safe-KubectlJson -Args @("-n", "flux-system", "get", "kustomizations.kustomize.toolkit.fluxcd.io", "-o", "json")
  $loadgen = Safe-KubectlJson -Args @("-n", "demo-ops", "get", "deploy", "demo-loadgen", "-o", "json")

  $items = @()
  if ($kustomizations -and $kustomizations.items) {
    foreach ($item in $kustomizations.items) {
      $ready = Get-ReadyCondition -Item $item
      $items += [pscustomobject]@{
        name = "$($item.metadata.name)"
        ready = $ready.status
        reason = $ready.reason
        message = $ready.message
        revision = "$($item.status.lastAppliedRevision)"
      }
    }
  }

  $payload = [pscustomobject]@{
    now = (Get-Date).ToString("o")
    gitRepository = [pscustomobject]@{
      branch = if ($gitRepo) { "$($gitRepo.spec.ref.branch)" } else { "unknown" }
      revision = if ($gitRepo -and $gitRepo.status -and $gitRepo.status.artifact) { "$($gitRepo.status.artifact.revision)" } else { "unknown" }
      ready = if ($gitRepo) { (Get-ReadyCondition -Item $gitRepo).status } else { "Unknown" }
    }
    loadgen = [pscustomobject]@{
      desiredReplicas = if ($loadgen -and $loadgen.spec) { [int]$loadgen.spec.replicas } else { -1 }
      readyReplicas = if ($loadgen -and $loadgen.status -and $null -ne $loadgen.status.readyReplicas) { [int]$loadgen.status.readyReplicas } else { 0 }
    }
    kustomizations = $items
  }

  return $payload | ConvertTo-Json -Depth 8 -Compress
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$indexPath = Join-Path $scriptDir "index.html"
if (-not (Test-Path $indexPath)) {
  throw "Cannot find $indexPath"
}

$listener = [System.Net.HttpListener]::new()
$listener.Prefixes.Add("http://localhost:$Port/")
$listener.Start()

Write-Host "Demo wall running at http://localhost:$Port/"
Write-Host "Press Ctrl+C to stop."
Start-Process "http://localhost:$Port/" | Out-Null

try {
  while ($listener.IsListening) {
    $context = $listener.GetContext()
    $requestPath = $context.Request.Url.AbsolutePath
    $response = $context.Response
    $response.Headers.Add("Cache-Control", "no-store")

    if ($requestPath -eq "/" -or $requestPath -eq "/index.html") {
      $bytes = [System.IO.File]::ReadAllBytes($indexPath)
      $response.StatusCode = 200
      $response.ContentType = "text/html; charset=utf-8"
      $response.OutputStream.Write($bytes, 0, $bytes.Length)
      $response.OutputStream.Close()
      continue
    }

    if ($requestPath -eq "/api/status") {
      $json = Build-StatusPayload
      $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
      $response.StatusCode = 200
      $response.ContentType = "application/json; charset=utf-8"
      $response.OutputStream.Write($bytes, 0, $bytes.Length)
      $response.OutputStream.Close()
      continue
    }

    $response.StatusCode = 404
    $notFound = [System.Text.Encoding]::UTF8.GetBytes("Not found")
    $response.OutputStream.Write($notFound, 0, $notFound.Length)
    $response.OutputStream.Close()
  }
} finally {
  if ($listener.IsListening) {
    $listener.Stop()
  }
  $listener.Close()
}
