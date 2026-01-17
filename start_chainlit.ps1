# RAG Agent Chainlit 启动脚本
# 功能：等待后台完全启动后再打开浏览器窗口

param(
    [int]$Port = 8000,
    [switch]$Headless = $false
)

$ErrorActionPreference = "Stop"

# 获取脚本所在目录
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# 检查是否安装了poetry
if (-not (Get-Command poetry -ErrorAction SilentlyContinue)) {
    Write-Host "❌ 错误: 未找到 poetry 命令" -ForegroundColor Red
    Write-Host "   请先安装 poetry: https://python-poetry.org/docs/#installation" -ForegroundColor Yellow
    exit 1
}

# 检查chainlit_app.py是否存在
$ChainlitApp = "app\interfaces\web\chainlit_app.py"
if (-not (Test-Path $ChainlitApp)) {
    Write-Host "❌ 错误: 未找到 chainlit_app.py: $ChainlitApp" -ForegroundColor Red
    exit 1
}

# 设置日志文件路径
$ErrorLogFile = "logs\chainlit_startup_error.log"
$RagAgentLogFile = "logs\rag_agent.log"
$LogDir = "logs"
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

Write-Host ""
Write-Host "══════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "                                                              " -ForegroundColor Green
Write-Host "        🚀 启动 RAG Agent Chainlit Web 应用 🚀                " -ForegroundColor Green
Write-Host "                                                              " -ForegroundColor Green
Write-Host "══════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""

# 设置端口环境变量
$env:CHAINLIT_PORT = $Port

# 启动Chainlit（headless模式，不自动打开浏览器）
Write-Host "📡 正在启动 Chainlit 服务器（端口: $Port）..." -ForegroundColor Yellow
Write-Host "📝 应用日志: $RagAgentLogFile" -ForegroundColor Yellow

# 启动Chainlit进程（使用headless模式）
# 重定向标准输出和标准错误到文件，避免混入脚本输出
$StdOutFile = "$LogDir\chainlit_stdout.log"
$ChainlitProcess = Start-Process -FilePath "poetry" `
    -ArgumentList "run", "chainlit", "run", $ChainlitApp, "--port", $Port, "--headless" `
    -NoNewWindow -PassThru -RedirectStandardOutput $StdOutFile -RedirectStandardError $ErrorLogFile

if (-not $ChainlitProcess) {
    Write-Host "❌ 错误: 无法启动 Chainlit 进程" -ForegroundColor Red
    exit 1
}

# 监控启动状态的关键词
$ReadyKeywords = @(
    "RAG Agent 初始化完成",
    "RAG Agent 启动完成",
    "步骤 5/5: RAG Agent 初始化完成",
    "服务已就绪",
    "Running on",
    "Uvicorn running on",
    "Application startup complete",
    "Started server process",
    "Waiting for application startup"
)

# Banner 已在 PowerShell 脚本中显示，不再从日志中检测

$ErrorKeywords = @(
    "初始化 RAG Agent 失败",
    "启动失败",
    "Error:",
    "Exception:"
)

$MaxWaitTime = 120  # 最多等待120秒
$StartTime = Get-Date
$Ready = $false

# 实时显示日志并监控启动状态
while (-not $Ready -and ((Get-Date) - $StartTime).TotalSeconds -lt $MaxWaitTime) {
    Start-Sleep -Milliseconds 500
    
    # 检查端口是否可访问（使用TCP连接，完全静默）
    try {
        $TcpClient = New-Object System.Net.Sockets.TcpClient
        $Connection = $TcpClient.BeginConnect("localhost", $Port, $null, $null)
        $Wait = $Connection.AsyncWaitHandle.WaitOne(300, $false)  # 300ms超时
        $PortOpen = $false
        if ($Wait) {
            try {
                $TcpClient.EndConnect($Connection)
                $PortOpen = $true
                $TcpClient.Close()
            } catch {
                $PortOpen = $false
            }
        } else {
            $TcpClient.Close()
        }
        
        if ($PortOpen -and -not $Ready) {
            # 端口可访问，再检查应用日志确认初始化完成
            if (Test-Path $RagAgentLogFile) {
                $RagLogContent = Get-Content $RagAgentLogFile -Tail 30 -ErrorAction SilentlyContinue
                if ($RagLogContent) {
                    foreach ($line in $RagLogContent) {
                        # 检查多种可能的初始化完成标志
                        if ($line -match "步骤 5/5.*RAG Agent 初始化完成" -or 
                            $line -match "RAG Agent 初始化完成" -or
                            $line -match "问答链创建完成" -or
                            $line -match "✅.*步骤 5/5") {
                            $Ready = $true
                            break
                        }
                    }
                }
            }
            # 如果端口可访问且等待超过20秒，即使没找到初始化日志也认为服务已就绪
            $Elapsed = ((Get-Date) - $StartTime).TotalSeconds
            if (-not $Ready -and $Elapsed -gt 20) {
                $Ready = $true
            }
        }
    } catch {
        # 端口未就绪，继续等待（静默忽略错误）
    }
    
    # 检查应用日志（rag_agent.log）和错误日志
    $LogContent = @()
    
    # 读取应用日志（主要日志来源）
    if (Test-Path $RagAgentLogFile) {
        $RagLogContent = Get-Content $RagAgentLogFile -Tail 30 -ErrorAction SilentlyContinue
        if ($RagLogContent) {
            $LogContent = @($LogContent) + @($RagLogContent)
        }
    }
    
    # 读取错误日志（如果有）
    if (Test-Path $ErrorLogFile) {
        $ErrorContent = Get-Content $ErrorLogFile -Tail 20 -ErrorAction SilentlyContinue
        if ($ErrorContent) {
            $LogContent = @($LogContent) + @($ErrorContent)
        }
    }
    
    if ($LogContent) {
        # 检查是否就绪
        foreach ($line in $LogContent) {
            # 首先检查rag_agent.log中的特定格式
            if ($line -match "步骤 5/5.*RAG Agent 初始化完成" -or 
                $line -match "✅.*步骤 5/5" -or
                $line -match "问答链创建完成") {
                if (-not $Ready) {
                    Write-Host ""
                    Write-Host "✅ 检测到服务就绪标志（从应用日志）" -ForegroundColor Green
                    $Ready = $true
                    break
                }
            }
            
            # 然后检查其他关键词
            foreach ($keyword in $ReadyKeywords) {
                if ($line -match [regex]::Escape($keyword)) {
                    if (-not $Ready) {
                        Write-Host ""
                        Write-Host "✅ 检测到服务就绪标志: $keyword" -ForegroundColor Green
                        $Ready = $true
                        break
                    }
                }
            }
            if ($Ready) { break }
        }
        
        # 检查是否有错误
        foreach ($line in $LogContent) {
            foreach ($keyword in $ErrorKeywords) {
                if ($line -match [regex]::Escape($keyword)) {
                    Write-Host ""
                    Write-Host "❌ 检测到错误: $line" -ForegroundColor Red
                    Write-Host "   请查看日志文件获取详细信息: $RagAgentLogFile" -ForegroundColor Yellow
                    # 不退出，继续等待，可能只是警告
                }
            }
        }
    }
    
    # 检查进程是否还在运行
    if ($ChainlitProcess.HasExited) {
        Write-Host ""
        Write-Host "❌ Chainlit 进程意外退出（退出代码: $($ChainlitProcess.ExitCode)）" -ForegroundColor Red
        Write-Host "   请查看日志文件: $RagAgentLogFile" -ForegroundColor Yellow
        if (Test-Path $ErrorLogFile) {
            Write-Host "   错误日志: $ErrorLogFile" -ForegroundColor Yellow
        }
        exit 1
    }
    
    # 显示等待动画（避免重复显示）
    if (-not $Ready) {
        $Elapsed = [int]((Get-Date) - $StartTime).TotalSeconds
        if ($Elapsed % 2 -eq 0) {
            # 使用回车符覆盖上一行，避免重复
            $Spaces = " " * 50  # 清除上一行的内容
            Write-Host "`r$Spaces`r⏳ 等待中... ($Elapsed 秒)" -ForegroundColor Yellow -NoNewline
        }
    }
}

# 清除等待动画的最后一行
Write-Host ""

if ($Ready) {
    Write-Host ""
    Write-Host "══════════════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host "                                                              " -ForegroundColor Green
    Write-Host "          🚀 RAG Agent - Chainlit Web 应用已就绪 🚀           " -ForegroundColor Green
    Write-Host "                                                              " -ForegroundColor Green
    Write-Host "  ✅ 后端服务已完全启动                                        " -ForegroundColor Green
    Write-Host "  ✅ RAG Agent 已初始化完成                                    " -ForegroundColor Green
    Write-Host "  ✅ 向量存储已加载                                            " -ForegroundColor Green
    Write-Host "  ✅ 问答链已创建                                              " -ForegroundColor Green
    Write-Host "                                                              " -ForegroundColor Green
    Write-Host "  现在可以安全地打开浏览器窗口了！                               " -ForegroundColor Green
    Write-Host "  http://localhost:$Port                                      " -ForegroundColor Green
    Write-Host "  按 Ctrl+C 停止服务                                           " -ForegroundColor Green
    Write-Host "══════════════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host ""
    Write-Host ""
    
    # 等待一小段时间确保服务完全就绪
    Start-Sleep -Seconds 1
    
    # 等待进程结束
    try {
        $ChainlitProcess.WaitForExit()
    } catch {
        Write-Host ""
        Write-Host "服务已停止" -ForegroundColor Yellow
    }
} else {
    Write-Host ""
    Write-Host "⚠️  警告: 在 $MaxWaitTime 秒内未检测到就绪标志" -ForegroundColor Yellow
    Write-Host "   但服务可能已经启动，正在打开浏览器..." -ForegroundColor Yellow
    Write-Host ""
    
    # 即使没检测到就绪标志，也尝试打开浏览器
    $Url = "http://localhost:$Port"
    Start-Process $Url
    
    Write-Host "   访问地址: $Url" -ForegroundColor Cyan
    Write-Host "   如果页面无法访问，请查看日志: $RagAgentLogFile" -ForegroundColor Yellow
    if (Test-Path $ErrorLogFile) {
        Write-Host "   错误日志: $ErrorLogFile" -ForegroundColor Yellow
    }
    Write-Host ""
    
    # 等待进程结束
    try {
        $ChainlitProcess.WaitForExit()
    } catch {
        Write-Host ""
        Write-Host "服务已停止" -ForegroundColor Yellow
    }
}
