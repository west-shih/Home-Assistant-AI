# 开发、运行与回滚

## 准备

使用现有 HAOS 和 MA，先确认 MA 能直接驱动一个真实音箱。旧记录 Core 2026.9.4、DeepSeek 集成 1.8.4 只说明历史环境，不构成当前兼容性保证。填写 `config/environment.example.yaml` 的本地副本，记录实际版本。不要把清单作为 HA 配置导入。

```bash
mkdir -p local/packages
cp 迁移配置包/family_music.yaml local/packages/family_music.yaml
cp 迁移配置包/DeepSeek中文提示词.txt local/DeepSeek中文提示词.txt
cp config/environment.example.yaml local/environment.yaml
```

手动编辑部署副本：播放器配置脚本首步 `players`（至少一个）；搜索使用的 `REPLACE_WITH_MA_CONFIG_ENTRY_ID`；固定宝宝音频 `REPLACE_WITH_BABY_TRACK_URI`（package 和提示词均替换为 MA 真实 URI）。配置条目 ID 可在 HA 开发者工具动作 `music_assistant.search` 选择集成后查看 YAML。房间名称不从实体 ID 的 l/r 推断。

## 安装到 HA

1. 备份现有 HA 配置及代理提示词；记录同名 UI 脚本、helper、自动化是否存在。不要在同 ID 的 UI 定义仍加载时再安装 package，否则会冲突或产生 `_2`。已有实例优先沿用原 UI 方式，逐项更新，或备份后明确迁移到 package。
2. 通过 Local To-do 集成创建专用 `todo.family_music_sleep`，不可混用购物清单。MA 集成和播放器先接好。
3. 把编辑后的 package 放到 HA `/config/packages/family_music.yaml`。按示例合并 `homeassistant.packages` 到现有 `configuration.yaml`，保留其他配置。
4. 本地执行 `python scripts/validate_config.py local/packages/family_music.yaml --deploy`。到 HA 开发者工具 → YAML 做配置检查；HAOS CLI 也可用 `ha core check`。失败时先修复，再重启。
5. 确认四个脚本、默认房间 helper 和巡检自动化存在；首先调用下面只读业务操作。注意播放器解析可能初始化 helper 选项。

```yaml
action: script.bedroom_music_tools
data:
  operation: status
  room: 卧室
```

再按路线文档手工验收播放。动作示例可粘贴到开发者工具，但必须先修改实际房间名称。

```yaml
action: script.bedroom_search_and_play
data:
  query: 轻音乐
  room: 卧室
  search_only: true
```

6. 配置能调用 HA 工具的 DeepSeek Conversation 集成；凭据填集成 UI。选择支持工具调用的模型、启用 HA Assist API，导入部署副本提示词，仅暴露两个业务脚本。配置/调度脚本和内部 todo 不向 Assist 暴露；检查自动暴露新实体设置。先验收文字 Assist 的工具轨迹。
7. 最后选用 STT/TTS 并绑定 Assist 管线；Piper 与 Whisper/其他 STT 可独立替换。手机键盘听写只用于获得文字，不等于已完成 Assist 音频管线接入。远程 Wyoming 服务还需网络可达与延迟验收。

## 每次修改

从短分支提交，优先修改迁移包基线及配套提示词，更新接口文档与验收记录。旧实体 ID 不随意改名；若需要改必须说明调用者迁移。部署准备的 UI 副本若继续维护，应在同次修改中同步。上游 DeepSeek 代码优先通过 HACS 管理，仓库中 1.8.4 仅为参考快照，升级先核对上游变更和本地修改。

离线校验仅检查本工程 package 和配置样例，不运行上游全套测试，也不假装验证真实设备。`--deploy` 只说明结构和占位符检查通过，仍需 HA 配置检查和运行验收。

## 回滚与记录

恢复修改前的 package / UI YAML、helper 定义和代理提示词，配置检查后重启。不要同时启用新巡检与旧 timer.finished 自动化。睡眠 todo 是运行数据，回滚前查询待执行计划，决定保留还是显式取消；只恢复代码不会自动取消已保存计划。当前方案恢复后会处理逾期任务，可能暂停新播放。

每次验收记录日期、HA/MA/集成版本、提交 SHA、输入、工具参数、目标房间、实际状态/听感、STT/LLM/执行/TTS 分段耗时、失败和回退结果。记录去除令牌、密钥和个人数据。密钥存 HA 集成 UI 或 `secrets.yaml`；本地副本放忽略的 `local/`。`.gitignore` 不会移除过去已经提交的信息。
