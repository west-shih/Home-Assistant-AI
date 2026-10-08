# 家庭音乐完整迁移配置（2026-10-04：公共睡眠调度版）

本文件描述当前版本，替代旧架构。项目根目录MD按时间追加保留历史，以本文和迁移包为当前配置。此包覆盖家庭语音音乐功能，不是HA/MA/lx_server整机备份，不包含密钥。

## 唯一播放器维护入口

打开HA脚本“家庭音乐播放器配置”（script.household_music_player_config），只修改sequence第一步players：

~~~yaml
players:
  卧室: media_player.wo_shi_l
  一楼: media_player.wo_shi_r
  # 书房: media_player.your_study_player
~~~

新增播放器先在HA/MA接入，然后仅增加名称和媒体实体一行。无需新建timer、登记收藏按钮、修改默认列表、其他脚本、自动化或提示词。配置至少保留一项；每台播放器建议只登记一个名称。名称改变不会丢失该媒体实体的睡眠计划，实体改变视为新设备，旧实体计划在巡检时取消。

- 默认播放器input_select.music_last_room选项自动按players同步；缓存名称若仍存在则保留，否则回退首项。
- 收藏从目标播放器所属HA设备的按钮实体查找favorite_current_song结尾的MA按钮。只有唯一匹配才使用；无匹配/多匹配/不可用时提示不支持，不影响播放和睡眠。不按其他设备猜按钮。
- 睡眠计划按播放器entity_id存储在一份本地待办列表中，不再为每台设备创建timer。

## 当前文件和实体

| 文件/实体 | 作用 |
|---|---|
| family_music.yaml | HA package，四个脚本、默认播放器helper、一个巡检自动化 |
| DeepSeek中文提示词.txt | 对话代理完整指令 |
| script.household_music_player_config | 唯一播放器列表和收藏识别入口 |
| script.household_music_sleep_scheduler | 公共睡眠存储与调度，内部调用，不需暴露给LLM |
| script.bedroom_search_and_play | 显示名家庭音乐搜索播放；保留旧ID兼容 |
| script.bedroom_music_tools | 显示名家庭音乐辅助控制；保留旧ID兼容 |
| input_select.music_last_room | 家庭音乐默认播放器，保存最近语音/脚本成功操作房间 |
| todo.family_music_sleep | 家庭音乐睡眠计划，由Local To-do集成创建；初次安装创建一次 |
| 家庭音乐公共睡眠巡检 | 每15秒和HA启动时巡检未完成计划 |

旧timer.bedroom_l_music_sleep与timer.bedroom_music_sleep在当前实例已停用，迁移包不包含它们。原睡眠自动化1791080661007已原位改为公共巡检，旧timer.finished流程不再使用。切换时两旧timer均空闲，无需迁移进行中的计划。

## 安装到新HA

1. 安装并配置Music Assistant集成，先确认各真实播放器已经接入；基础接入属于一次性的设备工作。
2. 添加Local To-do集成，清单名先用Family Music Sleep，使实体成为todo.family_music_sleep；再把显示名称改为家庭音乐睡眠计划。若ID不同，手动在实体设置改为上述ID。该清单只用于内部计划，不混入购物事项、不直接暴露给LLM。
3. 修改package的household_music_player_config.players为新实例名称和播放器实体。这里只需播放器映射，无timer/favorite字段。
4. 替换REPLACE_WITH_MA_CONFIG_ENTRY_ID为新HA Music Assistant配置条目ID。开发者工具→动作→music_assistant.search选择集成，然后查看YAML中的config_entry_id。
5. 导入宝宝本地音频，在MA歌曲详情→提供程序详细信息复制真实URI。将package和提示词中的REPLACE_WITH_BABY_TRACK_URI替换为此URI，不使用网页链接。
6. 将family_music.yaml放到/config/packages/，合并下列packages设置到现有configuration.yaml，不重复homeassistant键。由用户执行HA配置检查再重启。

~~~yaml
homeassistant:
  packages: !include_dir_named packages
~~~

7. 核对表中四个脚本和helper实体ID。若同名UI脚本/helper已存在，选择沿用UI方式或package方式，不同时创建重复实体导致_2后缀。
8. 通过HACS安装并配置DeepSeek集成（当前实例1.8.4），使用自己的API Key；启用Assist API，在对话代理粘贴配套提示词。音乐语音助手选择该代理，关闭优先本地处理。将两个业务脚本暴露给Assist，集中配置和调度脚本仅由业务脚本内部调用。
9. 新实例选择合适中文STT/TTS；当前旧Whisper性能问题尚未替换，迁移包不负责STT性能。

UI安装方式：创建一次Local To-do与默认播放器下拉helper；分别从部署准备粘贴四个家庭音乐脚本及公共巡检自动化。确保实体ID按上表固定，中文名称自动生成的ID可能不同，可先用对应英文名称创建后再更改显示名称或直接编辑ID。不要同时导入package重复定义。

## 完整已实现行为

- 最近播放器跨对话持久保存；未指定room时传自动，明确名称覆盖。播放确认后、成功控制/收藏/定时后更新；状态查询和仅搜索不更新。全家共享一个最近名称，手动MA/HA媒体卡操作暂不更新缓存。
- 音乐播放先搜索再替换队列、解除静音、恢复播放、等待playing；失败按真实情况说明。可组合volume_percent、sleep_minutes；只搜索没有上述副作用。
- 指定歌手按artists[].name匹配本人，允许包含该歌手的合唱；泛听筛选最多20条搜索歌曲，随机排列多首；精确点歌选择匹配首条。歌手别名/繁简差异可能无结果，元数据可能有误。
- 默认过滤明显特殊版本和DJ/JD、魔改、加减速、变调、串烧、车载重低音、混音等标签；明确要求可放开。电子/舞曲本身不排除。风格随机合格歌单；歌单内部未逐首筛查，未标记的改编仍可能出现。跨次随机不保证不重复。
- 宝宝白噪音/宝宝催眠曲/宝宝睡眠曲指向固定本地音频，默认12%音量（明确可覆盖）、repeat=one。普通音乐repeat=off。睡眠计划按用户要求添加，不擅自加默认时长。
- 辅助工具operation：sleep、cancel_sleep、status、favorite、pause、play、next、previous、volume、mute、unmute、select_room。sleep需要minutes=1到480；volume需要volume_percent=0到100；select_room只更改默认播放器。
- 收藏发送MA按钮请求，不保证同步第三方音乐账号；收藏按钮自动发现依赖HA设备关联和标准MA实体命名，无法识别时该播放器仅不支持收藏。

## 公共睡眠计划的规则

专用本地todo清单中，每个未完成条目summary为媒体实体，due为带时区截止时间。调度脚本mode=queued串行处理set/cancel/status/tick，避免脚本调用互相覆盖。重新设置更新同实体截止时间，额外重复项标记完成；取消仅将该实体计划标记完成，不暂停。完成的计划保留历史，不自动永久删除。

每15秒检查待执行条目；HA启动后/恢复运行时处理已逾期计划。到期调用media_pause，确认paused/idle/off后标记完成；播放器unknown/unavailable或暂停未确认时保留，下一次重试。HA离线时无法执行，恢复后会补处理；可能在设备恢复后暂停此时正在播放的音乐，这是逾期计划的预期行为，可显式取消计划避免。正常延迟约0到15秒，多设备等待/服务故障可能更久。

被从players移除的媒体实体，其计划在巡检时标记完成，不继续控制移除设备。清单内容由程序维护；手工更改截止时间会影响执行，标记完成等于取消。

首次安装只建一个todo和一个input_select。以后新增设备只改players；不再新增辅助元素或计时器。清单不是helper列表中的Timer类型，可在HA待办列表页面查看。

## 音源方案尚未实施

wy≈40%、tx≈30%、mg≈20%、kw≈10%，kg兜底仍是待办。当前由用户的lx_server tx优先决定来源，HA脚本没有按源权重调度。需先确认提供程序/lx_server可按请求指定源；预期每次选一源搜索，合格即用，失败再换源，不同时搜五源，不为比例重搜已知URI。

## 保存与验收状态

本次已确认UI保存、todo实体创建、旧计时器空闲后停用；未主动运行音乐或定时测试。用户此前确认过音乐闭环可用，不能将新配置保存成功等同于新调度已完成运行验收。建议用户验证两个播放器独立定时、取消不暂停、重启后保留、收藏、宝宝音量/循环以及无房间命令沿用缓存。

## 环境与备份

HA http://192.168.5.20/；MA http://192.168.5.12:8095/；iStore192.168.5.6；当前Core2026.9.4。原始当前配置在部署准备，修改前备份在历史参考/公共调度前_*。密码和API Key不写入迁移包。当前本地宝宝音频library://track/208，迁移时ID通常不同。


## 2026-10-04：切歌稳定确认与有限自动恢复

读取已有轨迹：18:22:51的一次播放2.76秒返回成功，时间线随后出现media_player.wo_shi_r空闲和播放变化。该记录不能证明音源是唯一原因，但暴露旧逻辑只检查瞬间playing。

搜索播放现在同一队列最多三阶段等待20/15/15秒，若playing则检查连续6秒不离开；paused/idle/off时尝试media_play，buffering只等待。未稳定则下一阶段继续，最多约68秒，不含MAplay_media本身耗时。恢复不重复搜索、不替换队列、不换成其他歌曲，保留随机/歌手/白噪音等原选择。成功返回stable_seconds和recovery_attempts；仍buffering返回loading=true和success=false，代理不把它说成无搜索结果，也不重复下搜索。

边界：服务调用本身阻塞/报错、设备断线、来源不可用或播放后较晚中断仍需排查；状态playing不是实际声音证明。当前三阶段等待不是持续后台监控。睡眠定时在稳定确认之后才设置。已保存UI与代理，备份实际原YAML；未主动播放测试，迁移配置包同步。


## 2026-10-04：稳定播放确认改为3秒

按用户要求，连续playing确认由6秒改为3秒，返回stable_seconds=3。20/15/15秒阶段等待保持，最长约59秒（不含MA服务耗时）。脚本、提示词及迁移包同步保存，未主动播放测试。
