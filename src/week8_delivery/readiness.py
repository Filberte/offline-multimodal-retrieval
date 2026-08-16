"""Final Week 8 release and hand-off gate aggregation."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from week8_delivery.datasets import dataset_inventory
from week8_delivery.lineage import validate_lineage
from week8_delivery.models import DeliveryGate, FinalReadiness, PlatformAssessment


def build_final_readiness(
    root: str | Path,
    *,
    test_summary: dict[str, Any],
    platforms: tuple[PlatformAssessment, ...],
    required_documents: tuple[str, ...] = (),
) -> FinalReadiness:
    base = Path(root).resolve()
    project_root = base.parent
    lineage = validate_lineage(project_root)
    datasets = dataset_inventory(project_root)
    windows = next((item for item in platforms if item.platform == "Windows"), None)
    simulated = tuple(item for item in platforms if item.platform != "Windows")
    documents_present = all((base / path).is_file() for path in required_documents)
    total_tests = int(test_summary.get("total_tests", 0) or 0)
    core = test_summary.get("core", {}) if isinstance(test_summary.get("core"), dict) else {}
    flutter = test_summary.get("flutter", {}) if isinstance(test_summary.get("flutter"), dict) else {}
    gates = (
        DeliveryGate("W8-G01", "Week 1–8 contribution lineage", bool(lineage["all_contributions_present"]), "All eight weeks and feed-forward links are present"),
        DeliveryGate("W8-G02", "Week 1 datasets available", all(item.available for item in datasets), ", ".join(f"{item.key}:{item.discovered_samples}" for item in datasets)),
        DeliveryGate("W8-G03", "Cumulative automated suite", bool(test_summary.get("all_passed")) and total_tests == 600, f"{total_tests}/600; continuous={test_summary.get('continuous_ids_tc_001_to_tc_600')}"),
        DeliveryGate("W8-G04", "Python core coverage", float(core.get("coverage_percent", 0)) >= 90, f"{core.get('coverage_percent', 0)}%"),
        DeliveryGate("W8-G05", "Flutter source coverage", float(flutter.get("coverage_percent", 0)) >= 80, f"{flutter.get('coverage_percent', 0)}%"),
        DeliveryGate("W8-G06", "Windows production baseline", windows is not None and windows.decision == "GO", windows.decision if windows else "missing"),
        DeliveryGate("W8-G07", "macOS/Linux source contracts", len(simulated) == 2 and all(not item.blocking_failures for item in simulated), "; ".join(item.decision for item in simulated)),
        DeliveryGate("W8-G08", "Final manager documents", documents_present if required_documents else True, f"{len(required_documents)} required files"),
        DeliveryGate("W8-G09", "Public GitHub publication", False, "Prepared locally; publication requires owner authorization", blocking=False),
        DeliveryGate("W8-G10", "Five-minute demo video", False, "Recording is assigned to the project owner on Windows", blocking=False),
    )
    return FinalReadiness(
        version="1.0.0",
        generated_at=date.today().isoformat(),
        gates=gates,
        external_actions=(
            "项目所有者按录制脚本完成 5 分钟 Windows 演示视频并放入 final_submit。",
            "项目所有者确认无敏感信息后创建/选择公开 GitHub 仓库并推送准备好的源码。",
            "Apple/Linux runner 生成的构建产物应替换模拟证据后再声明对应平台实机发布。",
        ),
    )
