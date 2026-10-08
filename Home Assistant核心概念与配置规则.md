# Home Assistant 核心概念与配置规则

更新：2026-10-02。本说明用家庭语音控制场景解释 HA 对象关系，以及播放器和 LLM 的配置边界。菜单名称可能随 HA 版本略有变化。

## 1. HA 中“设备”与“实体”是什么

可以把 HA 想成一层统一控制目录：集成连接外部系统，设备表示一个物理或逻辑设备，实体表示可读取或操作的一个具体功能。

```text
集成 Integration → 设备 Device → 实体 Entity → 状态 / 动作
```

例如 Music Assistant 集成连接 MA 服务；一个卧室音箱设备可以提供 `media_player.*` 播放器实体。某个设备也可能提供多个实体，例如播放器、音量或电源开关。

| 概念 | 含义 | 本项目例子 |
|---|---|---|
| 集成 Integration | HA 与设备/服务之间的适配层 | Music Assistant、HEOS、Wyoming |
| 设备 Device | 集成识别到的物理或逻辑设备 | 卧室音箱、浏览器播放器（若集成有识别） |
| 实体 Entity | HA 中可读取状态或执行操作的对象；有唯一 entity_id | `media_player.<名称>` |
| Area 区域 | 设备所在房间的组织标签 | 卧室 |
| Action / Service 动作 | 对实体执行的命令 | `media_player.media_pause`、`music_assistant.search` |
| 自动化 Automation | 事件/条件满足后按步骤执行的流程 | 旧的固定句式自动化 |
| 脚本 Script | 可复用的一组动作；可以由自动化、用户或支持工具调用的 LLM 触发 | 搜索并播放音乐 |
| Assist Pipeline | 语音输入、STT、对话代理、TTS 的流水线 | 手机麦克风 → STT → LLM → Piper |
| Conversation Agent | 理解用户文本、决定回答或调用工具的代理 | HA 内置代理或 LLM 代理 |
| Intent | 结构化的用户意图，例如控制某个实体 | 内置语句匹配或集成注册的意图 |

**实体是控制时最关键的对象。** 设备卡片或网页播放器能显示出来，不代表它一定能被 HA 控制；需要检查实体页是否存在可执行的动作及设备支持的功能。

## 2. `media_player` 是不是通用播放器接口？

是一个统一的控制接口，但不是每个播放器都实现所有能力。常见标准动作包括：

- 播放/暂停/停止：`media_player.media_play`、`media_player.media_pause`、`media_player.media_stop`
- 上一首/下一首：`media_player.media_previous_track`、`media_player.media_next_track`
- 音量/静音：`media_player.volume_set`、`media_player.volume_up`、`media_player.volume_down`、`media_player.volume_mute`
- 播放指定媒体：`media_player.play_media`
- 电源与播放源：`media_player.turn_on`、`media_player.turn_off`、`media_player.select_source`

调用动作前要确认目标实体支持对应功能。某些集成不支持音量、队列、搜索或暂停；同名标准动作会由集成翻译为具体设备命令。

### MA 与 HA 播放器的关系

- 在 HA 添加 **Music Assistant 集成**：MA 支持的播放器作为 HA `media_player` 实体出现，可供仪表盘、自动化、脚本和 Assist 使用。
- HA 标准播放器动作适合播放/暂停/音量等通用控制。
- MA 专用动作适合跨音乐源搜索、取得搜索结果、控制 MA 队列及播放 MA URI。
- 因此本项目把搜索和选曲交给 MA，把命令理解与安全校验交给 LLM/HA 脚本。

## 3. 浏览器 Web 播放器何时能控制

判断路径：

1. 在 HA“设置 → 设备与服务 → 实体”过滤 `media_player`，搜索“浏览器”或 MA 中的播放器名。
2. 如果 HA 有对应的 `media_player.*`，确认其集成来源、在线状态以及该实体实际支持的动作。
3. 如果 HA 没有实体，检查 MA 的播放器列表中该浏览器客户端是否作为可选输出 player 注册。若 MA 能识别，可研究通过 `music_assistant.play_media` 将播放指定到 MA player；若它只是打开了一个 MA 网页界面，则不自动成为 HA 媒体实体。
4. 对语音工具只暴露确认可用的播放器。目前以用户确认的“卧室”为唯一可靠目标。不要让 LLM猜测浏览器名称或未验证的实体。

本项目待记录：HA 中“卧室”的 entity_id、集成来源、支持功能；浏览器 Web player 在 HA 与 MA 的实际状态。

## 4. Assist 语音链路的各层规则

```text
音频输入
  → STT：语音变文字
  → Conversation Agent：理解文字、选择工具
  → HA 实体 / 脚本 / 集成动作：执行
  → TTS：把答复变成语音
```

- STT 只转写，不理解命令。当前 HA 内 Whisper 延迟与识别体验很差，用户决定不再将其作为主力。
- LLM Conversation Agent 处理开放式自然语言，并按提示/工具说明生成动作参数。LLM 本身不接收音频，前面仍需 STT。
- TTS 只负责播报。Piper 可暂时保留；它与 STT、LLM 分工独立。
- Assist 的实体暴露是访问控制。只暴露 LLM 需要控制或查询的实体，避免把所有 HA 设备都交给模型。
- 对 LLM，更推荐把脚本设计成有明确名称、描述、字段和边界的工具；清晰描述决定模型何时调用脚本。

## 5. 本项目的配置约定

### 5.1 实体命名与区域

- 将稳定播放器归入 HA 的“卧室”区域。
- 保留平台生成的 `entity_id`，文档同时记录友好名称、实体 ID、集成来源。
- 如果只有一个可靠播放器，首版工具可固定其 entity_id。待多个稳定播放器存在后，再增加 `area` 或 `player` 参数。
- 不要用设备名称猜实体 ID；在 HA 实体页核对。

### 5.2 LLM 可用的音乐工具

首版建议只开放：

| 工具 | 参数 | 行为 |
|---|---|---|
| `search_and_play_bedroom` | `query`：自然语言搜索内容 | 调 MA 搜索，按定义的结果选择规则将结果在卧室播放 |
| `set_bedroom_volume` | `volume`：约定 0–1 | 校验范围后调播放器音量 |
| `pause_bedroom` | 无 | 暂停卧室播放器 |
| `resume_bedroom` | 无 | 继续播放 |
| `next_bedroom_track` | 无 | 下一首 |
| `stop_bedroom` | 无 | 停止播放 |

实现细节：优先复用当前已验证的 MA 搜索与播放方式。工具描述应说明何时用、必需参数、搜索结果为空/服务失败时如何回复。不同意图只执行所需动作；例如“放点五月天，音量小一点”先设置有明确数值的音量，或在没有可推导目标时追问/采用已定义规则，不要默默猜一个数值。

HA 原生媒体动作与 MA 专用动作可以并存：通用传输控制优先使用 `media_player` 标准动作；音乐搜索和 MA 搜索结果播放使用 MA 动作。

### 5.3 秘密与安全

- LLM Key、HA 长期令牌、账号密码不写入脚本注释、文档、仓库或聊天转发内容。
- 在 HA 集成配置或 `secrets.yaml` 中保存秘密，并避免把秘密复制进诊断日志。
- LLM 只能得到当前任务所需的有限脚本/工具；不得把任意服务调用、管理配置或解锁等高风险操作无条件开放。

## 6. 配置与核对流程

1. **找播放器实体**：HA → 设置 → 设备与服务 → 实体 → 过滤 `media_player`。
2. **确认集成和设备**：点开“卧室”，记下 entity_id、集成来源、面积/区域、能力和当前状态。
3. **测试一项动作**：在开发者工具 → 动作中对该实体做暂停/恢复/音量测试；先选低影响操作，实际播放测试留意会改变队列。
4. **找 MA 浏览器输出**：在 MA Players 页面确认 browser player 是否在线、名字及类型；再确认它是否同步出现在 HA 实体列表。
5. **整理可复用脚本**：新建并单独测试搜索播放、音量、暂停、继续、下一首、停止脚本；保留旧自动化。
6. **连接 LLM 对话代理**：确认所选集成能够在该 HA 版本作为 Conversation Agent 工作，并能调用暴露的脚本/工具。先用文字 Assist 检查工具调用轨迹。
7. **配置语音输入**：选择手机系统 STT 或可用的 STT provider 替换 Whisper；确认文字 Assist 成功后再测语音链路。
8. **记录结果**：记录调用工具、参数、目标 entity_id、执行结果和耗时。

## 7. 常见误解

- **“HA 里看见了设备，就肯定能控制。”** 设备可能没有控制实体，或实体只提供有限功能。
- **“所有播放器都支持完全相同的功能。”** `media_player` 统一动作名称，但可用能力取决于集成/播放器。
- **“LLM 可以直接听语音。”** Assist 中 LLM 通常接收 STT 输出的文本；语音仍需要 STT。
- **“HA 只能靠固定句式。”** 内置代理侧重意图与句式；配置为 Conversation Agent 的 LLM 可以按自然语言调用有限工具，具体能力取决于集成及工具暴露。
- **“播放某个歌名就只靠 media_player 标准接口。”** 通用接口可接受指定媒体，但跨源搜索、挑结果和 MA 队列属于 MA 更专门的能力。

## 8. 官方参考

- [HA Assist](https://www.home-assistant.io/voice_control/)
- [HA 媒体播放器标准动作](https://www.home-assistant.io/integrations/media_player/)
- [HA 向 Assist 暴露实体](https://www.home-assistant.io/voice_control/voice_remote_expose_devices/)
- [HA Assist 最佳实践](https://www.home-assistant.io/voice_control/best_practices/)
- [HA 设备与实体架构](https://developers.home-assistant.io/docs/architecture/devices-and-services/)
- [Music Assistant HA 集成](https://www.music-assistant.io/integration/installation/)
- [Music Assistant 与 HA 组件关系](https://www.music-assistant.io/integration/)

## 2026-10-02 实际配置示例：卧室

已直接检查 HA：显示名“卧室”、实体 ID `media_player.wo_shi_r`、设备名“卧室-R”、设备型号 Denon Home 150 NV、集成 Music Assistant。这说明显示名、设备名和 entity_id 是不同字段，改显示名无需更改旧自动化引用。Assist 已公开该实体，当前可直接复用它作为首版音乐工具的固定目标。

HA 当前没有脚本，也没有 LLM Conversation Agent。中文音乐助手仍是内置 Home Assistant 对话代理，STT 仍为 faster-whisper。详细实况及完整音乐自动化 YAML 见项目的技术方案、应用配置说明和历史参考目录。

## 2026-10-03：脚本作为 LLM 音乐工具的实际例子

已新增 `script.bedroom_search_and_play`（显示名“卧室音乐搜索播放”）并公开给 Assist；必需字段 query 是音乐搜索词。对话代理已切换为 DeepSeek Conversation，配置 Home Assistant API。由 LLM 理解口语并调用工具，脚本负责可复用的 MA 搜索和固定卧室播放流程。暂停等标准媒体操作交给 HA 媒体工具。实体公开和字段说明是工具配置的一部分，提示词本身不能代替工具执行能力；运行效果仍需验收。


## 2026-10-04：显示名称与实体ID变化实例
原media_player.wo_shi_r现显示为一楼；media_player.wo_shi_l现显示为卧室。实体ID中的l/r不再表示实际房间位置，必须核对当前显示名与实体映射。已将脚本改为room参数加白名单映射，播放、音量、收藏与独立计时器统一路由。详细配置见技术方案和应用配置说明的多播放器兼容章节。
