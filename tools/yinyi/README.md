# tools/yinyi —— 音译版构建工具

把《泰拉瑞亚》的英文原文按**读音**转写成汉字（Cloud → 克劳德），用于生成
`yinyi-zh-translit` 分支上的 `zh-Hans*.json`。

## 组成

| 文件 | 作用 |
| --- | --- |
| `translit.py` | 音译引擎：英文单词 → 音节 → 汉字。保护 `{0}`、`[i:123]`、`{$Key}`、`<tag>`、URL 等富文本标记不参与转写 |
| `build.py` | 合并构建：人工语料优先，缺失的键用引擎补全，输出仓库根目录的 `zh-Hans*.json` |
| `overrides.json` | 人工覆写表（词级/短语级，键为小写），优先级最高，用来修机器翻译的翻车处 |
| `last-build-report.json` | 上一次构建的统计与 400 条样例，便于抽查（不提交） |

## 数据来源

1. `sources/yinyi/*.json` —— 人工音译语料（见该目录 README，来自 Steam 创意工坊模组）。
2. `backup_en/en-US*.json` —— 英文原文，同时是键的全集。
3. 仓库现有 `zh-Hans*.json` —— 键的全集（含少量英文文件里已删除的键）。

构建时先从「英文原文 ↔ 人工语料」里学出**词表**（约 3300 个单词）和**短语表**
（约 9900 条），机器补全时优先查这两张表，所以同一个专有名词在全文里读音一致，
实在查不到才走 `translit.py` 的拼写规则。

## 用法

```bash
python tools/yinyi/build.py
```

会就地重写仓库根目录的 11 个 `zh-Hans*.json`。样例与统计见
`tools/yinyi/last-build-report.json`。

## 想改某条翻译？

* 改一处：在 `overrides.json` 里加 `"英文原文(小写)": "想要的音译"`，重跑构建。
* 改整批：直接编辑 `sources/yinyi/*.json`（结构与游戏语言文件一致，按分类嵌套）。
* 改规则：调 `translit.py` 里的 `CV` / `CODA` / `SUFFIX` / `VOWEL_GROUP` 表。

## 字体

引擎只输出常用汉字，且都落在 `backup_config/config.bmfc` 的字符集内，因此不需要
重新生成 `Font/` 下的位图字体，直接走主构建流水线即可。
