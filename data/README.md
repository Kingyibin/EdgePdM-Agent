# 数据说明

## 数据集

- 名称：NASA C-MAPSS（Turbofan Engine Degradation Simulation）
- 用途：RUL（Remaining Useful Life）预测 benchmark
- 官方：NASA Prognostics Center of Excellence / [data.nasa.gov — CMAPSS Jet Engine Simulated Data](https://data.nasa.gov/dataset/cmapss-jet-engine-simulated-data)
- 本机采用镜像：Zenodo `CMAPSSData.zip`  
  `https://zenodo.org/records/15346912/files/CMAPSSData.zip?download=1`  
  （与 NASA progpy 数据集加载器引用一致）

## 当前布局（G1 已完成）

```text
data/raw/
  CMAPSSData.zip          # 原始压缩包（可选保留）
  _extract/               # 全量解压（含 FD001–FD004）
  train_FD001.txt
  test_FD001.txt
  RUL_FD001.txt
  readme.txt
  Damage Propagation Modeling.pdf
```

主线实验只用 **FD001**；其余子集在 `_extract/` 备查。

## 校验（实测 2026-07-23）

| 文件 | 大小(bytes) | 行数 | 备注 |
|------|-------------|------|------|
| train_FD001.txt | 3,515,356 | 20,631 | 100 units，完整失效 |
| test_FD001.txt | 2,228,855 | 13,096 | 100 units，截断 |
| RUL_FD001.txt | 429 | 100 | 每台一个 RUL；均值约 75.52 |

## 理解数据

不要只下载。必读：`notes/learning_cmapss.md`。

## Git

`data/raw/**` 默认 gitignore（保留 `.gitkeep` 与本 README）。需要复现时按上文 URL 重新下载。
