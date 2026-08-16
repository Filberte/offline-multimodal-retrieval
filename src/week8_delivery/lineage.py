"""Executable Week 1–8 contribution lineage and traceability checks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from week8_delivery.models import WeekContribution


def default_lineage() -> tuple[WeekContribution, ...]:
    """Return the signed-off eight-week delivery chain in dependency order."""

    return (
        WeekContribution(
            1,
            "需求、环境、数据与风险基线",
            "定义离线、跨平台、无障碍和数据治理边界，并提供最终演示数据。",
            ("Week1_Deliverables", "datasets/required_datasets"),
            (
                "Week1_Deliverables/01_Project_Requirements_Document.docx",
                "datasets/required_datasets/README.md",
            ),
            2,
        ),
        WeekContribution(
            2,
            "模块架构与多格式解析",
            "将 TXT/PDF/DOCX/JPG/PNG 转换为统一可索引记录。",
            ("Week8_Deliverables/src/week2_parser",),
            ("Week2_Deliverables/manager_submission/01_Week2_系统架构设计与技术设计文档.pdf",),
            3,
        ),
        WeekContribution(
            3,
            "本地多模态嵌入",
            "提供文本、图像和共享向量空间，并支持批处理与离线模型。",
            ("Week8_Deliverables/src/week3_embedding", "Week3_Deliverables/models"),
            ("Week3_Deliverables/manager_submission/01_Week3_多模态嵌入引擎技术与验证报告.pdf",),
            4,
        ),
        WeekContribution(
            4,
            "向量存储与混合检索",
            "组合 Chroma、关键词、语义排序、过滤与端到端检索。",
            ("Week8_Deliverables/src/week4_retrieval",),
            ("Week4_Deliverables/manager_submission/06_Week4_端到端功能与检索准确率报告.pdf",),
            5,
        ),
        WeekContribution(
            5,
            "Flutter UI 与无障碍",
            "提供资料库、搜索、结果、设置以及键盘、语义、高对比度和字体缩放。",
            ("Week8_Deliverables/app/offline_retrieval_ui",),
            ("Week5_Deliverables/final_submission/03_Week5_无障碍合规验证报告_WCAG2.1AA.pdf",),
            6,
        ),
        WeekContribution(
            6,
            "集成、稳定性、性能与安全",
            "串联解析到 UI 的本地进程协议，建立缓存、压力、缺陷与数据安全门禁。",
            ("Week8_Deliverables/src/week6_integration",),
            ("Week6_Deliverables/final_submit_7_files/01_Week6_系统集成全量测试与性能优化技术报告.pdf",),
            7,
        ),
        WeekContribution(
            7,
            "文档、开源合规与发布治理",
            "固化 API、安装维护、许可、发布预检和 500 项连续测试。",
            ("Week8_Deliverables/src/week7_release", "Week8_Deliverables/docs"),
            ("Week7_Deliverables/final_submit_7_files/01_Week7_完整技术文档与维护指南.pdf",),
            8,
        ),
        WeekContribution(
            8,
            "最终交付、演示与作品集",
            "形成 Windows 实机发布基线、跨平台构建流水线、600 项累计测试和完整移交。",
            ("Week8_Deliverables/src/week8_delivery", "Week8_Deliverables/release"),
            ("Week8_Deliverables/README.md",),
            None,
        ),
    )


def validate_lineage(project_root: str | Path) -> dict[str, Any]:
    """Verify all contribution inputs and the continuous dependency chain."""

    root = Path(project_root).resolve()
    contributions = default_lineage()
    weeks = [item.week for item in contributions]
    continuous = weeks == list(range(1, 9))
    feed_chain = all(
        item.feeds_week == item.week + 1 for item in contributions[:-1]
    ) and contributions[-1].feeds_week is None
    records = []
    for item in contributions:
        sources = [(path, (root / path).exists()) for path in item.source_paths]
        evidence = [(path, (root / path).is_file()) for path in item.evidence_paths]
        records.append(
            {
                **item.to_dict(),
                "source_status": [
                    {"path": path, "present": present} for path, present in sources
                ],
                "evidence_status": [
                    {"path": path, "present": present} for path, present in evidence
                ],
                "passed": all(present for _, present in (*sources, *evidence)),
            }
        )
    return {
        "weeks": weeks,
        "continuous_weeks_1_to_8": continuous,
        "continuous_feed_chain": feed_chain,
        "contributions": records,
        "all_contributions_present": continuous
        and feed_chain
        and all(record["passed"] for record in records),
    }
