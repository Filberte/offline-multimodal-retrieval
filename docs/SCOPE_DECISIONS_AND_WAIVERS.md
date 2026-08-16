# Scope Decisions and Deviation Record / 范围决定与偏差记录

- Document ID: W8-GOV-01
- Version: 1.0
- Date: 2026-08-16
- Status: recorded by the intern from the project lead's verbal decisions; **awaiting the project lead's written counter-signature**

## English summary

This document records every deliberate deviation between the original eight-week
task specification and the shipped system, together with who approved it and why.
Items marked "lead-approved (verbal)" were communicated by the project lead and
transcribed here by the intern on 2026-08-16; they become final when the lead
counter-signs. Nothing in this document retroactively upgrades evidence: platform
claims, tooling substitutions, and coverage scopes remain exactly as stated in the
per-week reports.

---

## 一、范围决定（负责人批准）

### D-01 平台范围：正式发布与演示以 Windows 为准

- **原要求**：Windows / macOS / Linux 三平台生产发布包（任务书 Week 8）。
- **决定**：实习期内以 Windows 真实构建与演示为验收基准;macOS/Linux 以
  源码契约模拟 + 预置 GitHub Actions workflow（`.github/workflows/cross-platform-release.yml`）交付,
  原生产物在仓库公开后由 CI（`windows-latest` / `macos-latest` / `ubuntu-latest`）生成。
- **理由**：实习生仅有 Windows 设备;跨平台通过源码契约与 CI 平摊风险,不做无证据声明。
- **批准**：项目负责人（口头,2026-08-16 由实习生转述记录）。

### D-02 可用性测试：自动化验证 + 专家走查,真人测试由负责人团队执行

- **原要求**：核心 UI 与无障碍流程的可用性测试（任务书 Week 5）。
- **决定**：实习期内交付 12 项任务式自动化可用性验证（TC-136–TC-150,成功率 100%）
  与专家走查;真实用户（含辅助技术用户）测试由负责人团队在交付后组织。
- **批准**：项目负责人（口头,2026-08-16 由实习生转述记录）。

### D-03 版本控制工作流：周度打包提交,Week 8 起建立 Git 仓库

- **原要求**：Git + GitHub 全程版本控制。
- **实际**：开发期间按周打包（manager_submission）直接提交负责人审阅,未保留连续 commit 历史;
  2026-08-16 起在 `offline-multimodal-retrieval` 建立 Git 仓库（单次回溯导入,提交信息中明确标注）,
  后续一切开发在 GitHub 上以连续提交进行。
- **批准**：项目负责人认可周度提交工作流（口头,2026-08-16 由实习生转述记录）。

### D-04 数据集替换：Natural Questions → SQuAD 2.0

- **原要求**：NQ 用于文本嵌入精度验证。
- **决定**：NQ 下载受限,Week 1 经负责人批准改用 SQuAD 2.0 dev 子集;COCO 2017 验证子集按原计划使用。
- **证据**：`Week3_Deliverables/reports/accuracy_validation.json`（"manager-approved NQ replacement"）。
- **批准**：项目负责人（Week 1,已有书面记录）。

### D-05 演示视频：按 W8-DEMO-04 手册由项目所有者录制

- **状态**：5 分钟逐镜头脚本、4 个稳定查询、录前检查表与异常恢复手册已就绪;
  录制完成后将视频链接补入 `README.md` 并关闭 W8-G10 gate。

## 二、技术栈偏差（含理由与缓解）

### T-01 PDF 解析：pypdf 替代 PDFium

- **理由**：纯 Python、无原生编译链,三平台行为一致,完全离线。
- **风险**：复杂版式/扫描件文本提取质量低于 PDFium。
- **缓解**：解析警告全量记录;基准集 62/62 文件解析零失败;扫描件走图像嵌入通道（MobileCLIP）。

### T-02 DOCX 解析：标准库 zipfile + XML 替代 Apache Tika

- **理由**：Tika 依赖 JVM,与"轻量离线端侧"目标冲突。
- **缓解**：解析器单元测试覆盖;`week2_parser` 覆盖率 94.85%。

### T-03 推理架构：Flutter UI + 本地 Python 子进程（stdio JSON-lines）

- **原设想**：Flutter 内嵌 TFLite 推理。
- **理由**：BERT TFLite 需 Select TF Ops,Windows 桌面 Dart 绑定不可用;
  stdio 桥不开端口、无网络面,通过 offline-only 安全审查（`SEC-001` 无监听器模式)。
- **缓解**：typed request/response 协议 + bridge 全量测试;TFLite/LiteRT 推理真实发生在本机
  （`bert_base_uncased_mean_pool_64.tflite`,SHA-256 已登记）。

### T-04 Google Test 未使用

- **理由**：项目无独立 C++ 业务模块（C++ 仅 Flutter Windows runner 模板）。
  测试由 Python unittest（460 例）+ flutter_test（140 例）承担,合计 600 例连续编号。

### T-05 无障碍外部工具验证延后

- **原要求**：Google Accessibility Scanner + WAVE。
- **现状**：Scanner 需 Android 实机、WAVE 需浏览器扩展与网页部署,当前环境均不可用（已如实记录于
  `accessibility_audit.json`）。以 12 项 WCAG 2.1 AA 映射自审、Flutter Semantics 自动化测试、
  对比度计算（5.67:1 正常 / 21:1 高对比)及《手动无障碍测试清单》（`docs/ACCESSIBILITY_MANUAL_TEST_CHECKLIST.md`,
  含 NVDA 步骤）替代;外部工具验证列为发布后跟进项。

### T-06 覆盖率统计口径

- Week 8 报告的 95.82% 覆盖 `week4_retrieval` / `week6_integration` / `week7_release` / `week8_delivery`;
- `week2_parser`（94.85%）与 `week3_embedding`（90.65%）在各自周度套件计量,
  并在 `week4_readiness_audit.json` 中以 90% 门槛复核通过。
- 所有模块均高于任务书对应周的门槛（80% / 85% / 90%）。

## 三、豁免后的最终验收映射

| # | 任务书交付物 | 豁免后状态 |
|---|---|---|
| 1 | 生产级跨平台应用 | Windows 达标（D-01 豁免 macOS/Linux 至 CI） |
| 2 | GitHub 生产代码库 | 本地仓库已建成并通过 460 例自测,待所有者公开发布（D-03） |
| 3 | 技术文档套件 | 达标 |
| 4 | 用户手册 + 无障碍指南 | 达标 |
| 5 | ≥90% 核心覆盖 + 集成/E2E 报告 | 达标（95.82% / 600 例,见 T-06 口径） |
| 6 | 开源合规报告 | 达标 |
| 7 | 5 分钟演示视频 | 脚本与手册就绪,录制待完成（D-05） |

## 四、会签

| 角色 | 姓名 | 签署 | 日期 |
|---|---|---|---|
| 实习生（记录人） | Guangzhe Zhu | ______ | 2026-08-16 |
| 项目负责人（批准人） | ______ | ______ | ______ |
