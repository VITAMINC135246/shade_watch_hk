# Shade Watch HK 操作指南

狀態：2026-11-09，依決策 D-017 撰寫。這是 [`GUIDE.md`](GUIDE.md) 的繁體中文版；兩者若有出入，以英文版為準。本文件是「repo 文件用英文」的語言例外（同 D-013）。

本指南帶你從一台裝好 repo 的電腦開始，一直走到報告數字為止。只使用已驗收的工具：

- 引擎 `SW-V1-POLICY-1.0`（V2，`356f611`）；
- `shade_map` F1.0（`35225fd`）；
- 海面政策 `SW-SEA-POLICY-2.2`（B2.2，`7707c51`）。

所有計算都由你自己執行；網頁只負責看結果和產生 config。

細節見：

- F：[`docs/shade_map/GUIDE.md`](shade_map/GUIDE.md)；
- B2.2：[`docs/sea2/GUIDE.md`](sea2/GUIDE.md)、[`docs/sea2/POLICY.md`](sea2/POLICY.md)；
- 代碼和表述規則：[`docs/OUTPUT_CODES.md`](OUTPUT_CODES.md)；
- 網頁：[`web/shade_map/README.md`](../web/shade_map/README.md)。

## 0. 結果是甚麼，不是甚麼

- **是甚麼**：用 CEDD 2020 DSM 和 1 km 向陽搜尋，算出每個 0.5 m 像素、每個時刻的遮蔭：0 日照、1 遮蔭、255 無效或不確定。
- **不是甚麼**：
  - 不是降溫效果、ΔT 或溫度；
  - 不是觀測真值（觀測精度 NOT VERIFIED）；
  - 不代表全港已經覆蓋。
- **依賴填補的判斷**：`sea-2.2` 把所有缺失的 DSM 值填成 HKPD 0 m。依賴填補資料的判斷，是這個假設下的模型結果。
- **255 的意思**：255 永遠不是陰影，也不是日照。填補之後，只剩兩種情況會是 255：
  - quality 3：太陽低時，1 km 外可能有遮擋；
  - quality 4：太陽在地平線或以下。

## 1. 每台電腦設定一次

1. 在 repo 根目錄使用 repo 的 `.venv`，系統用 macOS 或 Linux（Windows 請用 WSL2）。不支援 Windows 原生 Python，因為引擎用到 `fcntl`。
2. 確認原始 DSM 目錄在 `data/raw/dsm/2020/D12.DSM.TIFF`（3,310 張瓦片，約 26 GB）。它是只讀的，不要修改。
3. 把 `config/machine.example.json` 複製成 `config/machine.local.json`（git 會忽略這個檔）。各欄位：
   - `dsm_dir`：原始目錄的路徑。
   - `sea_profile`：`hk_cedd_2020`。
   - `output_root`：發佈結果的位置，預設 `outputs/shade_map`。必須是 repo 或 `outputs/` 內的新資料夾或 F 擁有的資料夾，F 會拒絕別人的資料夾。
   - `cache_namespace`：raw 運行的 horizon 快取資料夾（`sea-2.2` 運行用跟 view 綁定的快取）。
   - `workers`：1–4，開發時用 4。
   - `memory_budget_mb`：512–12288，預設 8192。
4. **建一次 B2.2 海面 view**（Mac 上約 35–40 分鐘；對原始資料只讀）：

   ```sh
   caffeinate -dims .venv/bin/python -m tools.sea2 build --machine config/machine.local.json
   ```

   - 它會寫入 `data/processed/dsm_views/sea_fill_v2_2/<view_id>/` 和一個指標檔。已驗收的 view 是 `8ee51b01…`；同樣的程式和資料重建，會得到完全相同的 view。
   - view 缺失或過期時，`sea-2.2` 運行會拒絕執行。只有 DSM 目錄改變時才需要重建。
   - `caffeinate -dims` 讓 Mac 保持清醒；Linux 上不用加。

## 2. 打開網頁

在 repo 根目錄執行：

```sh
python3 -m http.server 8765 --bind 127.0.0.1
```

然後打開 <http://127.0.0.1:8765/web/shade_map/>。使用網頁期間保持終端機開著，用完按 Ctrl-C 停止。

## 3. 產生區域 config

1. 打開 **New request**。
2. 在地圖上畫矩形，或輸入左下角和右上角：
   - HK1980 用公尺，格式 [easting, northing]；
   - 或 WGS84，格式 [latitude, longitude]。
   - 左下角必須在右上角的西南方，plan 不會幫你對調。
3. 取一個名稱：小寫字母、數字、`_` 或 `-`。名稱也是輸出資料夾的名字。用過的名稱如果設定不同，會被拒絕，請換新名稱。
4. 選時間：
   - **Daylight**：日期（列表或 `from..to` 範圍）加間隔分鐘數；只算日出到日落。
   - **Window**：日期加起訖時刻；落在日出前、日落後的時刻會被剔除。
   - **Instants**：逐個列出時刻，格式 `YYYY-MM-DDTHH:MM`，香港時間。
5. 選 DSM 來源：
   - `sea-2.2`：已驗收的填補政策。除非需要 raw 對照，否則用這個。
   - `raw`：DSM 原樣。
6. 看檢查結果：
   - **紅色**是錯誤：頁面不會給出 config，plan 也會拒絕。
   - **黃色**是要記錄下來的警告：
     - DSM 北邊界（深圳一側被填成 0 m）；
     - 被包圍的填補，例如水塘；
     - 落在白天以外的時刻。
7. 下載 JSON，存成 `config/regions/<name>.json`。頁面會列出這份 config 要執行的指令。

剛開始時區域盡量小：2×2 個原生格（1.5 × 1.2 km）約 720 萬像素。參考耗時（開發時，Mac，4 workers，冷快取）：

- 長洲 4 格 × 65 幀：約 11 分鐘；
- 2 格 × 3 幀：約 1 分鐘。

這些只是參考，不是預測。

## 4. 先 plan（一定先做）

```sh
.venv/bin/python -m tools.shade_map plan --machine config/machine.local.json config/regions/<name>.json
```

`plan` 不做 horizon 計算，會輸出一份 JSON，內容包括：

- 對齊後的範圍、格數、像素數；
- 幀數，以及被剔除的時刻和原因；
- 請求、批次、方向的數量和估算；
- 會不會出完整圖；
- 警告和衝突。

**常見錯誤**（exit 2，`invalid input:`）：

- 角點對調或名稱不合規則；
- 1 km 內需要 `14NE15*` 那 4 張瓦片（D-008）；
- 海面 view 缺失或過期（做第 1.4 步）；
- 名稱已經用過、但設定不同。

把 plan 和網頁的試算對照一下；兩者不同時，以 plan 為準。

## 5. 執行

```sh
caffeinate -dims .venv/bin/python -m tools.shade_map run --machine config/machine.local.json config/regions/<name>.json
```

- **續跑**：中斷了（睡眠、斷電、Ctrl-C），再執行同一條指令就會接著跑。
- **結果位置**：`<output_root>/<name>/<YYYYMMDD>/<HHMM>/`，裡面有：
  - `shade`、`quality`、`surface` 三層：每格一個 GeoTIFF，加一個 VRT，小區域另加一張完整圖；
  - `frame.json`。
  - 運行資料夾本身還有 `run_manifest.json`、`summary.json` 和 `summary.csv`。
- **工作檔和快取**：會一直保留，直到你執行 prune：

  ```sh
  .venv/bin/python -m tools.shade_map prune --machine config/machine.local.json config/regions/<name>.json        # 只列出
  .venv/bin/python -m tools.shade_map prune --machine config/machine.local.json config/regions/<name>.json --yes  # 刪除這次運行的工作資料夾
  ```

## 6. 量填補影響（只適用 sea-2.2 運行）

```sh
caffeinate -dims .venv/bin/python -m tools.sea2 fill-impact --machine config/machine.local.json config/regions/<name>.json [--times 0720,1230,1740]
```

**做甚麼**：用原始 DSM 把同樣的幀再算一次（對照組），逐像素比對。`--times` 可以只診斷部分幀，但這些時刻必須是該運行的幀。

**前提和成本**：要先有同一份 config 的完整 `sea-2.2` 運行。成本大約等於用 raw 跑一次這些幀。可以續跑，也不會寫進運行資料夾。

**輸出**：`<output_root>/_diagnostics/fill_impact/<name>/`，包括 `fill_impact.json`、`fill_impact.csv` 和依賴柵格。

**依賴代碼**（對實測和填補的目標）：

| 代碼 | 意思 |
| --- | --- |
| 0 | 不填也一樣 |
| 1 | 靠填補才確定（raw 是不確定） |
| 2 | 填補改變了判斷 |
| 3 | 填補的目標本身有判斷 |
| 4 | 仍然不確定 |

**依賴填補的陸地比例** ＝（陸地中代碼 1、2、3 的像素）÷ 全部陸地。這是依賴比例，**不是**遮蔭比例。

## 7. 看結果

在 **Results** 頁填上輸出資料夾（即 `output_root`），按 **List runs**，再選一個運行。

- **地圖**：用滑桿或下拉選單切換幀，用按鈕切換圖層。
- **像素**：點一個像素，看它的 shade、quality、surface 代碼，以及所屬瓦片的太陽位置。
- **單幀統計**：按下一節的分組列出，計數和發佈的檔案對得上。
- **全程彙總**：每個日期的平均遮蔭、日照上下限，以及全日走勢圖。
- **填補依賴**：如果做了第 6 步，這裡會顯示 fill-impact 的表格。

## 8. 報告數字

照 [`docs/OUTPUT_CODES.md`](OUTPUT_CODES.md)。重點：

1. **分組**：`sea-2.2` 的陸地 L＝surface 0＋3，水面 W＝1＋2；類別 4 和 255 只報數量。raw 運行的陸地＝surface 0。
2. **分母**：用整個分組。不要用「遮蔭 ÷（遮蔭＋日照）」，這會偏向遮蔭。
3. **三項並列**：日照、遮蔭、不確定一起列出，不確定再按 quality 拆開。
4. **文字要給上下限**：例如「陸地遮蔭 44.5 %–44.5 %，日照 55.5 %–55.5 %，不確定 0 %（長洲，2026-01-07 12:30，sea-2.2）」。下限＝該類 ÷ L；上限＝（該類＋不確定）÷ L。
5. **水面分開報告**：並註明水面的判斷比陸地不確定（0 m 填補比 DSM 水邊中位數低約 1.4 m）。
6. **填補依賴並列**：在主要數字旁邊給出依賴填補的陸地比例。
7. **分開陳述**：工程驗收、數值一致性、近似誤差、性能、觀測精度（NOT VERIFIED）、生產完成，六者分開說。區域結果不等於全港結果。

## 9. 四區量測（你的下一步）

**目的**：在移植之前，先量清楚在典型環境下，結果有多少依賴填補資料。這取代了 D-010 Q2 原本「空洞維持 255、超過 10% 就另做一版」的做法：D-016 已經把空洞填補了，現在要問的是「依賴填補的程度」。數字能不能接受，由你決定。

**區域**（每區 2×2 個原生格，讓每次運行都短）：

| 區域 | 角點 |
| --- | --- |
| 長洲 | `config/regions/cheung_chau.json`：HK1980 [820250, 807200] → [821750, 808400] |
| 中環／半山 | HK1980 [833750, 815000] → [835250, 816200] |
| 密集市區 | 自選，例如旺角；看網頁的警告 |
| 植被山坡 | 自選，例如郊野公園的山坡 |
| 北部邊境（建議加） | 自選，沿深圳河；用來量化深圳一側的填補影響 |

**時間**：兩個至日的白天，每 10 分鐘一幀：2026-06-21（81 幀）和 2026-12-22（65 幀）。兩個日期可以放在同一份 config，也可以每個日期一份。

**來源**：`sea-2.2`，之後對全部幀跑 `fill-impact`。

**每個區域、每個日期記錄**：

- 陸地的平均遮蔭上下限、平均日照上下限、平均不確定比例（`sea-2.2` 下全是 quality 3）；
- 水面的同樣數字；
- 依賴填補的陸地比例：平均值，以及最高的一幀。

**預算（粗估，未核實）**：每個區域、每個日期，運行約 10–15 分鐘，fill-impact 再加差不多的時間。五區兩日合計約 3–5 小時，快取和輸出共數 GB。先安排好時間、確認磁碟空間，並讓 Mac 保持清醒。

## 10. 疑難排解

| 現象 | 處理 |
| --- | --- |
| 網頁說要透過本機伺服器打開 | 在 repo 根目錄執行 `python3 -m http.server 8765 --bind 127.0.0.1`。 |
| Results 頁列不出運行 | 把輸出資料夾設成機器設定的 `output_root`，或按 **Find output folders under outputs/**。 |
| `sea view missing or built from a different catalogue` | 做第 1.4 步（`tools.sea2 build`）。 |
| `invalid input` 提到 `14NE15*` | 這個區域需要那 4 張偏移瓦片（D-008），把矩形移開。 |
| 名稱衝突 | 換一個新的區域名稱；F 不會覆蓋設定不同的運行。 |
| 運行中斷 | 再執行同一條 `run` 指令，會接著跑。 |

## 11. 限制（摘要）

完整清單見 `docs/sea2/POLICY.md` 和 `docs/shade_map/GUIDE.md`。

- **只限香港**：第一階段的引擎寫死了 EPSG:2326、0.5 m 格網和香港時間。
- **模型邊界**：1 km 搜尋和 5° 方向格是模型邊界，不代表精度已經證明。
- **0 m 填補的影響**：
  - 近岸海面的陰影略偏多；
  - 被包圍的填補（水塘、空洞）會變成深坑；
  - DSM 邊界外的地形（包括深圳一側）無法遮擋香港的目標。
- **quality 3 和 4 保持 255。**
- **沒有建模**：碼頭、浮橋、船和潮汐。
- **觀測精度 NOT VERIFIED。**
