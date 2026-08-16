"""运行 Week 2 至 Week 8 核心测试，并生成源码覆盖率摘要。"""

from __future__ import annotations

import ast
import json
import runpy
import sys
import trace
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
SRC = ROOT / "src"
REPORTS = ROOT / "reports"


# 运行指定 unittest 参数，并输出核心源码覆盖率摘要。
def main() -> int:
    REPORTS.mkdir(exist_ok=True)
    # Week 8 源码包已自包含 Week 2–8 的正式模块。
    sys.path.insert(0, str(SRC))
    runner = trace.Trace(count=True, trace=False, ignoredirs=[sys.base_prefix, sys.exec_prefix])
    exit_code = 0
    try:
        runner.runctx(
            "runpy.run_module('unittest', run_name='__main__')",
            {"runpy": runpy, "__name__": "__main__"},
            {},
        )
    except SystemExit as exc:
        exit_code = int(exc.code or 0)
    coverage = _summarize(runner.results().counts)
    path = REPORTS / "coverage_summary.json"
    path.write_text(json.dumps(coverage, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Source coverage: {coverage['coverage_percent']:.2f}%")
    print(f"Coverage report: {path}")
    return exit_code


# 将 trace 行计数转换为按源码文件汇总的覆盖率报告。
def _summarize(counts):
    files = {}
    total = covered_total = 0
    # CLI 与生产装配文件属于入口胶水；覆盖率门槛聚焦可复用核心模块。
    packages = {
        "week4_retrieval": {"__init__.py", "cli.py"},
        "week6_integration": {"__init__.py", "factory.py"},
        "week7_release": {"__init__.py"},
        "week8_delivery": {"__init__.py"},
    }
    for package, excluded in packages.items():
        for source in sorted((SRC / package).glob("*.py")):
            if source.name in excluded:
                continue
            executable = _executable_lines(source)
            executed = {
                line
                for file_name, line in counts
                if Path(file_name).resolve() == source.resolve()
            }
            covered = len(executable & executed)
            total += len(executable)
            covered_total += covered
            files[str(source.relative_to(ROOT))] = {
                "statements": len(executable),
                "covered": covered,
                "coverage_percent": round(
                    covered / len(executable) * 100 if executable else 100,
                    2,
                ),
            }
    percent = covered_total / total * 100 if total else 100.0
    return {
        "coverage_percent": round(percent, 2),
        "covered": covered_total,
        "statements": total,
        "threshold_percent": 90.0,
        "threshold_met": percent >= 90.0,
        "files": files,
    }


# 从抽象语法树提取可执行语句所在行，作为覆盖率统计分母。
def _executable_lines(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    return {
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.stmt) and hasattr(node, "lineno")
    }


if __name__ == "__main__":
    raise SystemExit(main())
