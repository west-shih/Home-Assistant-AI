# Home Assistant AI

家庭中文语音与音乐控制的配置工程：由 Home Assistant 执行动作，DeepSeek 理解自然语言，Music Assistant 管理音源、队列和播放器，STT/TTS 分别负责听写和播报。

## 当前基线与边界

仓库初始提交并非空项目，已包含多房间搜索播放、歌手/版本过滤、最近房间记忆、收藏、宝宝本地白噪音和持久睡眠计划。当前可部署基线是 [迁移配置包](迁移配置包/README.md)，原有文件全部保留。

这些能力来自截至 2026-10-04 的配置记录；保存过配置不代表已完成运行验收，本次也未连接家中 HA 或操作音箱。历史记录中的 IP、版本、房间名不代表当前现场。`卧室 → media_player.wo_shi_l`、`一楼 → media_player.wo_shi_r` 仅为旧映射，请现场核对。

首阶段范围是文字 Assist → DeepSeek → HA 音乐脚本 → MA → 已确认播放器。语音输入在文字闭环稳定后接入；旧 HA 内 Whisper 性能不佳，不作为必选默认。Piper 可独立保留。当前不新增 Java 网关、不重写第三方集成、不部署全套 HA/MA、不承诺闽南语识别或音源权重路由已经实现。

## 项目结构

| 路径 | 职责与维护规则 |
|---|---|
| `迁移配置包/family_music.yaml` | 当前 HA package 唯一部署基线；业务改动优先落在这里 |
| `迁移配置包/DeepSeek中文提示词.txt` | 配套代理指令，与脚本接口同步 |
| `config/` | HA 引入配置、环境核对清单示例；不存真实秘密 |
| `docs/architecture.md` | 模块职责、数据流、接口和来源优先级 |
| `docs/development.md` | 安装、校验、升级、回滚和第三方代码维护 |
| `docs/roadmap.md` | 实施顺序与每阶段验收条件 |
| `scripts/validate_config.py` | 离线 YAML、内部脚本引用、模板占位符检查 |
| `部署准备/` | 现有 UI 单文件配置和第三方 DeepSeek 1.8.4 快照；不是第二套自动部署入口 |
| 根目录三份中文说明 | 既有概念、配置过程、进度历史，按日期阅读 |

运行环境仍为 HAOS + 现有 MA 服务；本仓库是配置工程，不需要启动一个新的后端服务。未来确有独立服务需求再新增模块。

## 最短开始路径

1. 阅读 [开发与安装](docs/development.md)，备份现场脚本、自动化、helper 和代理指令。
2. 核对 MA 播放器实体，创建专用 Local To-do `todo.family_music_sleep`。
3. 复制 `迁移配置包/family_music.yaml` 到本地忽略目录 `local/packages/family_music.yaml`，修改首个 `players` 映射及两个 `REPLACE_WITH_*` 占位符。提示词另复制到 `local/` 并替换音频 URI。
4. 按 `config/configuration.example.yaml` 合并 packages 设置，上传配置到 HA；不要同时导入已有同 ID 的 UI 脚本。
5. HA 配置检查通过后重启；先手工调用状态查询，再验收搜索、播放和定时，最后配置 DeepSeek 与语音管线。

离线检查（Python 3.10+）：

```bash
python -m pip install -r requirements-dev.txt
python scripts/validate_config.py
python scripts/validate_config.py local/packages/family_music.yaml --deploy
```

第一条检查允许分发模板保留占位符；`--deploy` 检查部署副本必须完成替换。它不验证 HA schema、Jinja 执行或真实音乐服务。完整安装和回滚见开发文档。

## 后续路线

先固化部署和文字工具验收，再接 STT/Piper，随后测试 ESPHome 语音终端与方言能力；音源权重、独立用户房间记忆和更强恢复能力后置。详细任务与通过条件见 [实施路线](docs/roadmap.md)。
