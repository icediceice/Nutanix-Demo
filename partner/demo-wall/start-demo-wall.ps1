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
  $virtualService = Safe-KubectlJson -Args @("-n", "demo-app", "get", "virtualservice", "frontend", "-o", "json")
  $gkLabels = Safe-KubectlJson -Args @("get", "k8sdemorequiredlabels.constraints.gatekeeper.sh", "demo-required-labels", "-o", "json")
  $gkResources = Safe-KubectlJson -Args @("get", "k8sdemorequiredresources.constraints.gatekeeper.sh", "demo-required-resources", "-o", "json")
  $gkNoLatest = Safe-KubectlJson -Args @("get", "k8sdemonolatest.constraints.gatekeeper.sh", "demo-no-latest", "-o", "json")

  $items = @()
  $readyCount = 0
  if ($kustomizations -and $kustomizations.items) {
    foreach ($item in $kustomizations.items) {
      $ready = Get-ReadyCondition -Item $item
      if ($ready.status -eq "True") { $readyCount += 1 }
      $items += [pscustomobject]@{
        name = "$($item.metadata.name)"
        ready = $ready.status
        reason = $ready.reason
        message = $ready.message
        revision = "$($item.status.lastAppliedRevision)"
      }
    }
  }

  $kTotal = if ($items.Count -gt 0) { $items.Count } else { 0 }
  $fluxSuccessRate = if ($kTotal -gt 0) { [math]::Round(($readyCount / $kTotal) * 100, 1) } else { 0.0 }
  $fluxStatus = if ($fluxSuccessRate -ge 90) { "good" } elseif ($fluxSuccessRate -ge 70) { "warn" } else { "bad" }

  $weightV1 = 0
  $weightV2 = 0
  if ($virtualService -and $virtualService.spec -and $virtualService.spec.http -and $virtualService.spec.http.Count -gt 0) {
    $routes = $virtualService.spec.http[0].route
    foreach ($r in $routes) {
      if ($r.destination.subset -eq "v1") { $weightV1 = [int]$r.weight }
      if ($r.destination.subset -eq "v2") { $weightV2 = [int]$r.weight }
    }
  }

  $constraints = @($gkLabels, $gkResources, $gkNoLatest)
  $pass = 0
  $warn = 0
  $fail = 0
  $error = 0
  $policyTotal = 0
  foreach ($c in $constraints) {
    if (-not $c) { continue }
    $policyTotal += 1
    $violations = [int]$(if ($c.status -and $null -ne $c.status.totalViolations) { $c.status.totalViolations } else { 0 })
    if ($violations -gt 0) {
      $warn += $violations
    } else {
      $pass += 1
    }
  }
  $policyCompliance = if ($policyTotal -gt 0) { [math]::Round(($pass / $policyTotal) * 100, 1) } else { 100.0 }
  $policyStatus = if ($policyCompliance -ge 95) { "good" } elseif ($policyCompliance -ge 60) { "warn" } else { "bad" }

  $desired = if ($loadgen -and $loadgen.spec) { [int]$loadgen.spec.replicas } else { -1 }
  $loadProfile = if ($desired -le 0) { "off" } elseif ($desired -ge 1) { "active" } else { "unknown" }

  $payload = [pscustomobject]@{
    now = (Get-Date).ToString("o")
    gitRepository = [pscustomobject]@{
      branch = if ($gitRepo) { "$($gitRepo.spec.ref.branch)" } else { "unknown" }
      revision = if ($gitRepo -and $gitRepo.status -and $gitRepo.status.artifact) { "$($gitRepo.status.artifact.revision)" } else { "unknown" }
      ready = if ($gitRepo) { (Get-ReadyCondition -Item $gitRepo).status } else { "Unknown" }
    }
    loadgen = [pscustomobject]@{
      desiredReplicas = $desired
      readyReplicas = if ($loadgen -and $loadgen.status -and $null -ne $loadgen.status.readyReplicas) { [int]$loadgen.status.readyReplicas } else { 0 }
      profile = $loadProfile
    }
    canary = [pscustomobject]@{
      v1 = $weightV1
      v2 = $weightV2
    }
    policy = [pscustomobject]@{
      pass = $pass
      warn = $warn
      fail = $fail
      error = $error
      compliance = $policyCompliance
      status = $policyStatus
    }
    kpi = @(
      [pscustomobject]@{
        name = "Flux Success Rate"
        value = "$fluxSuccessRate%"
        status = $fluxStatus
        threshold = ">= 90%"
      },
      [pscustomobject]@{
        name = "Canary Weight v2"
        value = "$weightV2%"
        status = "good"
        threshold = "informational"
      },
      [pscustomobject]@{
        name = "Policy Compliance"
        value = "$policyCompliance%"
        status = $policyStatus
        threshold = ">= 95%"
      },
      [pscustomobject]@{
        name = "Rollback SLA Target"
        value = "< 3 minutes"
        status = "good"
        threshold = "target"
      }
    )
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
