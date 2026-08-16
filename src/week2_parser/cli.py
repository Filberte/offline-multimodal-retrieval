"""批量导入命令行入口。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from week2_parser.ingestion import discover_files, ingest_files


def main() -> int:
    parser = argparse.ArgumentParser(description="解析 Week 2 支持的本地文件。")
    parser.add_argument("paths", nargs="+", help="需要导入的文件或目录。")
    parser.add_argument("--output", "-o", help="可选 JSON 报告输出路径。")
    args = parser.parse_args()

    # CLI 同时支持文件和目录：目录会先 discover，再统一交给 ingest_files。
    files: list[Path] = []
    for value in args.paths:
        path = Path(value)
        if path.is_dir():
            files.extend(discover_files(path))
        else:
            files.append(path)

    result = ingest_files(files)
    # 输出 JSON 报告，便于截图验收，也便于后续 UI 或日志系统复用。
    payload = {
        "total_files": result.total_files,
        "success_rate": result.success_rate,
        "parsed": [
            {
                "metadata": item.metadata.__dict__,
                "text_preview": item.text[:500],
                "warnings": list(item.warnings),
            }
            for item in result.parsed
        ],
        "failed": list(result.failed),
    }

    rendered = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered)
    # 如果存在失败文件，返回非 0，符合命令行工具的通用约定。
    return 0 if not result.failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
