# yangqi-tech-writing GitHub 公开发布设计

日期：2026-07-11

状态：已批准

目标仓库：`w4yne00/yangqi-tech-writing`

## 1. 发布目标

将已经完成并通过验证的 `yangqi-tech-writing v1` 发布为公开 GitHub 项目，形成可安装、可测试、可追踪版本、可持续演进的 G 企网络安全与信息化技术写作 Skill。

首次公开版本使用 `v1.0.0`，采用 MIT License。仓库默认分支为 `main`，GitHub Release 附带可直接安装的 `yangqi-tech-writing.skill`。

## 2. 发布范围

首次发布包含：

- 主运行入口 `SKILL.md`；
- 7 类正式文种场景包；
- 保护项、证据、AI 痕迹、结构反模式、组织语体和质量闸门规则；
- `protected_diff.py`、`evidence_check.py`、`style_audit.py`；
- 24 项评测数据；
- 22 项单元测试及脚本烟测样例；
- README、TESTING、CHANGELOG、ROADMAP、VERSION、LICENSE；
- Python 3.9、3.11、3.12 GitHub Actions 测试矩阵；
- `.skill` 安装包和 `v1.0.0` Release。

不在首次发布范围内：

- `yangqi-style-distiller` 的实现；
- 企业历史文档解析和 Style Profile 提炼；
- 技术方案正确性、法规适用性或 AI 作者身份判断；
- 在线服务、Web 界面和知识库后端。

## 3. 仓库结构

```text
yangqi-tech-writing/
├── .github/
│   └── workflows/
│       └── test.yml
├── evals/
│   └── evals.json
├── references/
│   ├── scene-packs/
│   └── *.md
├── scripts/
│   └── *.py
├── tests/
│   ├── fixtures/
│   └── test_*.py
├── .gitignore
├── CHANGELOG.md
├── LICENSE
├── README.md
├── ROADMAP.md
├── SKILL.md
├── TESTING.md
└── VERSION
```

`.skill` 文件不纳入 Git 历史中的源码根目录，通过 GitHub Release 附件交付，避免二进制包与源码重复维护。

## 4. README 设计

README 以中文为主，顶部保留简短英文摘要和检索关键词。内容顺序固定为：

1. 项目定位与一句话摘要；
2. 适用场景和不适用边界；
3. 核心能力与执行链路；
4. 安装方式；
5. 使用示例；
6. 目录结构；
7. 三个审计脚本的用途和退出码；
8. 测试与 CI；
9. 版本策略与路线图；
10. 贡献方式、许可证和免责声明。

README 不使用“彻底消除 AI 味”“保证合规”“自动生成高质量方案”等不可验证宣传语。项目说明应明确：风格审计不判断作者身份，正则检查不能代替技术和法律审查。

## 5. 版本规划

采用 Semantic Versioning：

- `v1.0.0`：当前稳定公开版，包含 7 类场景、24 项评测和 3 个审计脚本；
- `v1.1.x`：向后兼容的规则、场景包、脚本和评测增强；
- `v1.2.0`：新增组织级 Style Profile 加载接口；
- `v2.0.0`：与独立的 `yangqi-style-distiller` 建立稳定 Profile 协议，允许不兼容的结构升级。

补丁版本只修复错误或完善文档；次版本可增加向后兼容能力；主版本用于接口或行为的不兼容变化。

## 6. CHANGELOG 与 ROADMAP

`CHANGELOG.md` 采用 Keep a Changelog 风格，首版记录 Added、Quality、Known Limitations 三组内容。

`ROADMAP.md` 公开以下方向：

- v1.1：真实语料评测、保护项模式增强、触发边界评测；
- v1.2：Style Profile schema、加载规则和一致性检查；
- v2.0：`yangqi-style-distiller`、来源追踪和组织风格版本治理。

路线图表达方向，不承诺未经确认的发布日期。

## 7. CI 与质量门槛

GitHub Actions 在 push 和 pull_request 时运行：

```bash
python -m unittest discover -s tests -v
python scripts/style_audit.py tests/fixtures/sample.md
```

测试矩阵覆盖 Python 3.9、3.11、3.12。CI 不额外安装运行时依赖。首版发布前必须满足：

- 22 项单元测试全部通过；
- `SKILL.md` frontmatter 和本地引用有效；
- `evals/evals.json` 含 24 个唯一用例；
- `.skill` 压缩包完整且不含 `evals/`、`__pycache__`、`.DS_Store` 和 `.pyc`；
- README、VERSION、CHANGELOG 和 Release 标签均为 `1.0.0` / `v1.0.0` 对应关系。

## 8. Git 与 GitHub 发布流程

1. 将已验证的 v1 源码复制到当前仓库根目录；
2. 新增开源项目文件和 CI；
3. 在本地运行完整测试和打包检查；
4. 提交到 `main`，首个提交信息为 `release: publish yangqi-tech-writing v1.0.0`；
5. 使用 GitHub CLI 创建公开仓库 `w4yne00/yangqi-tech-writing`；
6. 推送 `main`；
7. 创建带注释标签 `v1.0.0` 并推送；
8. 创建 GitHub Release，正文取自 CHANGELOG，上传 `.skill` 附件；
9. 回读仓库、CI、标签和 Release 状态。

## 9. 外部写入与认证

创建仓库、推送标签和发布 Release 属于明确授权的 GitHub 外部写入。当前 `gh` 的 `w4yne00` 令牌已失效；执行外部步骤前，用户需要完成 `gh auth login -h github.com`。认证恢复后，再检查目标仓库名是否已被占用。

## 10. 验收标准

- `https://github.com/w4yne00/yangqi-tech-writing` 可公开访问；
- 默认分支为 `main`；
- README 在仓库首页正确渲染；
- MIT License、VERSION、CHANGELOG、ROADMAP 完整；
- Actions 工作流存在且测试通过；
- `v1.0.0` 标签和 Release 存在；
- Release 包含可下载的 `yangqi-tech-writing.skill`；
- 仓库内容不包含密钥、账号令牌、个人文档或未授权历史材料。

## 11. 设计自检

- 无未定义占位项；
- 仓库、版本、许可证、分支和发布物口径一致；
- 首版不提前耦合尚未设计的 Distiller；
- 外部写入均在用户明确授权范围内；
- 公开发布不扩大技能对技术正确性、法律适用性和作者身份的能力声明。
