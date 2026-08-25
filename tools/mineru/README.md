# MinerU 远程 PDF 提取

`extract_with_mineru_flash.py` 调用 MinerU 官方免 Token Agent 轻量解析接口：本机不下载模型，但会把指定 PDF 上传至远程服务。仅对已获授权上传的公开试卷使用。

```powershell
.venv\Scripts\python gaokao_math_benchmark\tools\mineru\extract_with_mineru_flash.py `
  "<试卷.pdf>" --output-dir "<输出目录>" --timeout 600
```

可用 `--page-range 10-20` 只解析指定页。默认启用中文 OCR、公式和表格识别，生成 Markdown 与任务回执。

MinerU 是初提取工具，不是数学正确性验证器。公式上下标、正负号、矩阵、分段函数、图形标注、题号和跨页内容都可能错位。必须执行“原始 PDF → MinerU Markdown → 原页逐题核对 → 数学复核 → 版本化修订”，不得根据猜测自动补写缺失公式。
