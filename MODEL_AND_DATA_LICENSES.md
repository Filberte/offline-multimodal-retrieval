# Model and dataset license boundaries

## Release decision

The source archive contains adapters, conversion hooks, tests, and aggregate evaluation results only. It excludes pretrained weights and original evaluation datasets. Users must obtain optional models and datasets from authoritative sources and accept their terms independently.

## Models

- BERT Base code and published checkpoints are associated with the upstream Apache-2.0 project. The release does not bundle a checkpoint; the local path is configured by the user.
- MobileCLIP code is MIT-licensed, while published weights use Apple’s ML Research Model Terms of Use and DataCompDR data uses CC-BY-NC-ND. Consequently, MobileCLIP weights and training data are explicitly excluded from the distributable package.
- timm source is Apache-2.0, but pretrained weights can inherit dataset or model-specific conditions. Weight selection therefore remains a separate approval step.

## Validation data

- Wikipedia text can require attribution and share-alike handling under CC BY-SA/GFDL terms.
- SQuAD, COCO, and RVL-CDIP artifacts must be reviewed against their own source terms and content-level rights.
- The Week 7 archive includes only derived aggregate metrics and synthetic test fixtures; it does not redistribute source articles, photos, annotations, or question/answer records.

## Operational rule

The preflight gate fails when model-weight extensions such as `.pt`, `.pth`, `.ckpt`, `.onnx`, `.tflite`, or `.safetensors` are found in the release root. A maintainer may use these assets locally, outside the source distribution boundary.
