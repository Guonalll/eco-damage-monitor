# 广域生态破坏公开网络信息采集与分析系统

本项目是一个面向公开网络文本的合规采集与分析 MVP，围绕“广域生态破坏”主题，提供采集、清洗、结构化抽取、专题识别、地理归一、统计分析与 Streamlit 可视化面板。项目强调工程化、可维护、可配置与可审计，默认使用 SQLite，可通过配置切换到 PostgreSQL。

## 1. 系统总体架构图（文本）

```text
公开数据源
├─ 主流新闻公开网页
├─ 政府门户公开网页
├─ 无需登录的公开论坛/社区网页
└─ 公众号授权导出数据 / 人工整理 URL 清单

采集层
├─ BaseCollector 抽象基类
├─ News / Gov / Forum 示例采集器
├─ WeChat 授权导入模块
└─ 限速 / 重试 / 超时 / robots 检查 / 去重接口

解析清洗层
├─ HTML 解析
├─ 正文抽取
├─ 样板文本去除
├─ 特殊符号与全半角归一
└─ 中文分句

去重与结构化抽取层
├─ Simhash 近重复聚类
├─ 规则化事件抽取
├─ 数值信息抽取
└─ 标准专题 Schema 映射

NLP 分析层
├─ 相关性分类
├─ 细粒度事件分类
├─ 情绪/语气分类
├─ 向量检索
└─ 主题建模

地理归一层
├─ 行政区地名识别
├─ 标题+正文地点融合
├─ 弱地理线索解析
└─ GIS 输出接口

存储层
├─ SQLAlchemy
├─ SQLite 默认实现
└─ PostgreSQL 配置兼容接口

分析输出层
├─ 时间趋势统计
├─ 地区分布统计
├─ 来源结构统计
├─ 高影响案例识别
├─ 主题演化数据输出
└─ 日报/周报 Markdown 输出

可视化层
└─ Streamlit 面板
   ├─ 采集状态
   ├─ 关键词检索
   ├─ 语义检索
   ├─ 时间趋势
   ├─ 地区分布
   ├─ 主题聚类
   ├─ 典型文本
   ├─ 高影响案例
   └─ 地图聚合结果预览
```

## 2. 完整目录结构

```text
见项目目录，采用 `src/` 布局，核心目录包括 `collectors/`、`cleaners/`、`extractors/`、`nlp/`、`geo/`、`storage/`、`analytics/` 与 `dashboards/`。
```

## 3. 模块说明

### `config.py`
- 作用：统一加载应用、数据源、模型配置。
- 输入：`configs/*.yaml` 和环境变量。
- 输出：结构化 Pydantic 配置对象。
- 依赖：`pydantic`、`pyyaml`。

### `collectors/base.py`
- 作用：定义采集器抽象基类与统一请求行为。
- 输入：站点配置、公开网页 URL。
- 输出：标准化 `EcoDocument`。
- 依赖：`httpx`、`tenacity`、`robots.txt`、清洗模块。

### `extractors/event_extractor.py`
- 作用：抽取生态破坏行为、执法整改、数值实体。
- 输入：清洗后的中文文本。
- 输出：关键词、数值表达、企业/项目名、专题布尔标记。
- 依赖：`re`。

### `geo/normalizer.py`
- 作用：行政区与弱地理线索归一。
- 输入：标题、正文。
- 输出：省、市、区县、归一地名列表。

### `analytics/reporting.py`
- 作用：统计分析、高影响案例筛选、主题演化数据生成、Markdown 报告生成。
- 输入：数据库文档记录。
- 输出：分析表、聚合结果、报告文本。

## 4. 安装方式

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
```

可选增强依赖：

```bash
pip install -e .[dynamic,ml,dev]
```

## 5. 初始化数据库

```bash
eco-monitor init-db
```

## 6. 导入配置

1. 复制环境变量模板：

```bash
copy .env.example .env
```

2. 编辑：
- `configs/app.yaml`
- `configs/sources.example.yaml`
- `configs/models.example.yaml`

3. 将需要启用的公开数据源改为 `enabled: true`。

## 7. 执行采集

```bash
eco-monitor collect
```

公众号仅支持授权导入：

```bash
eco-monitor import-wechat authorized_articles.json
```

## 8. 执行分析

```bash
eco-monitor analyze
```

## 9. 启动面板

```bash
streamlit run src/eco_damage_monitor/dashboards/streamlit_app.py
```

## 10. 生成报告与导出

```bash
eco-monitor export
eco-monitor generate-report
```

## 11. 测试命令

```bash
pytest
```

## 12. Demo 数据快速跑通

```bash
eco-monitor init-db
eco-monitor seed-demo
eco-monitor analyze
eco-monitor generate-report
```

## 13. 合规声明

- 本项目只实现公开网页与授权导出数据的合规采集和导入。
- 采集前需遵守目标网站服务条款、robots 规则和访问频率限制。
- 不实现任何绕过登录、验证码、风控、付费墙、签名校验、JS 加密的功能。
- 不采集私人页面、非公开页面、受限页面。
- 公众号仅支持人工 URL 清单管理和授权导出数据导入。
- 所有采集、清洗、分析、导出过程应保留日志、配置和规则版本，便于审计与回溯。

## 14. MVP 已实现能力

- 可配置 CLI 与项目骨架
- 新闻 / 政府 / 论坛公开网页示例采集器
- 公众号授权导入模块
- HTML 清洗与中文分句
- Simhash 近重复聚类
- 规则事件抽取与数值识别
- 地名归一、主题分类、时间地区统计
- Streamlit 轻量面板

## 15. 增强版迭代计划

1. 增加 Playwright 与 Scrapy 兼容层。
2. 接入可配置中文 Transformer 做相关性复筛、零样本分类和 reranker。
3. 引入更完整的行政区划、保护区、河湖与矿区知识库。
4. 增加 PostgreSQL + pgvector、FastAPI 服务与任务调度。
