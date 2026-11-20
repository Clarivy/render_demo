# LaRenderer 开场动画（Blender 4.5 / Cycles）

30 秒（900 帧，1920×1080，30 fps）的概念开场动画，风格为多巴胺配色 × Tactile 3D，片尾落版 **LaRenderer**。
动画只展示能力概念，不涉及模型结构。所有镜头由 Python 脚本从零搭建，结果确定、可复现。

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
