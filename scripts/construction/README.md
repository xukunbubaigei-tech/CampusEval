# 数据构建工具

- [考研数据构建](kaoyan/README.md)
- [MIT 数据构建](mit/README.md)
- [SOA 数据构建](soa/README.md)
- [U-MATH 数据构建](umath/README.md)

## PDF 提取输入规范

需要 MinerU 提取的新 PDF 统一通过 [MinerU 网页端](https://mineru.net/)精准解析，下载 JSON 后，保存到 `workspace/` 下以解析内容命名的直接子文件夹。完整步骤见 [workspace 标准流程](../../workspace/README.md#网页端精准解析标准步骤)。新批次需适配各来源构建器的固定路径与文件名，不直接将原始版面 JSON 当作题目 JSONL。
