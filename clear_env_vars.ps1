# 清理 BUFFOTTE 环境变量脚本
# 这个脚本会删除所有 BUFFOTTE 相关的环境变量
# 让邮件发送功能使用 email_config.json 配置文件

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  清理 BUFFOTTE 环境变量" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 获取所有 BUFFOTTE 环境变量
$buffotteVars = Get-ChildItem Env: | Where-Object { $_.Name -like "BUFFOTTE*" }

if ($buffotteVars.Count -eq 0) {
    Write-Host "✓ 未找到 BUFFOTTE 环境变量" -ForegroundColor Green
    Write-Host ""
    exit 0
}

Write-Host "找到以下 BUFFOTTE 环境变量:" -ForegroundColor Yellow
Write-Host ""
foreach ($var in $buffotteVars) {
    Write-Host "  - $($var.Name) = $($var.Value)"
}
Write-Host ""

$confirmation = Read-Host "是否删除这些环境变量? (y/N)"

if ($confirmation -eq 'y' -or $confirmation -eq 'Y') {
    Write-Host ""
    Write-Host "正在删除环境变量..." -ForegroundColor Yellow
    
    foreach ($var in $buffotteVars) {
        Remove-Item "Env:$($var.Name)" -ErrorAction SilentlyContinue
        Write-Host "  ✓ 已删除: $($var.Name)" -ForegroundColor Green
    }
    
    Write-Host ""
    Write-Host "✓ 所有环境变量已清理完毕!" -ForegroundColor Green
    Write-Host ""
    Write-Host "现在邮件发送功能将使用 email_config.json 配置文件" -ForegroundColor Cyan
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "已取消操作" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
