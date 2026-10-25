# sources/yinyi —— 人工音译语料（出处）

这里的 7 个 JSON 来自 Steam 创意工坊模组 **《泰拉瑞亚音译版》**
（TerrariaTransliteratedEdition）：

* 创意工坊页面：https://steamcommunity.com/sharedfiles/filedetails/?id=3824080213
* 作者：HoCha113
* 类型：tModLoader 模组（创意工坊 appid 1281930）
* 版本：2026.8.3.095
* 本地路径（订阅后）：`steamapps/workshop/content/1281930/3824080213/2026.8/TerrariaTransliteratedEdition.tmod`

`.tmod` 是 tModLoader 的容器格式（`TMOD` 头 + 20 字节哈希 + 256 字节签名 +
数据长度 + 名字/版本 + 文件表，文件体为 raw deflate），解包后取出
`Assets/Text/*.json`，即上面这些文件。模组里的 DLL 只做一件事：把
`LanguageManager` 里对应分类的字符串替换成这些 JSON 的内容。

## 与仓库的对应关系

| 语料 | 仓库文件 |
| --- | --- |
| Main.json | zh-Hans.json |
| Items.json | zh-Hans.Items.json |
| Game.json | zh-Hans.Game.json |
| NPCs.json | zh-Hans.NPCs.json |
| Projectiles.json | zh-Hans.Projectiles.json |
| Town.json | zh-Hans.Town.json |
| Legacy.json | zh-Hans.Legacy.json |

Mobile / PS4 / Switch / XBO 四份平台文案语料里没有，由 `tools/yinyi/translit.py`
按同一风格补全。

## 声明

语料版权归原作者 HoCha113 所有，此处仅用于非商业的免费汉化分支，并已在
根目录 README 与游戏内说明中署名。若原作者要求，可删除本目录并只保留
机器音译结果。
