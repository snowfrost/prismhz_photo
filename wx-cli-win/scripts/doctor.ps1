# wx-cli Windows 环境检查脚本（doctor）
# 用法：以管理员身份打开 PowerShell，执行：
#   powershell -ExecutionPolicy Bypass -File .\doctor.ps1

$ErrorActionPreference = "Continue"
$Pass = 0; $Warn = 0; $Fail = 0

function Ok  ($msg) { Write-Host "  [✓] $msg" -ForegroundColor Green; $script:Pass++ }
function Wn  ($msg) { Write-Host "  [!] $msg" -ForegroundColor Yellow; $script:Warn++ }
function Bad ($msg) { Write-Host "  [✗] $msg" -ForegroundColor Red;   $script:Fail++ }

Write-Host "===== wx-cli Windows 环境检查 =====" -ForegroundColor Cyan

# ── 1. 操作系统 ─────────────────────────────────────
$OS = [Environment]::OSVersion.VersionString
Write-Host "系统：$OS"
if ($env:PROCESSOR_ARCHITECTURE -eq "AMD64") { Ok "64 位系统（需要 x64）" } else { Bad "非 x64 架构，wx-cli 只发布 x64 二进制" }

# ── 2. 是否管理员 ───────────────────────────────────
$IsAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if ($IsAdmin) { Ok "当前以管理员身份运行（wx init 必需）" } else { Wn "当前不是管理员。wx init 需要管理员权限，请右键 PowerShell → 以管理员身份运行" }

# ── 3. wx 是否已安装 ────────────────────────────────
$wxPath = Get-Command wx -ErrorAction SilentlyContinue
$wxDefault = Join-Path $env:LOCALAPPDATA "wx-cli\wx.exe"
if ($wxPath) {
    Ok "wx 已安装：$($wxPath.Source)"
    try { & $wxPath.Source --version 2>$null | ForEach-Object { Write-Host "      版本：$_" -ForegroundColor Green } } catch {}
} elseif (Test-Path $wxDefault) {
    Ok "wx 已安装（默认路径）：$wxDefault"
    & $wxDefault --version 2>$null
} else {
    Bad "wx 未安装。执行 install.ps1 安装：powershell -ExecutionPolicy Bypass -File .\install.ps1"
}

# ── 4. 微信进程是否在运行 ───────────────────────────
$wxProc = Get-Process -Name "Weixin" -ErrorAction SilentlyContinue
if ($wxProc) {
    Ok "微信 Weixin.exe 正在运行（PID: $($wxProc.Id -join ',')）"
} else {
    Bad "微信（Weixin.exe）未在运行。wx-cli 需扫描微信进程内存提取密钥，请先登录微信 4.x 再运行 wx init"
}

# ── 5. 微信数据目录探测 ─────────────────────────────
$WeChatDir = Join-Path $env:APPDATA "Tencent\xwechat_files"
if (Test-Path $WeChatDir) {
    $Dbs = Get-ChildItem $WeChatDir -Recurse -Filter "*.db" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($Dbs) { Ok "检测到微信数据文件（xwechat_files 含 *.db）" } else { Wn "找到 xwechat_files 目录但未见 .db，可能微信尚未产生本地数据（先正常使用微信一段时间）" }
} else {
    Wn "未在 %APPDATA%\Tencent 找到 xwechat_files。若微信装在非默认路径，请先运行 wx init 自动探测，或参照 config.example.json 手动配置"
}

# ── 6. 网络可达性（npm registry，用于安装）──────────
try {
    $R = Invoke-WebRequest -Uri "https://registry.npmjs.org/@jackwener/wx-cli" -Method Head -TimeoutSec 8 -UseBasicParsing
    Ok "网络可达 npm registry（安装源可用）"
} catch {
    Wn "无法访问 npm registry，安装 wx 可能失败（可稍后重试或使用代理）"
}

Write-Host ""
Write-Host "===== 检查结果：通过 $Pass / 警告 $Warn / 失败 $Fail =====" -ForegroundColor Cyan
if ($Fail -gt 0) {
    Write-Host "存在 $Fail 个失败项，按上方提示处理后，重新运行本脚本复查。" -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "环境就绪。开始使用：wx sessions（微信需保持登录运行）" -ForegroundColor Green
}
