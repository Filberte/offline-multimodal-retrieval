"""Week 8 final-delivery orchestration and evidence contracts."""

from week8_delivery.datasets import (
    dataset_inventory,
    default_demo_selection,
    prepare_demo_dataset,
)
from week8_delivery.lineage import default_lineage, validate_lineage
from week8_delivery.platforms import evaluate_platforms
from week8_delivery.readiness import build_final_readiness

__all__ = [
    "build_final_readiness",
    "dataset_inventory",
    "default_demo_selection",
    "default_lineage",
    "evaluate_platforms",
    "prepare_demo_dataset",
    "validate_lineage",
]
