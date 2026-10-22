# 模块职责与接口

## 数据流

文字 Assist（首阶段）或麦克风 → STT → Conversation Agent → 两个业务脚本 → Music Assistant → 播放器。文字回答可由 Piper 播报；TTS 输出终端与音乐播放器独立配置，不能假定 HEOS 自动接收 Assist 回答。

| 模块 | 输入 / 输出 | 边界 |
|---|---|---|
| STT | 音频 → 文本 | 不执行业务；Whisper 可放远端或替换，不阻塞文字模式 |
| DeepSeek Conversation | 文本 → 工具参数、回复 | 需集成支持 HA Assist API 和工具调用；提示词不能代替执行权限 |
| `household_music_player_config` | room → players、目标实体、收藏按钮 | 唯一房间白名单；无效房间失败；内部工具不直接暴露 |
| `bedroom_search_and_play` | query、room、artist、randomize、allow_versions、search_only、volume_percent、sleep_minutes | MA 搜索、筛选、替换队列、有限恢复；旧 bedroom ID 保留兼容多房间 |
| `bedroom_music_tools` | operation、room、minutes、volume_percent | 状态、控制、收藏、默认房间与睡眠入口 |
| `household_music_sleep_scheduler` | set/cancel/status/tick | `todo.family_music_sleep` 持久存截止时间；串行处理；内部使用 |
| 公共睡眠巡检 | 每 15 秒 / HA 启动 → tick | 到期暂停确认后完成条目；离线恢复补执行，非精准实时定时器 |
| MA / lx_server | 搜索、URI、队列与音源 | 源优先级由源服务管理，HA 尚未实现比例路由 |
| `input_select.music_last_room` | 最近成功操作房间 | 全家共享；手工媒体卡操作不会自动更新 |

## 工具契约

以 package 的 `fields` 与真实响应为准。音量参数为 0–100，内部转为 0–1；睡眠分钟为 1–480。`room=自动` 使用最近有效房间，无缓存回退配置首项。搜索空结果、执行失败、尚在缓冲必须分别回复，只有实际确认的部分才能报告成功。

搜索脚本只查找时不播放、不更新默认房间。播放会替换队列并解除静音，可能改变音量和循环；现场测试需留意这些副作用。当前连续 playing 确认值为 3 秒，三阶段等待 20/15/15 秒；HA 状态不能证明音箱实际有声音。完整细节见迁移包说明。

## 配置来源优先级

1. 实际 HA/MA 实体、动作 schema 和轨迹决定现场事实。
2. 版本控制中的 `迁移配置包/` 决定本工程的部署基线。
3. `部署准备/` 单文件是 UI 安装参考；业务修改后若仍维护 UI 安装，必须同步对应脚本和提示词，不能混用不同版本。
4. 根目录中文文档保留演进历史，旧 timer、单房间或旧实体说明不覆盖当前迁移包。

不导入整个部署准备目录。内含上游代码快照和旧脚本，不是 HA packages 目录。第三方快照保留原许可证，不把它作为本工程新代码目录。

## 官方参考

- [HA packages](https://www.home-assistant.io/docs/configuration/packages/)
- [Wyoming](https://www.home-assistant.io/integrations/wyoming/)
- [Assist](https://www.home-assistant.io/voice_control/)
- [DeepSeek 集成上游](https://github.com/leofleischmann/Homeassistant-Deepseek-Integration)
