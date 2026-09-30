# wx-cli Windows 一键安装脚本
# 用法：以管理员身份打开 PowerShell，执行：
#   powershell -ExecutionPolicy Bypass -File .\install.ps1
# 或直接：右键本文件 → 使用 PowerShell 运行
#
# 说明：wx-cli 官方 GitHub 仓库已下线（微信 DMCA），本脚本改为从 npm registry
#       直接获取 Windows 二进制，不依赖 GitHub，稳定可用。

$ErrorActionPreference = "Stop"

$BinName   = "wx.exe"
$Version   = "0.3.0"
$InstallDir = Join-Path $env:LOCALAPPDATA "wx-cli"
$Tarball   = "https://registry.npmjs.org/@jackwener/wx-cli-win32-x64/-/wx-cli-win32-x64-$Version.tgz"

Write-Host "======================================" -ForegroundColor Cyan
Write-Host " wx-cli v$Version  Windows 安装器" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

# ── 0. 检测是否已安装 ────────────────────────────────
$Existing = Join-Path $InstallDir $BinName
if (Test-Path $Existing) {
    Write-Host "检测到已安装版本："
    & $Existing --version 2>$null
    Write-Host ""
}

# ── 1. 下载 npm tarball（内含 wx.exe）────────────────
Write-Host "下载中：$Tarball" -ForegroundColor Yellow
$TmpTar = Join-Path $env:TEMP "wx-cli-$Version.tgz"
Invoke-WebRequest -Uri $Tarball -OutFile $TmpTar -UseBasicParsing

# ── 2. 解压（Windows 10+ 自带 tar，支持 tgz）─────────
$ExtractDir = Join-Path $env:TEMP "wx-cli-extract"
if (Test-Path $ExtractDir) { Remove-Item -Recurse -Force $ExtractDir }
New-Item -ItemType Directory -Path $ExtractDir | Out-Null
tar -xzf $TmpTar -C $ExtractDir
if ($LASTEXITCODE -ne 0) { Write-Error "解压失败，请检查网络后重试"; exit 1 }

# ── 3. 复制 wx.exe 到安装目录 ────────────────────────
$SrcExe = Join-Path $ExtractDir "package\bin\$BinName"
if (-not (Test-Path $SrcExe)) { Write-Error "压缩包内未找到 wx.exe"; exit 1 }
if (-not (Test-Path $InstallDir)) { New-Item -ItemType Directory -Path $InstallDir | Out-Null }
Copy-Item -Force $SrcExe (Join-Path $InstallDir $BinName)

# ── 4. 加入用户 PATH ─────────────────────────────────
$UserPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($UserPath -notlike "*$InstallDir*") {
    [Environment]::SetEnvironmentVariable("PATH", "$UserPath;$InstallDir", "User")
    Write-Host "已将 $InstallDir 加入用户 PATH（新开终端生效）" -ForegroundColor Green
}

Write-Host ""
Write-Host "✓ 安装完成：$InstallDir\$BinName" -ForegroundColor Green
& (Join-Path $InstallDir $BinName) --version
Write-Host ""
Write-Host "下一步（以管理员身份，且微信 4.x 正在登录运行）：" -ForegroundColor Cyan
Write-Host "  1. wx init        # 首次初始化，扫描微信进程提取解密密钥"
Write-Host "  2. wx sessions    # 查看最近会话"
Write-Host "  3. wx --help      # 全部命令"
Write-Host "当前终端 PATH 未刷新，请新开一个终端再执行 wx 命令。"
