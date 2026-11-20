# LaRenderer 开场动画（Blender 4.5 / Cycles）

30 秒（900 帧，1920×1080，30 fps）的概念开场动画，风格为多巴胺配色 × Tactile 3D，片尾落版 **LaRenderer**。
动画只展示能力概念，不涉及模型结构。所有镜头由 Python 脚本从零搭建，结果确定、可复现。

> 本页以下各节是 **v1**（已交付、已冻结）的说明；按客户意见修改的 **v2**（32 秒）见文末「[v2 版本（32 秒）](#v2-版本32-秒)」。
> 所有脚本不加参数时仍是 v1 行为，加 `--film v2` 才处理 v2。

## 成片（`out/`）
| 文件 | 说明 |
|---|---|
| `LaRenderer_opening.mp4` | 带能力标签（左下角糖果胶囊字幕）的版本，H.264 yuv420p，BT.709 |
| `LaRenderer_opening_clean.mp4` | 无任何叠加层的纯净版，方便剪辑师自行加字 |
| `LaRenderer_opening_master.mov` / `LaRenderer_opening_clean_master.mov` | ProRes 422 HQ 10-bit 母版，供剪辑使用 |
| `cuts.png` | 四个剪辑点前后帧对照 |

逐帧素材：
- `renders/final/<镜头>/f_####.png`：16-bit 原始渲染；
- `renders/film_comp/`：合成字幕后的整片 16-bit 帧；
- `renders/film_comp_clean/`：不含字幕的整片 16-bit 帧。

## 分镜（120 BPM，每拍 15 帧，每小节 60 帧，所有剪辑点都落在小节线上）
| 镜头 | 时间 | 展示能力 | 内容 |
|---|---|---|---|
| S01 `s01_lights_world` | 0–8 s | 点光源 + 环境贴图任意旋转一致 | 夜色中的糖果日晷岛被一颗白色光球点亮；光球分裂为珊瑚/青柠/蓝三色光，三色功率之和为白光，单遮挡阴影因此呈柠檬黄、紫、青；光球升空化作环境图里的太阳；环境图按节拍转四个 90°（θ=360° 与 θ=0° 逐帧一致），再滑动、俯仰；镜面探针、天空地球仪、右上角经纬度小窗三处同步读出旋转 |
| S02 `s02_caustics` | 8–14 s | 焦散、玻璃、高反射材质 | 薄荷色珠宝盒房间；柠檬玻璃球、粉色玻璃心、青色玻璃环按节拍落下，各自绽放有色焦散；色散水晶兔投下彩虹焦散；铬旋涡与镜面球互相反射；最后推进镜面球 |
| S03 `s03_gummy` | 14–20 s | 几何动画、帧间连续 | 珊瑚色房间，青柠软糖兔落地挤压、回弹，0.2× 慢动作；滚动铬球撞击软糖；机位锁定，地面、墙镜、铬球中的反射与软糖形变逐帧同步 |
| S04 `s04_every_dot` | 20–26 s | 高分辨率纹理 | 柠檬色画廊，单镜头 46× 连续推进，从全景推到 20000 px 修拉《大碗岛》约 1:1 像素/纹素，画中一个白色笔触鼓起、化作光球 |
| S05 `s05_title` | 26–30 s | 片尾落版 | 光球接续 S04 的光点再次分裂，十个糖果字母按十六分音符依次落地；三色光在第 15 小节重拍合成一束白光，彩色阴影收拢成一道清晰阴影；上方六边形蜂巢回放前四章 |

## 配乐
目前没有声音。请配 120 BPM 的曲子，并把第一个强拍对齐到第 1 帧，所有动作和剪辑点都按这个节拍设计。

## 复现 / 修改
```bash
# 单镜头预览（只可使用 GPU 6/7；dopa 会拒绝其他 GPU）
CUDA_VISIBLE_DEVICES=6 tools/blender/blender -b --factory-startup -P shots/s03_gummy.py -- --mode preview --frames 1-180:10
# 全部终渲（GPU 6+7 队列，只补渲缺失的帧，可断点续渲；S05 自动最后渲染）
python3 scripts/render_finals.py
# 字幕叠加层 + 合成 + 编码（带字幕版、纯净版、ProRes 母版、剪辑点对照）
tools/venv/bin/python -I scripts/assemble.py --mode final --master
# 终渲质检（缺帧、闪帧、与预览逐块对比，以及分镜表第 7 节的回环/静止区/1:1 检查）
tools/venv/bin/python -I scripts/qa_finals.py
```
- `--slug` 会在右下角加一行小字 “Illustrative · rendered with Cycles”，默认关闭。
- 文档：`docs/brief.md`（需求与技术约定）、`docs/storyboard.md`（锁定分镜，含逐帧节拍表与 QA 标准）、`docs/lead_notes_r2.md`（第二轮修改意见）、`docs/reports/`（各镜头搭建与修改报告）。
- 代码：`lib/dopa.py`（风格工具包：调色板、材质、圆角几何、动画缓动、渲染入口）、`shots/`（每个镜头一个脚本）、`scripts/`（天空图生成、代理贴图、叠加层、合成、QA、终渲队列）。

## 素材与授权
- HDRI、材质贴图、glTF 模型：Poly Haven（CC0）。
- 斯坦福兔子、Spot 奶牛：公开研究模型。
- 修拉《大碗岛》20000 px 扫描：Wikimedia Commons（公有领域）。
- 梵高《麦田与柏树》：The Met Open Access（CC0）。
- 字体：Fredoka、Nunito 等（SIL OFL）。
- 详见 `assets/paintings/SOURCES.txt`。

## 说明
这段开场是用 Cycles 路径追踪渲染的概念动画，不是 LaRenderer 的输出。若需在片中注明，可用 `--slug`，或在开场之后接 LaRenderer 对相同场景的渲染结果。

## v2 版本（32 秒）

v2 = v1 + 客户的两条修改意见。完整规格见 `docs/storyboard_v2.md`（已锁定），镜头表见 `docs/shots_v2.json`。

### 改了什么
1. **新结尾：从一个场景拉远到很多场景的六边形蜂巢。** 结尾从画作内部开始，镜头连续拉远，原来这幅画只是蜂巢墙上的一格，墙上每一格都在播放一个场景（前几章的片段 + 12 个新的小场景，每个展示一种渲染现象）。拉远之后接 v1 的片尾标题，**LaRenderer 那几个字不变**：同样的十个糖果字母、材质、落地节奏、三色光在重拍合成白光、最终机位，字的大小和位置与 v1 一致，不加标语。
2. **画不再放大到那么大，框到主体即可。** S04 不再推到约 1 纹素/像素，而是停在《大碗岛》的主体上：撑橙色阳伞的女士和白衣小女孩，人物完整入画，点彩笔触仍然看得见，放大约 ×7。S04 不再有光点鼓出来、也没有光球。
3. **S04 的最后一帧和 S05 的第一帧是同一个画面**（无缝衔接），所以整段读作「推近主体（S04）→ 拉远到所有场景（结尾）」。

片长 32.0 秒 = 960 帧 = 16 小节（120 BPM，每拍 15 帧），剪辑点都在小节线上：

| 镜头 | 帧 | 时间 | 来源 |
|---|---|---|---|
| S01 `s01_lights_world` | 1–240 | 0–8 s | 复用 v1 终渲帧，不重渲 |
| S02 `s02_caustics` | 241–420 | 8–14 s | 复用 v1 终渲帧，不重渲 |
| S03 `s03_gummy` | 421–600 | 14–20 s | 复用 v1 终渲帧，不重渲 |
| S04 `s04_subject` | 601–780 | 20–26 s | 新镜头（`shots/s04_subject.py`）：推到画面主体，f150–180 静止 |
| S05 `s05_finale` | 781–960 | 26–32 s | 新镜头（`shots/s05_finale.py`）：蜂巢拉远 + 不变的标题，标题段比 v1 晚 60 帧 |

字幕：S01–S03 与 v1 完全相同；S04 的胶囊字幕 “High-res textures” 从第 616 帧出现，旁边的缩放读数取自 `renders/meta/s04_subject.json`（×1.0 → ×7.0，推镜回弹时会短暂到 ×7.4），第 776 帧前退出，不再显示 “≈1 texel / px”；结尾段没有任何叠加层。配乐、`--slug`、“20K” 措辞等待定事项与 v1 相同，仍未决定。

### 复现 v2
```bash
# 1) 终渲队列（只用 GPU 6/7，只补缺失的帧，可断点续渲）。先看计划：
python3 scripts/render_finals.py --film v2 --dry-run
#    顺序：12 个小场景 shots/t_*.py（按各自 meta 的循环长度）+ S04（180 帧）+ S04 的 overscan 静帧
#    → scripts/make_hex_tiles.py --require-final（蜂巢贴图必须全部来自终渲，否则不渲 S05）→ S05（180 帧）
python3 scripts/render_finals.py --film v2
# 2) 字幕叠加层 + 合成 + 编码（带字幕版、纯净版、ProRes 母版、剪辑点对照、每秒一帧总览）
tools/venv/bin/python -I scripts/assemble.py --film v2 --mode final --master
# 3) 终渲质检：逐帧检查 + v1 的回环/静止区检查 + S04 静止段、S04→S05 接缝、标题不变、蜂巢贴图全部终渲
tools/venv/bin/python -I scripts/qa_finals.py --film v2 --require-complete
# 预览版（还没渲出来的帧用带标注的占位图代替）
tools/venv/bin/python -I scripts/assemble.py --film v2 --mode preview --allow-missing
```
- 单独检查字幕：`tools/venv/bin/python -I scripts/make_overlays.py --film v2 --sheet renders/review/overlays_v2_sheet.png`。
- 质检脚本自检（用已知答案的输入验证各项检查）：`tools/venv/bin/python -I scripts/qa_finals.py --film v2 --selftest`。

### v2 输出位置
| 位置 | 内容 |
|---|---|
| `out/v2/LaRenderer_opening_v2.mp4` | 带字幕版，H.264 yuv420p，BT.709 |
| `out/v2/LaRenderer_opening_v2_clean.mp4` | 无叠加层的纯净版 |
| `out/v2/LaRenderer_opening_v2_master.mov` / `out/v2/LaRenderer_opening_v2_clean_master.mov` | ProRes 422 HQ 10-bit 母版（`--master`） |
| `out/v2/cuts.png` | 四个剪辑点前后帧对照（240\|241、420\|421、600\|601、780\|781） |
| `out/v2/overview_1fps.png` | 每秒一帧的全片缩略图（8 × 4） |
| `out/v2/assembly.json` | 合成清单与 QA 结果 |
| `out/v2/preview/` | 同名的预览版输出 |
| `renders/film_v2/`、`renders/film_comp_v2/`、`renders/film_comp_clean_v2/`、`renders/overlays_v2/` | v2 的整片逐帧中间文件（16-bit）与字幕层 |
| `renders/final/s04_subject/`、`renders/final/s05_finale/`、`renders/final/t_*/` | v2 新镜头和小场景的终渲帧；`renders/final/s04_subject/overscan.png` 是结尾中心格用的静帧 |
| `renders/hex_tiles/` | 蜂巢每一格的贴图序列和 `manifest.json` |
| `logs/finals_v2/`、`renders/qa/v2/` | v2 的渲染日志、质检报告和差异热图 |

v1 不受影响：v1 的成片、`renders/final/<v1 镜头>`、`versions/v1/` 都不会被 v2 改写；S01–S03 的 v1 终渲帧只读复用。
