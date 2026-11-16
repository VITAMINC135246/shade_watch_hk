# Shade Watch HK 操作指南

狀態：2026-11-16，適用標記 `mac-v1.0`。英文版是 [GUIDE.md](GUIDE.md)；兩者不一致時以英文版為準。

這份指南帶你從一台有 repo 的 Mac 走到可以報告的數字。每一項計算都由你自己啟動；網頁只看結果、產生設定檔。

更多細節：設計見 [ARCHITECTURE.md](ARCHITECTURE.md)；代碼和報告規則見 [OUTPUT_CODES.md](OUTPUT_CODES.md)；網頁見 [../web/viewer/README.md](../web/viewer/README.md)。政策的說明在記錄裡：[records/v1/POLICY.md](records/v1/POLICY.md)（引擎）、[records/sea2/POLICY.md](records/sea2/POLICY.md)（填補）。

## 0. 結果是什麼、不是什麼

- **是什麼**：用城市的 DSM、向太陽方向搜尋 1 km，算出每個 0.5 m 像素在每個時刻的遮蔭圖（0 日照、1 遮蔭、255 無效或不確定）。
- **不是什麼**：
  - 不是降溫效果、ΔT 或溫度；
  - 不是觀測到的真實情況（觀測精度 NOT VERIFIED）；
  - 不是全港或全市的覆蓋。
- **依賴填補的判斷。** 用 `sea-2.2` 時，DSM 的所有缺值都以該城市高程基準的 0 m 填補（香港是 HKPD，鹿特丹是 NAP）。依賴填補資料的判斷，是在這個假設下的模型結果。
- **255 的意思。** 255 不是遮蔭，也不是日照。填補之後只剩兩種：quality 3（太陽低時，1 km 外可能有遮擋）和 quality 4（太陽在地平線或以下）。

## 1. 第一次設定 Mac

1. 在 repo 根目錄用 repo 的 `.venv`（Python 3.12，套件見 `requirements.lock.txt`）。支援 macOS。Linux 屬於 C2.0，尚未核實。不支援 Windows 原生。
2. 確認香港 DSM 在 `data/raw/hong_kong/dsm_cedd_2020/D12.DSM.TIFF`（3,310 張瓦片，約 26 GB）。原始資料只讀，不要修改。
3. 把 `config/machine.example.json` 複製成 `config/machine.local.json`（Git 會忽略它）。欄位：
   - `dsm_dir`：香港的原始目錄。
   - `sea_profile`：`hk_cedd_2020`。
   - `output_root`：發佈結果的位置，預設 `runs/main`。請用 `runs/` 底下直接的一個資料夾；工具會拒絕不是它建立的資料夾。
   - `cache_namespace`：raw 運行的 horizon 快取名稱前綴（預設 `raw`，後面會加上城市，例如 `raw_hong_kong`）。`sea-2.2` 運行用的是跟 view 綁定的快取。
   - `workers`：1–4，開發時用 4。
   - `memory_budget_mb`：512–12288，預設 8192。
   - `cities.<city_id>.raw_dir`：香港以外每個已登記城市的原始資料夾。
4. **建一次香港的填補 view**（Mac 上約 35–40 分鐘；只讀原始資料）：

   ```sh
   caffeinate -dims .venv/bin/python -m shade_watch.fill build
   ```

   - 它會寫出 `data/derived/views/<view_id>/` 和一個指標檔。已驗收的 view 是 `412eae79…`；同樣的程式、資料和函式庫重建會得到相同的結果。
   - `sea-2.2` 運行遇到缺少或過時的 view 會拒絕。DSM 目錄或檔案時間改變時要重建。
   - `caffeinate -dims` 讓 Mac 保持清醒。

所有指令都接受 `--machine <檔案>`，預設是 `config/machine.local.json`。

## 2. 打開網頁

在 repo 根目錄：

```sh
python3 -m http.server 8765 --bind 127.0.0.1
```

然後打開 <http://127.0.0.1:8765/web/viewer/>。用網頁時保持終端機開著，用 Ctrl-C 停止。

## 3. 產生區域設定檔

網頁產生的是香港的區域設定檔。也可以手寫；範例在 `config/regions/`。

1. 打開 **New request**。
2. 在地圖上畫矩形，或輸入左下角和右上角：
   - HK1980，單位公尺，[東距, 北距]；
   - 或 WGS84，[緯度, 經度]。
   - 左下角必須在右上角的西南方。規劃不會替你對調。
3. 取一個名字：小寫字母、數字、`_` 或 `-`。名字也是輸出資料夾的名字。用過的名字如果設定不同會被拒絕，請用新名字。
4. 選時間：
   - **Daylight**：日期（列表或範圍 `from..to`）加間隔分鐘數，只算日出到日落。
   - **Window**：日期加起訖時刻，日照以外的時刻會被丟掉。
   - **Instants**：明確的 `YYYY-MM-DDTHH:MM`，用城市的當地時間。
5. 選 DSM 來源：
   - `sea-2.2`：已驗收的填補政策。除非要做 raw 對照，都用這個。
   - `raw`：原樣的 DSM。
6. 看檢查結果：
   - **紅色**是錯誤：不會產生設定檔，規劃也會拒絕。
   - **琥珀色**是要記下的警告：DSM 北緣（深圳一側，填成 0 m）、封閉的填補區（例如水塘）、日照以外的時刻。
7. 下載 JSON，存成 `config/regions/<name>.json`。網頁會列出這份設定檔要用的指令。

區域設定檔有兩種 schema。`shade-map-region-1.0` 只用於香港，預設 `raw`。`shade-map-region-1.1` 要寫 `city`，接受 `projected` 角點，預設 `sea-2.2`。香港以外的新工作請用 1.1。

剛開始請用小區域：香港 2×2 格（1.5 × 1.2 km）約 720 萬像素。Mac 上用 4 個 workers 的實測：快取已有時，2×2 格 146 幀約 8–12 分鐘。這不是預測。

## 4. 規劃（一定先做）

```sh
.venv/bin/python -m shade_watch plan config/regions/<name>.json
```

`plan` 不做任何 horizon 計算。它輸出 JSON，內容有：

- 對齊後的範圍、格子和像素數；
- 幀，以及被丟掉的時刻和原因；
- 請求、批次和方向的數目、缺少的方向數，以及估計；
- 會不會寫完整圖；
- 警告和衝突。

**錯誤**（退出碼 2，`invalid input:`）：

- 角點對調或名字不合規；
- 香港的區域在 1 km 內需要那 4 張 `14NE15*` 瓦片（它們的網格有偏移）；
- 缺少或過時的填補 view（做第 1 節第 4 步，或登記城市）；
- 名字用過、但設定不同。

網頁的試算和 `plan` 不一致時，以 `plan` 為準。

## 5. 運行

```sh
caffeinate -dims .venv/bin/python -m shade_watch run config/regions/<name>.json
```

也可以不寫設定檔，直接在 Python 裡呼叫：

```python
from shade_watch import shade_map, plan_shade_map
plan_shade_map([820250, 807200], [821750, 808400], "2026-06-21", name="cc_test", crs="hk1980")
shade_map([820250, 807200], [821750, 808400], "2026-06-21", name="cc_test", crs="hk1980")
```

`when` 是一個日期（日照時間、每 10 分鐘），或和設定檔一樣的時間物件。`crs` 是 `wgs84`（預設）、`hk1980`，或 `projected`（要配 `city`）。`dsm_source` 預設 `sea-2.2`。

- **續跑：** 運行中斷（睡眠、斷電、Ctrl-C）時，再執行同一個指令就會接著跑。
- **結果在哪：** `<output_root>/<name>/<YYYYMMDD>/<HHMM>/`，有 `shade`、`quality`、`surface`（每格一個 GeoTIFF、一個 VRT，小區域另有完整圖）和 `frame.json`。運行資料夾還有 `run_manifest.json`、`summary.json`、`summary.csv`。搬動發佈結果時，圖層資料夾要和 VRT 放在一起。
- **工作檔：** 在你清理之前都會保留：

  ```sh
  .venv/bin/python -m shade_watch prune config/regions/<name>.json        # 列出
  .venv/bin/python -m shade_watch prune config/regions/<name>.json --yes  # 刪掉這個運行的工作資料夾
  ```

## 6. 量填補依賴（`sea-2.2` 運行）

```sh
caffeinate -dims .venv/bin/python -m shade_watch.fill fill-impact config/regions/<name>.json [--times 0720,1230,1740]
```

**做什麼。** 用原始 DSM 重算同樣的幀（反事實），逐像素比較。`--times` 可以只算其中幾幀，時刻必須是運行裡有的幀。

**條件和代價。** 需要同一份設定檔已完成的 `sea-2.2` 運行。代價約等於用 raw 跑這些幀。可以續跑，不會寫進運行資料夾。

**輸出：** `<output_root>/_diagnostics/fill_impact/<name>/`（`fill_impact.json`、`fill_impact.csv` 和依賴柵格）。

**依賴代碼**（實測和填補的目標）：

| 代碼 | 意思 |
| --- | --- |
| 0 | 不填補也是同樣的判斷 |
| 1 | 因填補而有了判斷（raw 運行裡是不確定） |
| 2 | 填補改變了判斷 |
| 3 | 填補出來的目標，有判斷 |
| 4 | 仍然不確定 |

**依賴填補的陸地** ＝（陸地裡代碼 1、2、3 的像素）÷ 全部陸地。這是依賴的比例，**不是**遮蔭的比例。

## 7. 看結果

在 **Results** 設定輸出資料夾（預設 `runs/main`），或按 **Find output folders under runs/ and baselines/**，再按 **List runs**，選一個運行。

輸出資料夾可以填 repo 裡任何一個發佈根目錄，例如 `baselines/measure_5regions_20261110`。也可以直接用網址打開某個運行：`http://127.0.0.1:8765/web/viewer/#/results?root=<輸出資料夾>&run=<名字>&frame=<YYYYMMDD>/<HHMM>&layer=shade`。這個網頁是為香港做的，鹿特丹的運行能否正確顯示未核實。

- **地圖：** 用滑桿或列表切換幀，用按鈕切換圖層。
- **像素：** 點一個像素，看它的 shade、quality、surface 代碼，以及所在瓦片的太陽位置。
- **單幀統計：** 分組照下面的定義，數字和發佈的檔案對得上。
- **整個運行：** 每個日期的平均遮蔭和日照上下限，以及全天的曲線。
- **填補依賴：** 做過第 6 節的話，會顯示 fill-impact 的表。

一天的第一幀和最後一幀常常沒有日照像素：太陽還低於瓦片的遠距門檻，沒被遮擋的像素只能是不確定。這是引擎的規則，不是計數錯誤。

## 8. 報告數字

照 [OUTPUT_CODES.md](OUTPUT_CODES.md)。簡單說：

1. **分組。** `sea-2.2` 的陸地 L ＝ surface 0 ＋ 3，水面 W ＝ surface 1 ＋ 2；類別 4 和 255 只計數。raw 運行的陸地 ＝ surface 0。
2. **分母。** 用整個組。不要用「遮蔭 ÷（遮蔭＋日照）」，那會偏向遮蔭。
3. **三項並列。** 日照、遮蔭、不確定一起報，不確定再按 quality 分開。
4. **文字裡寫上下限。** 下限 ＝ 該類 ÷ L；上限 ＝（該類＋不確定）÷ L。
5. **水面分開報。** 水面和陸地分開，並說明水面的判斷比較不確定（香港的 0 m 填補比 DSM 水邊中位數約低 1.4 m）。
6. **並列填補依賴。** 主要數字旁邊寫上依賴填補的陸地比例。
7. **分開陳述。** 工程驗收、數值一致性、近似誤差、性能、觀測精度（NOT VERIFIED）、生產完成，六者分開說。一個區域的結果不等於全港的結果。

## 9. 其他城市

已登記的城市是香港和鹿特丹（`config/cities/`）。香港以外的城市要先用原始圖幅登記一次。

**鹿特丹。** 把兩張圖幅 `R_37FZ1.tif` 和 `R_37HN1.tif` 放在 `data/raw/rotterdam/dsm_ahn_05m/`，在機器設定檔把 `cities.rotterdam.raw_dir` 設成這個資料夾。然後：

```sh
.venv/bin/python -m shade_watch.city register rotterdam
.venv/bin/python -m shade_watch plan config/regions/rotterdam_projected.json
caffeinate -dims .venv/bin/python -m shade_watch run config/regions/rotterdam_projected.json
```

- 登記會把圖幅無損切成原生格，放在 `data/derived/catalogues/rotterdam/<ingest_id>/`，並建出 0 m NAP 的填補 view（約 2–4 分鐘）。它會印出 `ingest_id`、`view_id` 和一份報告；會有警告 `fill_above_ground`，這是預期的。
- 在 Python 裡：`shade_map([51.9200, 4.4750], [51.9230, 4.4800], when, name=..., city="rotterdam")`。幀資料夾用城市的當地日期和時刻（Europe/Amsterdam）。不存在的當地時刻無效；有歧義的時刻要寫明時差。
- 要在不同機器上重現完全相同的矩形，請用 `projected` 角點（RD New）。

**新增城市。** 在 `config/cities/<city_id>.json` 加城市設定檔（投影的公尺座標系、0.5 m、高程基準、IANA 時區、資料來源說明、精確範圍、範圍中心 0.01° 內的日照參考點，以及每張圖幅的位元組大小、SHA-256 和宣告的 NoData），在 `config/sea_profiles/` 加 `h_sea_m` 為 0.00 的填補設定檔，設定 `cities.<city_id>.raw_dir`，然後登記。完整的欄位規則見記錄 [records/city/GUIDE.md](records/city/GUIDE.md)。

## 10. 疑難排解

| 狀況 | 處理 |
| --- | --- |
| 網頁說要透過本機伺服器打開 | 在 repo 根目錄執行 `python3 -m http.server 8765 --bind 127.0.0.1`。 |
| Results 頁列不出運行 | 把輸出資料夾設成機器設定檔的 `output_root`，或按 **Find output folders under runs/ and baselines/**。 |
| `sea view missing or built from a different catalogue` | 香港：做第 1 節第 4 步。其他城市：執行 `shade_watch.city register <city>`。 |
| `invalid input` 提到 `14NE15*` | 區域需要那 4 張偏移的瓦片；移動矩形。 |
| 名字衝突 | 用新的區域名字；工具不會覆蓋設定不同的運行。 |
| `output_root` 被拒絕 | 用 `runs/` 底下直接的一個資料夾，而且是工具建立的或還不存在的。 |
| 運行中斷 | 再執行同一個 `run` 指令，會接著跑。 |

## 11. 限制

- **網格。** 只支援投影公尺座標系的 0.5 m DSM。
- **模型邊界。** 1 km 搜尋和 5° 方向格是模型邊界，不代表精度已證明；近似誤差沒有量化。
- **0 m 填補。**
  - 香港：近岸水面的遮蔭略為偏多；封閉的填補區（水塘、空洞）會變成坑；DSM 邊界以外的地形（包括深圳一側）不能遮擋香港的目標。
  - 鹿特丹：約一半的有效像素低於 0 m NAP，填補後的表面可能擋住旁邊低地的陽光。fill-impact 能量出這種依賴，但分不出假遮蔭和真遮蔭。
- **quality 3 和 4 仍是 255。**
- **沒有模擬：** 碼頭、浮橋、船隻和潮汐。
- **太陽位置：** NOAA 近似法在鹿特丹緯度的精度未核實。
- **觀測精度 NOT VERIFIED**（香港和鹿特丹）；鹿特丹的地表類別 NOT VERIFIED。
