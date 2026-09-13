# 试错记录

> 现象 → 原因 → 处理 → 预防。小坑也记，不扩写成虚假「核心贡献」。

## 2026-07-23

### T-001：Cursor create_project 在本机初始化 git 失败

- **现象**：MCP `create_project` 报 `spawn /bin/sh ENOENT`
- **原因**：Windows 环境对该 MCP 的 shell 假设不兼容
- **处理**：目录已手工创建；本地执行 `git init` 成功
- **预防**：本机优先用 PowerShell/`git` 初始化；MCP 失败不阻塞立项

### T-002：C-MAPSS 下载渠道选择

- **现象**：NASA 门户下载链路不稳定/不便脚本化
- **原因**：门户页面偏交互；直接 zip 链接更适合自动化
- **处理**：使用 Zenodo `CMAPSSData.zip`（progpy 同源引用），校验行数与 unit 数
- **预防**：`data/README.md` 同时写官方口径 + 镜像 URL；下载后必做行数校验

### T-004：本机无 CMake/C++ 编译器

- **现象**：`cmake` / `g++` / `cl` 均不在 PATH
- **原因**：干净 Windows 环境未装工具链
- **处理**：`winget install BrechtSanders.WinLibs.POSIX.UCRT`（含 g++ 与 cmake）
- **预防**：在 `cpp_inference/README.md` 写明依赖；G4 文档记录

### T-005：torch.onnx dynamo 路径在 GBK 控制台崩溃

- **现象**：`UnicodeEncodeError: 'gbk' codec can't encode character '\u2705'`
- **原因**：新 exporter 打印 emoji；Windows 默认 GBK
- **处理**：`dynamo=False` 走 legacy exporter；并设 `PYTHONIOENCODING=utf-8`
- **预防**：导出脚本固定 legacy 参数直至上游稳定

### T-006：MinGW 无法直接链接 MSVC 的 `onnxruntime.lib`

- **现象**：官方包提供 MSVC import lib
- **处理**：`gendef onnxruntime.dll` + `dlltool` 生成 `libonnxruntime.a`（导出 `OrtGetApiBase` 等）
- **预防**：构建说明写入 `cpp_inference/README.md`

### T-003：系统 Python 无 pandas

- **现象**：`ModuleNotFoundError: No module named 'pandas'`
- **原因**：未在项目内建虚拟环境
- **处理**：`python -m venv .venv` 后 pip 安装 pandas/numpy/pyyaml
- **预防**：所有命令使用 `E:\EdgePdM-Agent\.venv\Scripts\python.exe`；根目录提供 `requirements.txt`

### T-007：GGUF 首次下载 404

- **现象**：`Qwen/Qwen2.5-0.5B-Instruct-GGUF` 下某文件名大小写/命名不匹配导致 Entry not found
- **原因**：HF 文件名与猜测不一致
- **处理**：Head 探测多条 URL；改用 `bartowski/.../Qwen2.5-0.5B-Instruct-Q4_K_M.gguf`（约 380MB）成功
- **预防**：下载前先 `HEAD`；在 `agent/README.md` 写死可用 URL 或探测脚本

### T-008：0.5B 解释质量不稳定（胡编 RUL 语义）

- **现象**：示例中偶发把 RUL 说成「年」、建议空泛、重复复述 JSON
- **原因**：模型容量小 + 未做强约束解码；属预期风险
- **处理**：不删瑕疵示例；在实验 notes / learning_llamacpp / 会议纪要写明局限；prompt 强调「不得改写 RUL」
- **预防**：面试主动讲边界；需要质量时换 1.5B+ Instruct GGUF 或加规则模板后处理

### T-009：马拉松轮次 rotate 崩溃残留 r05–r07

- **现象**：`experiments/` 除完整 `r01`–`r03` 外，仍有 `r05`/`r06`/`r07` 目录
- **原因**：上一会话中途崩溃，rotate「只留最近 2 轮」未执行完
- **处理**：2026-08-20 写入故事时标明为残留；主旁证看 `r01`–`r03`；可择机删除旧轮次
- **预防**：马拉松停止/崩溃后检查轮次目录；清理逻辑与训练同进程原子化
