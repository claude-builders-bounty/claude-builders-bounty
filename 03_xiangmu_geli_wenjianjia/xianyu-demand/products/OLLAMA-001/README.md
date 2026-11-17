# Ollama 本地部署大模型 - 使用指南

## 产品概述
本产品提供 Ollama 本地大模型一键部署方案，包含自动化部署脚本、常用模型下载脚本、Web UI 部署方案、完整文档和远程协助支持。

## 快速开始

### 方式一：一键部署脚本（推荐，最简单）
1. 解压下载的压缩包
2. 右键点击 deploy_ollama.bat 选择 "以管理员身份运行"
3. 等待自动完成（约 10-30 分钟，视网速和硬件而定）
4. 完成后访问 http://localhost:11434 测试，或打开 http://localhost:3000 使用 Web UI

### 方式二：手动部署（适合已有环境或需自定义）
参考 docs/deployment-guide.md 详细文档。

## 目录结构
OLLAMA-001/
  deploy_ollama.bat          # 一键部署脚本（Windows）
  deploy_ollama.sh           # Linux/macOS 部署脚本
  scripts/
    download_models.py       # 模型批量下载脚本（断点续传/校验）
    check_gpu.py             # GPU/显存检测与模型推荐
    backup_config.py         # 配置备份/迁移脚本
  docs/
    deployment-guide.md      # 详细部署指南
    troubleshooting.md       # 常见问题与解决方案
    model-recommendations.md # 硬件配置对应模型推荐
    api-reference.md         # Ollama API 参考
  models/
    recommended_models.txt   # 推荐模型列表与下载命令
  assets/
    cover.png                # 封面图
    demo.mp4                 # 演示视频

## 硬件配置建议

| 场景 | 显存/内存 | 推荐模型 | 预估速度 |
|---|---|---|---|
| 入门体验 | CPU only / 8GB+ RAM | qwen2.5:1.5b / 3b | ~10-30 tok/s |
| 日常开发 | 8GB VRAM | qwen2.5:7b / llama3.1:8b | 20-50 tok/s |
| 专业开发 | 16GB VRAM | qwen2.5:14b / llama3.1:8b / codellama:7b | 15-40 tok/s |
| 重度推理 | 24GB+ VRAM | qwen2.5:32b / llama3.1:70b (量化) | 10-25 tok/s |
| 仅CPU/内存大 | 32GB+ RAM | qwen2.5:14b/32b (gguf量化) | 5-15 tok/s |

## 常用命令速查表

ollama list                    # 查看已安装模型
ollama pull qwen2.5:7b         # 下载模型
ollama pull qwen2.5:14b        # 下载大模型
ollama pull codellama:7b       # 代码模型
ollama pull nomic-embed-text   # 嵌入模型
ollama rm qwen2.5:7b           # 删除模型
ollama run qwen2.5:7b          # 运行交互
ollama serve                   # 启动服务（后台运行）

# API 调用示例
curl http://localhost:11434/api/generate -d '{
  "model": "qwen2.5:7b",
  "prompt": "你好，请用中文介绍一下你自己",
  "stream": false
}'

文件位置：
Windows: %USERPROFILE%\.ollama
Linux/Mac: ~/.ollama
模型存储: ~/.ollama/models
配置文件: ~/.ollama/config.yaml

## 常见问题快速解决

| 问题 | 解决方案 |
|---|---|
| ollama 命令未找到 | 重启终端/重启电脑，或将 ollama 添加到 PATH |
| 显存不足 (CUDA OOM) | 使用更小模型，或添加 OLLAMA_NUM_GPU_LAYERS=0 强制 CPU 推理 |
| 下载慢/失败 | 设置镜像源: OLLAMA_MODELS=D:\models + 使用镜像源 |
| 端口冲突 (11434) | 修改配置: OLLAMA_HOST=0.0.0.0:11435 |
| 显存不足 (CUDA OOM) | 使用量化模型 (q4_k_m, q4_k_s) 或 OLLAMA_NUM_GPU_LAYERS=0 强制 CPU |

## 售后支持

- 远程协助：购买后提供 1 次远程协助部署 (TeamViewer/ToDesk/向日葵，约 30-60 分钟)
- 答疑周期：购买后 30 天内免费答疑
- 联系方式：闲鱼私聊 / 订单留言
- 响应时间：工作日 10:00-22:00，通常 1 小时内回复

## 免责声明

1. 本产品基于开源软件 Ollama (Apache 2.0) 及各模型官方许可证，仅提供部署整合与技术支持
2. 模型版权归各模型发布方所有，请遵守各模型许可证 (Apache 2.0 / MIT / Llama 3 License 等)
3. 禁止将部署包用于违法用途，使用者需自行承担法律责任
4. 远程协助仅限 1 次/单，额外需求需另行协商
