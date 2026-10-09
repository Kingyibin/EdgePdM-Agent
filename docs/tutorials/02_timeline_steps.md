# EdgePdM-Agent · 全过程逐步拆解（详课）

> 按选题 → G0–G6 → 定稿 → 马拉松 → 首提 git 走路。  
> 简历 2026.06–至今 = 实做；Gate/JSON 日期 07-23 起 = 落盘。  
> 原理课（RUL、泄漏、NASA Score、ONNX 边界）见 `docs/tutorials/01_mastery_from_zero.md`。  
> 仓库：`E:\EdgePdM-Agent`。负责人不得自己宣布 Gate PASS。

正式主数字（capped RUL=125，测试每台 last cycle/window）：

| 模型 | RMSE | MAE | NASA Score | 角色 |
|------|------|-----|------------|------|
| Ridge | 20.84 | 16.34 | 1285 | 线性下限 |
| XGBoost | **17.48** | 12.29 | 929 | 表格标尺 |
| LSTM | **14.27** | **10.48** | **324.6** | 正式交付 + 导 ONNX |
| 扫描最优 | ~13.10 | — | ~240.8 | **旁证，无权重** |

C++：同一窗口 pred ≈ **118.47**，单线程约 **0.167 ms**。LLM **不算** RUL。

---

## 地图

```text
选题：否手册 RAG、否微调主线；要公开数据 + C++ + 本地解释
G0 骨架、主管闸门、T-001 git
G1 Zenodo 下载、venv、讲清 RUL 标签（T-002/T-003）
G2 Ridge/XGB 同口径标尺
G3 LSTM window=30 打赢 XGB，存 lstm.pt
G4 导出 ONNX；WinLibs；GBK dynamo；dlltool（T-004～006）
G5 llama.cpp 只解释 JSON；GGUF 404；0.5B 把 RUL 说成「年」（T-007/008）
G6 README / 架构 / 简历草稿 / 终审 COMPLETE
08-06 定稿：时间线、会议、双角色
08-20 马拉松扫描 13.10 不换正式模型（ADR-009，T-009）
本地首提 04c4b69
```

---

## 第 0 步：选题——补 C++/端侧，而不是再做一本手册

**当时简历缺口**  
有客流 LSTM、有一段 RAG、有嵌入式/实习，投 C++ / 端侧 AI / Agent 时缺一块硬项目。

**明确不选**  
- 手册型工业诊断 RAG：资料不够，且和 CursorRAG 重复，再做一遍会翻同样的车。  
- 大模型微调当主线：补不了最缺的 C++ 与端侧工程。

**选**  
公开 **NASA C-MAPSS FD001**（仿真航空发动机多传感器退化）→ 自训 RUL → ONNX → C++ ORT → llama.cpp 解释结构化 JSON。

**发动机只是练习场**  
方法叙事是「多传感器时间序列上的预测性维护 + 端侧部署」，不是转航发。

**动机可以诚实说**  
启动理由里有「GitHub 上有可复现 pipeline」。对外必须是**复现 + 扩展**（C++ 与本地 LLM），不能只交复刻。ADR-001/002 写在 `docs/02_decision_record.md`。

**心路原文位置**  
`notes/mindset_journal.md` 2026-07-23 立项段。

---

## 第 1 步：G0 立项骨架

**Gate 要什么**  
项目可被接手：目录、README/AGENTS、G0–G6 验收单、ADR、学习计划、work_log / mindset / trial_error、`CURRENT_GATE`、`.gitignore`（数据、venv、大权重）。

**T-001**  
Cursor `create_project` 报 `spawn /bin/sh ENOENT`（Windows 对该 MCP 的 shell 假设不兼容）。目录已手工建好，本地 `git init` 成功。预防：本机优先 PowerShell/git，MCP 失败不阻塞立项。

**制度**  
`.cursor/agents/project-manager.md`：拆阶段、PASS/FAIL。  
**负责人不得自行宣布 Gate PASS。** 会议：`docs/meetings/2026-07-23_G0_kickoff.md`。

**下一步为什么是数据不是模型**  
标签讲不清，后面 RMSE 再低也是假的。G0 PASS 后才允许 G1。

---

## 第 2 步：G1 数据——先能讲，再写代码

**目标**  
不看代码也能讲清标签怎么来。不是「Kaggle 下了就算」。

**T-002 下载**  
NASA 门户偏交互，不便脚本化。改用 Zenodo `CMAPSSData.zip`（progpy 同源引用），下载后校验行数。`data/README.md` 同时写官方口径和镜像。

**校验（必须能报）**  
- `train_FD001.txt`：**20631** 行，100 台，跑到失效  
- 测试：**13096** 行，100 台，中途截断  
- `RUL_FD001.txt`：**100** 行，每台截断时刻再过多少周期会坏  

**T-003 环境**  
系统 Python 无 pandas → `python -m venv .venv`，以后命令走 `E:\EdgePdM-Agent\.venv\Scripts\python.exe`。

**必须能讲的标签逻辑**

1. 每行：`unit, cycle, 3 个工况, 21 个传感器`。很多通道几乎常数，正式特征留 **17 个有变化的**（`src/features.py` / `configs/default.yaml`）。  
2. **训练 RUL** = 该 unit 最大 cycle − 当前 cycle（因为训练跑到失效）。  
3. **测试**没有完整失效曲线：官方另给 RUL 文件，模拟「现在还没坏、要你估计还剩多久」。  
4. **capped 125**：早期寿命很长时传感器几乎没退化，硬学「还剩 300」没稳定信号。125 是 C-MAPSS 论文常见设定，不是物理寿命。  
5. **FD001 单工况**。别说已经泛化 FD002/004 多工况。  
6. **按 unit 切分**：不能把所有行随机 8:2。同一台后面的周期进测试 = 泄漏。

学习笔记：`notes/learning_cmapss.md`（含面试五问）。  
教程：`docs/tutorials/00_project_walkthrough_for_beginners.md`。  
会议：`2026-07-23_G1_data_sync.md`。G1 PASS 后才 G2。

---

## 第 3 步：G2 Baseline——没有尺子就不要谈深度学习

**要解决的问题**  
LSTM 再低，没有同口径表格模型，面试官会说 magician。

**代码**  
`src/data.py` `features.py` `metrics.py`；入口 `scripts/run_baseline_fd001.py`。  
不是只 clone 外部仓库交差，代码在本仓 `src/`。

**特征**  
当前 cycle 的 17 维 + 滚动统计（rolling_window=5）→ 共 34 维。XGB 吃的是**手工表**，不是 30 步轨迹。

**划分**  
- 测试：每台 **last cycle**（100 个点）  
- CV：`GroupKFold` 按 unit  
- scaler **只 fit 训练 unit**

**指标（`experiments/exp_20260722_baseline_xgb_ridge/metrics.json`）**

| | RMSE capped125 | MAE | NASA Score | RMSE 原始 RUL |
|--|----------------|-----|------------|---------------|
| Ridge | 20.84 | 16.34 | 1285.3 | 21.79 |
| XGBoost | **17.48** | 12.29 | **929.3** | 18.41 |

GroupKFold 上 XGB RMSE 均值约 **18.60**（验证），测试 17.48，没有崩。

**NASA Score 为什么要报**  
非对称：预测太乐观（`pred > true`，以为还能跑、其实快坏）惩罚更重。代码 `src/metrics.py` `nasa_score`。维护场景里「晚报警」比「早报警」更糟。

**产物**  
metrics、joblib、散点图、`experiments/exp_20260722_baseline_xgb_ridge/`。  
会议：`2026-07-23_G2_baseline_review.md`。PASS 后允许 G3。

**下一步**  
有了 17.48 这把尺子，序列模型必须打赢它才配导 ONNX。

---

## 第 4 步：G3 LSTM——正式算法数字从这里锁死

**窗口怎么造（`src/sequence.py`）**

- `build_windows`：每个 unit 内，每个能满 30 拍的终点都是一个训练样本；标签是**窗口最后一拍**的 RUL。  
- `last_window_per_unit`：测试每台只用最后 30 拍；长度不够就**前面重复第一行 padding**。

**正式结构（实验 notes 原文）**  
window=30，17 维，**2 层 hidden 64**，dropout=0.2，Adam lr=1e-3，MSE，25 epoch，按 unit 留 20% 验证，取 best val checkpoint。Scaler 只在训练窗口 fit。

脚本：`scripts/run_lstm_fd001.py`。  
产物：`experiments/exp_20260722_lstm_fd001/`（`lstm.pt`、`predictions_lstm.csv`、`scatter_lstm.png`、`history.json`、`metrics.json`）。

**同口径对比**

| 模型 | RMSE | MAE | Score |
|------|------|-----|-------|
| G2 XGB | 17.48 | 12.29 | 929.3 |
| **G3 LSTM** | **14.27** | **10.48** | **324.6** |

验证集 best RMSE ≈ **13.70** 是留出发动机的全部窗口；测试 14.27 是每台最后一窗，两个数不能读成「只掉了 0.6」。Score 从 929 到 325，是相对 XGBoost 少了一批大的乐观误差（晚报警占 Score 的比例从约 88% 降到约 61%），不是每一台都变准。细节在 `docs/07_seal_review.md`。

**为什么 LSTM 能赢 XGB（可以说、不要神化）**  
XGB 看当前拍的滚动统计；LSTM 看 30 步斜率。window 太短或划分泄漏，LSTM 也会输。不是「深度学习一定强」。

**ADR-005**  
主模型候选 LSTM，部署走 ONNX。XGB 留在表里对照。  
会议：`2026-07-23_G3_lstm_compare.md`。

**明确没做**  
Transformer、双向三层 Attention 当正式交付。数据只有 100 台训练机，更深不一定更好——后面马拉松会证明种子都能把同结构晃到 15.29。

---

## 第 5 步：G4 ONNX + C++——证明能部署，不是 notebook

拆成「导出 → 编译 → 对齐」三小步，每步都有真坑。

### 5.1 导出

`scripts/export_lstm_onnx.py` → `models/onnx/rul_lstm.onnx` + sidecar。

**T-005**  
`torch.onnx` dynamo 路径往控制台打 emoji `✅`，Windows 默认 GBK → `UnicodeEncodeError`。  
处理：`dynamo=False` 走 legacy exporter；`PYTHONIOENCODING=utf-8`。  
这不是模型问题，是工具链编码。

### 5.2 编译

**T-004**  
干净 Windows：`cmake` / `g++` / `cl` 都不在 PATH。  
处理：`winget install BrechtSanders.WinLibs.POSIX.UCRT`（g++ 与 cmake）。

**T-006**  
官方 ONNX Runtime 给的是 **MSVC import lib** `onnxruntime.lib`。MinGW 链不过。  
处理：`gendef onnxruntime.dll` + `dlltool` 生成 `libonnxruntime.a`（导出 `OrtGetApiBase` 等）。  
写入 `cpp_inference/README.md`。

代码：`cpp_inference/src/main.cpp`，CMake 工程。

### 5.3 证明了什么、没证明什么

**ADR-006 诚实边界**  
C++ **不**做滚动均值、不 fit scaler。它读一张**已经缩放过**的 30×17 CSV，喂给 ORT。  
证明的是推理引擎 + 延迟，不是「特征工程已全部 C++ 化」。下一步才是把 mean/scale 写进 sidecar 在 C++ 里减除。

**实测（`experiments/exp_20260723_cpp_onnx_infer/metrics.json`）**

| 项 | 值 |
|----|-----|
| 样本 | `sample_window_unit1_scaled.csv` |
| Python ORT pred | 118.4717 |
| C++ pred | 118.472 |
| unit1 真 RUL | 112.0 |
| 延迟 | **0.167 ms**（warmup 5 + 50 iter 平均） |
| 线程 | intra_op=1 |
| 工具链 | MinGW-w64 g++ 16.1.0 + CMake 4.3.3 + ORT 1.20.1 |

差在浮点打印，不是两套模型。  
0.167 ms 是**单窗口、单样本、这台 CPU**，不是产线 1000 台并发。

会议：`2026-07-23_G4_cpp_onnx.md`。学习笔记：`notes/learning_onnx_cpp.md`。

---

## 第 6 步：G5 本地 LLM——只解释，不许改数字

**目标**  
把「RUL=118、风险=预警、异常传感器=…」说成人话。主线**不是**手册 RAG。

**T-007**  
按 `Qwen/Qwen2.5-0.5B-Instruct-GGUF` 猜文件名 → 404。  
HEAD 探测后改用 `bartowski/.../Qwen2.5-0.5B-Instruct-Q4_K_M.gguf`（约 380MB）成功。  
预防：下载前 HEAD；URL 写死在 `agent/README.md`。

**怎么跑**  
`scripts/start_llama_server.ps1` 起 `llama-server`；`agent/explain_client.py` 把 JSON 塞进 prompt。  
示例 5 组：`agent/examples/case01_*` … `case05_*`。

**ADR-007**  
LLM 不得改 RUL、不得当回归器。小模型预测寿命会胡编。

**T-008（故意留着的瑕疵）**  
0.5B 偶发把 RUL 说成「年」、建议空泛、重复复述 JSON。  
处理：**不删**瑕疵示例；笔记和会议写明局限；prompt 强调不得改写 RUL。  
需要质量时换 1.5B+ Instruct，或规则模板后处理——那是质量迭代，不是架构错误。

会议：`2026-07-23_G5_llm_boundary.md`。

---

## 第 7 步：G6 结项包装

外人要能复现，面试要能深聊。

验收：  
- README：安装、数据、训练、C++、LLM 分步  
- `assets/design/architecture.md`  
- `docs/benchmark_summary.md`  
- 简历草稿 `docs/resume_project_bullet.md`  
- iteration_log 与 mindset 总复盘  

主管终审 PASS，`CURRENT_GATE` = **COMPLETE**（2026-07-23）。  
会议：`2026-07-23_G6_closeout.md`。

结项前复盘四条（mindset）：标签能讲清；baseline 与 LSTM 同口径；延迟是实测；LLM 边界写死。承认 0.5B 一般、C++ 吃预缩放窗口。

---

## 第 8 步：2026-08-06 定稿审查

**缺的不是再一个模型，是「像不像真实做过」**  
有没有人卡关？失败有没有写下？别人能不能按索引把故事讲完？

补了：`docs/04_roles_and_governance.md`、`project-lead` subagent、`docs/05_full_process_timeline.md`、会议全集、`docs/06_final_delivery_audit.md`、`docs/INDEX.md`、T-007/008 与 ADR-005～008。

**不重训模型。** 痕迹要能从 INDEX 读到。

---

## 第 9 步：马拉松扫描（结项后旁证）

**动机**  
闲时验证「14.27 是不是单次运气」；补 MC Dropout 不确定性。  
脚本：`training_marathon.py`。入库故事：`experiments/marathon_sweep_notes.md`。ADR-009。

**扫描设定**  
每轮 12 组真训（非模拟）：window 15–40、hidden 48–96、层数 1–3、lr 1e-3/5e-4/2e-3、seed 轮换。单次约 18 epoch（短于正式 25）。目录**只写 metrics.json，不存 .pt**。

**目录怎么读**  
- `r01_`～`r03_`：完整轮次，主旁证  
- `r05_`～`r07_`：上一会话崩溃残留（T-009，rotate 没清完），不影响结论  
- `exp_*`：七月正式实验，**简历仍看这里**

**关键数字**

| 谁 | RMSE | Score | 有没有权重 |
|----|------|-------|------------|
| 扫描最优 `r01_w30_h64_lr5e4` | **13.10** | 240.8 | **无**，未导 ONNX |
| 同结构另一 seed `r01_w30_h64` | 13.37 | 284.4 | 无 |
| 同结构 `r03_w30_h64` | **15.29** | 548.4 | 无（可变差） |
| 正式 G3 | **14.27** | 324.6 | 有 `lstm.pt` + C++ 对齐 |

约 67/71 组打赢 XGB 17.48。  
`r03_w30_h64` 的 MC Dropout coverage95 ≈ 0.67，mean σ ≈ 6.99。

**面试怎么用这个故事**  
「我后来扫过，最好到 13.1，同结构换种子也能差到 15.3。所以 14.27 不是玄学一次。但我没有权重、没有 C++ 复验，不能把 13.1 写进简历主数字。要换主线得另开 G7：重训存权 → ONNX → C++。」

---

## 第 10 步：本地 git 首提 `04c4b69`

长时间「有文件无 commit」。Cursor 切工作区时 `git stash` 在空仓上失败。  
首提包含源码+文档+指标，**不含** GGUF 和大权重。  
到定稿时仍是本地仓，未作为独立远程强推——面试被问「GitHub 链接」要按当时真实托管情况说，不要假装一直有公开远程。

---

## 错误速查（现象 → 处理）

| ID | 阶段 | 一句话 |
|----|------|--------|
| T-001 | G0 | create_project ENOENT → 手工 git init |
| T-002 | G1 | NASA 门户不便 → Zenodo + 行数校验 |
| T-003 | G1 | 无 pandas → 项目 venv |
| T-004 | G4 | 无编译器 → WinLibs |
| T-005 | G4 | dynamo emoji / GBK → legacy export |
| T-006 | G4 | MSVC lib vs MinGW → gendef/dlltool |
| T-007 | G5 | GGUF 404 → bartowski Q4_K_M |
| T-008 | G5 | 0.5B 胡编 RUL 含义 → 留瑕疵 + 写边界 |
| T-009 | 扫描 | rotate 崩溃留 r05–r07 → 文档标明残留 |

---

## 90 秒串讲

投递缺 C++/端侧，不选手册 RAG 和微调。用公开 FD001 把按设备划分和 capped RUL 讲清，XGB 17.48 当尺子，LSTM 30 窗 2 层 64 到 14.27。导出 ONNX 时 dynamo 在 GBK 控制台炸掉，MinGW 链不了 MSVC 的 ORT lib，用 dlltool 打通。C++ 只吃预缩放 30×17，对齐 118.47、约 0.17ms。本地 0.5B 只解释 JSON，还会把 RUL 说成「年」。后来扫描出过 13.1，没有换正式端侧模型。
