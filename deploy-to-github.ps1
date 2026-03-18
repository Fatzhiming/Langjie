# GitHub 部署脚本

param(
    [string]$CommitMessage = "🦞 龙虾工作流 - 自动提交量化交易项目代码",
    [switch]$Initialize
)

$projectDir = "E:\Langjie\King\projects\quant-btcusdt"
cd $projectDir

Write-Host "🦞 准备推送到 GitHub..." -ForegroundColor Cyan
Write-Host "📂 项目目录：$projectDir" -ForegroundColor Gray

# 检查 Git 是否初始化
if ($Initialize -or -not (Test-Path ".git")) {
    Write-Host "📦 初始化 Git 仓库..." -ForegroundColor Yellow
    git init
    git branch -M main
    
    # 创建 .gitignore
    $gitignore = @"
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
*.egg-info/
dist/
build/

# 日志
logs/*.log
*.log

# 配置（敏感信息）
config.local.yaml
.env

# IDE
.vscode/
.idea/
*.swp
*.swo

# 测试
.pytest_cache/
.coverage
htmlcov/

# 临时文件
*.tmp
*.bak
"@
    $gitignore | Out-File -FilePath ".gitignore" -Encoding utf8
    Write-Host "✅ .gitignore 已创建" -ForegroundColor Green
}

# 添加所有文件
Write-Host "📝 添加文件到 Git..." -ForegroundColor Yellow
git add -A

# 检查是否有变更
$status = git status --porcelain
if ($status) {
    # 提交
    Write-Host "💾 提交变更..." -ForegroundColor Yellow
    git commit -m $CommitMessage
    
    # 推送到 GitHub
    Write-Host "🚀 推送到 GitHub..." -ForegroundColor Yellow
    git push -u origin main
    
    Write-Host "✅ 推送成功！" -ForegroundColor Green
    Write-Host "📍 仓库：https://github.com/your-username/$((Get-Item $projectDir).Name)" -ForegroundColor Cyan
} else {
    Write-Host "✅ 没有变更，无需提交" -ForegroundColor Green
}

Write-Host ""
Write-Host "📊 Git 状态:" -ForegroundColor Cyan
git status --short
