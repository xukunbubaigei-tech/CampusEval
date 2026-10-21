"""Refresh the human-readable dataset inventory without a JSON manifest."""
from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FILES = (
    ('高考 Benchmark', 'main/benchmark.jsonl', '题目'),
    ('训练集', 'main/training.jsonl', '题目'),
    ('考研数学一', 'kaoyan/questions.jsonl', '题目'),
    ('MIT', 'MIT/questions.jsonl', '题目'),
    ('SOA', 'SOA/questions.jsonl', '题目'),
    ('U-MATH', 'U-MATH/questions.jsonl', '题目'),
    ('客观题 mini', 'objective_70/questions.jsonl', '固定子集'),
    ('主观题 mini', 'subjective_50/questions.jsonl', '固定子集'),
    ('固定主观题 Rubric', 'subjective_50/rubrics.jsonl', 'Rubric'),
    ('考研 Rubric', 'kaoyan/rubrics.jsonl', 'Rubric'),
    ('Benchmark Rubric', 'main/benchmark.rubrics.jsonl', 'Rubric'),
    ('训练集 Rubric', 'main/training.rubrics.jsonl', 'Rubric'),
)


def inventory(root: Path) -> list[dict]:
    result = []
    for label, relative, kind in FILES:
        path = root / 'datasets' / relative
        if not path.is_file():
            continue
        raw = path.read_bytes()
        records = [json.loads(line) for line in raw.decode('utf-8-sig').splitlines() if line.strip()]
        result.append(dict(label=label, path=relative, kind=kind, records=len(records),
                           bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
    return result


def write_dataset_readme(root: Path) -> Path:
    files = inventory(root)
    primary = sum(item['records'] for item in files if item['kind'] == '题目')
    image_count = sum(p.is_file() for p in (root / 'data/images').rglob('*'))
    lines = [
        '# 数据集说明与文件清单', '',
        f'清单更新日期：{date.today().isoformat()}。以下数量、字节数和 SHA-256 按当前实际文件统计。', '',
        f'六份主数据当前合计 **{primary:,} 条记录**，规范图片 **{image_count} 个文件**。'
        '固定 mini 是主库子集，不重复计入主记录总量；ID 唯一不代表已完成语义去重。', '',
        '## 文件导航', '',
        '| 数据 | 文件 | 类型 | 记录数 | 字节数 |',
        '|---|---|---|---:|---:|',
    ]
    for item in files:
        lines.append(f"| {item['label']} | [{item['path']}]({item['path']}) | {item['kind']} | {item['records']} | {item['bytes']} |")
    lines += [
        '', '来源、许可和各库使用边界见各子目录 README；已完成修订与待处理问题见 '
        '[数据维护摘要](MAINTENANCE.md)。模型测试结果单独保存在 [reports/](../reports/README.md)。', '',
        '## 数据格式与使用边界', '',
        '- 文件为 UTF-8 JSONL，每行一个对象。题目包含 `id`、`source`、`question`、`answer`、`metadata`；'
        'Rubric 通过 `question_id` 对应题目，包含 `rubric`、`reference_solution_1`、`reference_solution_2`。',
        '- 图片路径相对项目根目录，统一位于 `data/images/`。复制数据时需同时保留引用图片。',
        '- 主观题 Rubric 使用实验性统一 20 分尺度，生成完成与结构校验通过均不代表逐题数学复核通过。',
        '- U-MATH 原始数据没有独立解析，`solution` 留空；考研有 47 条空解析，其中 '
        '`kaoyan_math1_2022_03_19` 未生成 Rubric。',
        '- 主观题 mini 有 14 条与训练集同 ID，训练后评测需隔离重叠记录，并进一步检查同题异 ID 和近似题。',
        '', '## 文件版本指纹', '',
        'SHA-256 用于人工核对文件是否与此清单记录的版本相同，不证明数学内容正确。'
        '题库改变后应重新生成本清单；离线结构校验直接检查现有文件，不再依赖 JSON 发布清单。', '',
        '| 文件 | SHA-256 |', '|---|---|',
    ]
    lines += [f"| `{item['path']}` | `{item['sha256']}` |" for item in files]
    lines += [
        '', '## 维护方式', '',
        '从项目父目录执行：', '', '```powershell',
        '.venv\\Scripts\\python.exe CampusEval\\scripts\\maintenance\\update_dataset_readme.py',
        '.venv\\Scripts\\python.exe CampusEval\\scripts\\maintenance\\validate_clean_release.py', '```', '',
        '第一条命令更新本说明中的清单；导入脚本发布新数据后也会自动更新。第二条检查结构、ID、固定子集、'
        '原有 50 份 Rubric 及图片引用，结果写入本地 `workspace/reports/dataset_validation.json`。'
        '考研专项校验结果写入本地 `workspace/reports/kaoyan_validation.json`。'
        '这些检查不提供全库数学正确性认证；新增 Rubric 的既有验证范围见数据维护摘要。', '',
    ]
    path = root / 'datasets/README.md'
    path.write_text('\n'.join(lines), encoding='utf-8')
    return path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root', type=Path, default=ROOT)
    args = parser.parse_args()
    print(write_dataset_readme(args.project_root.resolve()))
