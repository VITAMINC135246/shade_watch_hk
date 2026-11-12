> Implementation follow-up: the design below is a preserved research record. The 1 km update is implemented in `src/spatial.py` and `src/pipeline.py`; see [current method](METHOD.md) and [verification](QA.md). Its historical 1.5 km discussion is not the active configuration.

# 分块计算：论文、代码核查与建议路线

核查日期：2026-09-28。状态：研究与设计建议，尚未实施。

## 建议结论

保留本项目的 DSM 逐像元 horizon/LUT 计算，新增独立于原始 GeoTIFF 图幅的空间分块执行层：**统一网格 → 按窗口读取中央块及周边 DSM → 计算中央块的 horizon → 写出中央块 → 释放内存 → 下一块**。

采用真实邻区数据形成 halo（计算时额外读取的外围区域），中央输出块互不重叠。后续逐块调度、缓存 horizon、限制并发并支持断点续算。分块后仍按 0.5 m 像元计算，不会把整块赋成一个阴影值。

最值得借鉴的是 Deep Umbra 的邻区输入与中央裁切结构、Slim Shady / Sun Blocked 的逐块任务组织，以及 GRASS r.horizon 的输入范围与输出范围分离。实际读写优先使用本项目已有的 Rasterio/GDAL。以下是代码阅读和论文核查的结论，未安装、执行或基准测试外部项目。

## 逐篇核查

| 研究 | 空间分块证据 | 代码情况与采纳判断 |
| --- | --- | --- |
| Shade Watch，2025 | 正文记录使用 3315 个 DSM 输入图幅、1000 m 邻域 buffer、按方位预计算 horizon LUT；未明确说明空间块尺寸、任务调度、中央块裁切或内存管理协议。 | 本次未找到可核查的作者分块引擎。不能因为正文未写，就断言作者没有分块。保留其 horizon/LUT 方法，自行实现执行层。 |
| Shadow Accrual Maps，2019 | 主要贡献是利用太阳运动与方向复用加速时间累积；实现使用三维空间网格索引城市几何。这种光线求交索引不等同于逐块读取超大 DSM。 | 官方仓库提供已计算的 slippy tiles 与读取脚本；核查版本未含完整阴影生成引擎，不能直接作为 DSM 分块计算底座。 |
| Deep Umbra，2025；预印本 2024 | 明确将 256×256 中央块扩为 512×512 邻域输入，预测后裁回中央 256×256，专门处理邻块建筑投影。 | 有公开训练/推理代码及 MIT LICENSE。非常适合参考 halo/crop 结构；其 cGAN 输出累积阴影，不直接替代我们按时刻计算的二元物理结果。 |
| (Slim) Shady，2025 预印本 | 方法写明示例输入块 1000×1000 m，查询点间隔 950 m，并讨论边缘重叠。主分支确实按 DSM 文件/日期提交并行计算。 | 有完整 Python 流程。当前核查代码在阴影计算前裁去 DSM 的 50 像元边缘；未见为中央输出块额外拼接远邻 DSM 的完整机制。适合参考调度，不宜照搬为无接缝方案。 |
| Sun Blocked，2025 会议摘要 | 摘要介绍时空数据的阴影分析，本身没有详细的分块/halo 协议。作者对应分支按 tile 与日期提交计算任务。 | `feature/cli-refactor` 提供 CLI、可配置进程数、分阶段文件和空间任务分配；README 标注仍在开发。点周边提取统计的 buffer 不等于计算块的遮挡 halo。 |
| Global patterns of inequality in pedestrian shade provision，2026 | 方法明确采用 Slim Shady 并经 Sun Blocked 扩展的流程；正文没有给出一套新的通用分块算法。 | 论文 Code availability → Zenodo → `lukasbeuster/slim_shady`。这是同一代码体系的城市尺度应用证据；Zenodo 未固定论文运行所用提交，不能把当前分支视作论文运行的精确快照。 |

来源：

- Shade Watch：本地原文 `references/Shade Watch.pdf`，§2.3.1、§2.4、§4.1、Data availability；[出版页及 DOI](https://doi.org/10.1016/j.scs.2024.106011)。原文记载 8 GB 桌面机约 98 小时预计算全港 LUT；这个性能记录本身不能证明具体如何调度空间块。作者数据声明为按请求提供。
- Shadow Accrual Maps：[原文，尤其 §6、§8.1](https://arxiv.org/pdf/1907.04435)，[官方仓库](https://github.com/VIDA-NYU/shadow-accrual-maps)。空间加速索引、时间复用、结果发布瓦片是三个不同概念。
- Deep Umbra：[原文 §IV-A、Figure 3、§IV-C、§V](https://arxiv.org/html/2402.17169)，[官方仓库](https://github.com/uic-evl/deep-umbra)。论文采用 zoom 16，描述约 2.3 m 像元；不能把其 128 像元边缘直接套用为香港 0.5 m DSM 的遮挡半径。
- Slim Shady：[预印本，§5.2–5.3](https://assets-eu.researchsquare.com/files/rs-6966874/v1_covered_8e9acaa0-28cb-440b-afbd-9d8c8515aa5c.pdf)，[DOI](https://doi.org/10.21203/rs.3.rs-6966874/v1)，[计算仓库](https://github.com/lukasbeuster/slim_shady)。预印本原来的 `throwing_shade` 链接现重定向到这个仓库。
- Sun Blocked：[官方会议摘要](https://meetingorganizer.copernicus.org/ICUC12/ICUC12-797.html)，[作者对应分支](https://github.com/lukasbeuster/slim_shady/tree/feature/cli-refactor)。其分支 README 明确引用该摘要。
- Global patterns：[正式 DOI](https://doi.org/10.1038/s41467-026-69190-w)，[MIT 作者站可读稿，Methods 与 Code availability](https://senseable.mit.edu/papers/pdf/20260115_Gu-etal_Shady_inequalities_NatureCommunications.pdf)，[官方 Zenodo 记录](https://zenodo.org/records/17972371)。本次读取的是 MIT 托管的 accepted/in-press 稿；出版商 HTML 未成功返回。

这两组研究的关系也有明确证据：Deep Umbra 使用 Shadow Accrual Maps 生成训练真值；Global patterns 的方法与 Zenodo 则明确连接 Slim Shady / Sun Blocked。它们不构成一条可以直接替换全部方法的单一软件升级链。

## 代码证据及固定版本

以下均是 2026-09-28 实际读取的公开提交，链接可用于复核。只读源码，没有运行这些仓库。

### Deep Umbra

提交：`c6e24dddccc818ee37edace4ec9b6502b82e04d4`。

- [`utils.py:152–185`](https://github.com/uic-evl/deep-umbra/blob/c6e24dddccc818ee37edace4ec9b6502b82e04d4/utils.py#L152-L185)：`load_input_grid` 读取包含中心的 3×3 邻域，先组成 768×768，再取中间 512×512。
- [`utils.py:435–459`](https://github.com/uic-evl/deep-umbra/blob/c6e24dddccc818ee37edace4ec9b6502b82e04d4/utils.py#L435-L459)：`predict_shadow` 从推理结果裁出中央 256×256。
- [MIT LICENSE](https://github.com/uic-evl/deep-umbra/blob/c6e24dddccc818ee37edace4ec9b6502b82e04d4/LICENSE)。

可借鉴真实邻区拼接与中央输出。其未找到邻块时的零初始化行为不适合直接复制到本项目；本项目需继续区分缺数据与真实低地，并传播不确定性。

### Slim Shady 主分支

提交：`028515b874f7c6b8c8a5c33791a1e7396e2aca79`。

- [`03_process_area_parallel_multiple_days.py:60–120`](https://github.com/lukasbeuster/slim_shady/blob/028515b874f7c6b8c8a5c33791a1e7396e2aca79/code/03_process_area_parallel_multiple_days.py#L60-L120)：按文件预处理，再按文件/日期提交阴影任务，示例硬编码 32 个进程。
- [同文件 365–370 行](https://github.com/lukasbeuster/slim_shady/blob/028515b874f7c6b8c8a5c33791a1e7396e2aca79/code/03_process_area_parallel_multiple_days.py#L365-L370)：在运行阴影模型之前，将建筑 DSM 与 canopy DSM 每侧裁去 50 像元。
- [`shade_setup.py`](https://github.com/lukasbeuster/slim_shady/blob/028515b874f7c6b8c8a5c33791a1e7396e2aca79/code/shade_setup.py)：读入单份处理后的 DSM，调用 UMEP 衍生阴影函数并按同一输入栅格写出；该调用链未加载额外邻区 DSM。

论文用 1000 m 方块与 950 m 间隔举例：几何上相邻原始输入的重叠宽度为 50 m，亦可表达为相对于 950 m 中央格每侧外伸 25 m。0.5 m 分辨率下，代码的每侧 50 像元裁切等于 25 m。因此此版本的裁切顺序不能证明阴影模型保留了外侧 halo。上述判断限于核查版本，不推断作者所有实验都存在同样的问题。

核查仓库文件树未发现仓库级 LICENSE，README 的 License 节为空。可独立参考结构；直接移植源码前需厘清授权与上游 UMEP 代码的许可。

此前作为视觉参考的 [`lukasbeuster/SlimShady`](https://github.com/lukasbeuster/SlimShady) 是另一个网站展示仓库；研究计算应查看带下划线的 `slim_shady`。

### Sun Blocked 分支

提交：`cc56ed7d192c0b38c854a8e8c5ccd51fe9cb2f0e`。

- [`src/processing.py:62–91`](https://github.com/lukasbeuster/slim_shady/blob/cc56ed7d192c0b38c854a8e8c5ccd51fe9cb2f0e/src/processing.py#L62-L91)：`run_shade_simulations` 按 tile/date 调度，进程数取自配置。
- [`src/raster.py:178–201`](https://github.com/lukasbeuster/slim_shady/blob/cc56ed7d192c0b38c854a8e8c5ccd51fe9cb2f0e/src/raster.py#L178-L201)：DSM 预处理仍有默认 50 像元边缘裁切。
- 同分支的 `simulation.buffers` 用于点周围栅格值提取；不能据此宣称遮挡计算具有对应长度的邻区支持。

可参考配置、任务键与中间产物组织。重试和完成判断需自己做成可验证的机制；仅检查文件存在不足以验证任务完整，也不能忽略子任务异常。

### Shadow Accrual Maps

提交：`1b4e92780281a3072523318cd318fd44bff1f379`。

- [`shadow.py`](https://github.com/VIDA-NYU/shadow-accrual-maps/blob/1b4e92780281a3072523318cd318fd44bff1f379/shadow.py) 根据经纬度找到 zoom 17 的 256×256 瓦片，从二进制文件读取已有累积值。
- [README](https://github.com/VIDA-NYU/shadow-accrual-maps/blob/1b4e92780281a3072523318cd318fd44bff1f379/README.md) 明确说明该仓库提供计算好的数据及读取脚本。没有在该版本找到论文的完整 C++/OpenGL 阴影引擎。

## 可用的其他基础设施

| 工具/项目 | 可借鉴或使用的能力 | 本项目中的位置 |
| --- | --- | --- |
| [Rasterio windowed I/O](https://rasterio.readthedocs.io/en/stable/topics/windowed-rw.html) + [GDAL VRT](https://gdal.org/en/stable/drivers/raster/vrt.html) | 按窗口读写大于内存的栅格；VRT 引用源图幅形成逻辑镶嵌。实际 I/O 仍受源 TIFF 存储块和缓存影响。 | 首选读写层。只读取任务需要的源文件窗口；不先生成全港内存数组。 |
| [GRASS r.horizon](https://grass.osgeo.org/grass-stable/manuals/r.horizon.html) / [GitHub 源码](https://github.com/OSGeo/grass/tree/main/raster/r.horizon) | 输出计算区域与外扩读取范围分开，支持 `bufferzone`、四侧 buffer、`maxdistance` 和线程设置。 | 最贴近本问题的成熟方法参考，也可作为之后独立比较的候选。其太阳方向约定、地球曲率等需对齐后再比较。 |
| [GRASS r.tile](https://grass.osgeo.org/grass-stable/manuals/r.tile.html) / [源码](https://github.com/OSGeo/grass/tree/main/raster/r.tile) | 按行列块大小与 overlap 切分栅格。 | 展示已有分块工具，但单独切文件不负责阴影边界正确性。 |
| [GRASS r.sun](https://grass.osgeo.org/grass-stable/manuals/r.sun.html) | `npartitions` 降低输入内存需求；文档明确其输出数组并不随该参数分块。 | 不把开启这个参数等同于全流程内存有界。 |
| [HORAYZON](https://github.com/ChristianSteger/HORAYZON) | Embree 光线追踪、C++ 并行 horizon 与阴影；支持内域/外域，示例以外域 TIN 简化降低内存。MIT LICENSE。 | 保留为后续性能研究候选；它改变栅格到几何的表示，不作为本轮执行层改造的前置条件。 |
| [Dask overlap](https://docs.dask.org/en/stable/array-overlap.html) | 为数组块交换邻域、处理后 trim。 | 将来多机调度候选。halo 大于块时可能重分块；第一版用简单可控的单机任务循环更易验证内存。 |

HORAYZON 实际核查示例：[提交 77e3b26 的 `gridded_planar_DEM_2m.py`](https://github.com/ChristianSteger/HORAYZON/blob/77e3b26f94068df01ce4a302d931db83023327cb/examples/horizon/gridded_planar_DEM_2m.py)。它设定内域和搜索距离、读取外域并简化外围地形；不据此宣称它提供无需配置的全港流式任务调度。

## 本项目需要改动的位置

本地代码核查：

- [源文件接缝检查](</Volumes/My Passport for Mac/Projects/shade_watch_hk/src/shade_watch.py:125>) 的第 130 行把所有源 DSM 整幅读入列表。即使输出范围不变，大量输入也可能在预检阶段耗尽内存。需要按相邻边界窗口读取，并避免累积无限长度的差值列表。
- [带缓冲 DSM 读取](</Volumes/My Passport for Mac/Projects/shade_watch_hk/src/shade_watch.py:171>) 打开全部源文件并合并整个研究区窗口。需要源图幅空间索引、相交筛选、有上限的文件句柄与窗口读取。
- [主循环](</Volumes/My Passport for Mac/Projects/shade_watch_hk/src/shade_watch.py:319>) 按方位顺序计算，空间上仍持有整个输出研究区，没有空间任务循环。
- [逐像元 horizon 核心](</Volumes/My Passport for Mac/Projects/shade_watch_hk/src/horizon.py:166>) 默认最大搜索 1500 m、完整支持检查 1000 m。halo 应覆盖实际搜索依赖，并计入采样取整边缘；不能因为当前输入只外扩 1000 m 就认定算子依赖半径也是 1000 m。
- [低太阳高度敏感性阈值](</Volumes/My Passport for Mac/Projects/shade_watch_hk/src/shade_watch.py:347>) 当前由整个输入和输出区域的高度极值计算。分块时若每块另算阈值，即使 DSM 拼接正确，quality/NoData 也可能形成块缝。

## 建议开发顺序与验收条件

### 第一步：冻结计算定义与单区参考

固定 CRS、分辨率、全局网格原点、日期/太阳位置策略、方位分箱、NoData 编码、搜索距离、完整支持距离和质量规则。以现有 600×450 m 输出作为回归基准。

首次验收保持与单区参考完全相同的可用 DSM 外边界。当前搜索可达 1500 m，但输入仅外扩 1000 m，某些方向在达到搜索上限之前已越出输入。若新版直接加入更远的真实 DSM，结果变化可能来自输入增加，应另做敏感性试验，不能混入分块等价性验收。

所有空间索引均来自同一全局网格；不能每块独立重投影或重新对齐。当前 `round` 采样需保留全局地址与取整规则，尤其测试半像元位置及奇数块偏移。太阳位置和不确定性策略应独立于任务块大小；若今后允许全港太阳位置随地理位置变化，也应先定义位置规则再划分计算任务。

### 第二步：单进程、按需读取、中央输出

建立仅含文件路径、CRS、像元大小、边界和 NoData 的 DSM 清单。为每个中央块构造 halo 窗口，只读取与该窗口相交的源数据。复用现有逐像元 horizon 核心，只计算中央块目标像元；外围仅提供潜在遮挡物。

每块独立写出 horizon、二元标签和 quality，并释放大数组。通过窗口写入或 VRT 组织全国/全港结果，避免最后又在内存中合成全幅。显示视频使用明确标注的预览分辨率，原生科学栅格继续保持 0.5 m。

中央块无重复也无缺口；两块可以读取重叠 DSM，但最终像元只由一个中央块负责。无需在重叠区平均 0/1 标签。

**验收门槛：**同输入、同参数下，分块与单区版本的 labels、quality、有效掩膜逐像元一致；horizon 先要求一致，若因明确的数值实现差异采用容差，应记录差异且确保标签不受影响。改变任务顺序、块尺寸或把边界平移若干像元，结果仍应一致。

### 第三步：跨块验证与内存预算

必须覆盖建筑或高地处于相邻块/对角块、低太阳高度、缺 DSM、真实数据外边界、输入 GeoTIFF 接缝、研究区不足整块以及全 NoData 块。开发阶段可使用明确标为测试夹具的人工几何；本次未创建此类数据。再用已有真实 DSM 做多块回归，分别报告块缝附近与内部差异。

块尺寸先作为参数，测试 1024、2048、4096 像元中央块，以峰值内存和耗时选择默认值，不跟随源文件的 750×600 m 图幅。推荐首先评估 2048×2048 像元（1024×1024 m）中央块。

以 2048×2048 中央块和 0.5 m DSM 为例，仅计算一个 float32 DSM 数组：

| 每侧 halo | 输入行列数 | 仅 DSM 字节量，十进制 MB |
| --- | --- | --- |
| 1000 m | 6048×6048 | 146.3 MB |
| 1500 m | 8048×8048 | 259.1 MB |

这是几何与数组类型推算，不是峰值内存测试；未计采样保护边缘、有效掩膜、坐标数组、horizon、临时数组、GDAL 缓存和进程开销。进程数必须根据实测单任务峰值与可用 RAM 决定。halo 很大时，过小中央块会反复读取同一邻区；增加任务数不保证加速。

**验收门槛：**固定块大小和并发数时，扩大总研究区或输入文件数，大数组内存保持在预算内；允许轻量文件索引随图幅数增长。接缝检查、统计、拼接、渲染等阶段都要受同样约束。

### 第四步：缓存、续算、有限并行，再做全港试跑

先以单进程通过正确性和内存验收，再增加有限进程池。任务以网格/中央块/方位为键，缓存与日期无关的 horizon LUT。太阳时序比较逐窗口进行，避免保存整日全部帧在 RAM。

记录源数据版本、参数与网格指纹、算子版本、任务状态、运行时间和输出校验。使用临时文件完成后再原子改名；失败需可见，续算必须验证已有输出完整且参数一致。

验收崩溃后重启与干净完整运行结果一致、无重复/缺失中央像元，随后从小区、多块连续区域逐级扩大。全港前估算计算量与落盘容量。分块解决内存增长，不自动消除当前逐像元长距离扫描的时间成本；如仍过慢，再单独比较优化 horizon 算法、HORAYZON 或 GRASS 引擎。

## 这条路线的正确性边界

若每个中央像元看到与单区参考相同的全部算子依赖数据，并采用相同的采样、太阳参数和分类规则，改变任务分组应不改变结果。这是本项目推荐设计的验收目标，不是已经通过的测试结论。

内部计算块边界可以通过充分 halo 消除人为截断；整个 DSM 覆盖范围以外、缺测区域或既定最大搜索距离以外的未知遮挡仍须保留不确定性。任何固定长度 overlap 都不能自动保证任意地形和任意低太阳高度的全物理正确性。

本次仅新增这份研究记录。现有计算代码、配置、原始输入和输出未修改。
