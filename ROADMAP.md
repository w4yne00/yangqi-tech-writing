# Roadmap

路线图说明演进方向，不承诺具体发布日期。版本行为遵循 Semantic Versioning。

## v1.1.x：兼容性增强

- 引入更多真实文种和近失配评测，降低过度触发与过度改写。
- 扩充法规编号、标准编号、责任主体和复杂时间表达的保护模式。
- 增加脚本误报、漏报和跨 Python 版本回归测试。
- 完善 Annotation mode、证据账本和复合文种路由。

## v1.2.0：Style Profile 接口

- 定义组织级 `organization-style-profile` schema。
- 支持按企业、部门和文种加载经批准的 Style Profile。
- 增加 Profile 完整性、证据追踪和冲突检查。
- 保持组织级语体与个人语言模仿之间的明确边界。

## v2.0.0：yangqi-style-distiller 协议

- 建设独立的 `yangqi-style-distiller` Skill，从授权样稿提炼组织级风格规则。
- 建立 Distiller 与 Writer 之间的稳定 Profile 协议和版本治理。
- 支持黄金样稿、失败样稿、冲突样稿和跨文种证据追踪。
- 对不兼容的 Profile schema 或运行行为变更使用主版本升级。
