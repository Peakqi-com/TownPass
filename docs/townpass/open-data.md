# 開放資料：data.taipei 可用資料集（已驗證）

> 2026-11-06 實測：抓下 data.taipei 全部 **2,816 個資料集**的 metadata，篩出適合手機微服務的候選，並對 30 個資料集**實際下載**，確認格式、筆數、欄位、座標、編碼、CORS 與更新時間。
> 原始結果：[`open-data/verified-2026-11-06.json`](open-data/verified-2026-11-06.json)
> 全部資料集目錄（可直接搜尋）：[`open-data/data-taipei-catalog.csv`](open-data/data-taipei-catalog.csv)
> 驗證腳本：[`open-data/verify_datasets.py`](open-data/verify_datasets.py)
>
> 所有資料集的授權都是「**政府資料開放授權條款-第1版**」，可以使用，但要標示出處（寫進作品 README §5）。

---

> **作品 repo 已經做好代理**：`townpass2026-peakqi` 的 `/api/opendata/<id>` 已處理下面所有問題（CORS、Big5、CSV/XML、TWD97、快取、找附近），第 2、3 節裡 21 個來源都已登記，網頁端用 `getOpenData()` 呼叫即可。新增來源見該 repo 的 `src/lib/opendata/sources.ts`。

## 1. 共通結論（寫程式前先看）

| 問題 | 結論 | 做法 |
|---|---|---|
| **CORS** | 只有 YouBike、停車場、交通訊息三個來源開放 CORS，**其他都沒有** | 一律經過作品的 Next.js Route Handler 代理（`/api/opendata/<id>`），網頁不直接打 data.taipei |
| **編碼** | 有 9 個是 **Big5**：飲水機、哺集乳室、親子友善廁所、資源回收收受點、捷運無障礙電梯、捷運無障礙異常公告、戶政等。`fetch().text()` 會變亂碼 | 用 `new TextDecoder('big5').decode(await res.arrayBuffer())` 解碼。UTF-8 檔案有 BOM，要去掉 `﻿` |
| **座標** | 多數是 WGS84 經緯度。**今日施工、停車場、公園設施是 TWD97（二度分帶）**；防空疏散避難的「緯經度」是兩個值併在一個欄位 | TWD97 要轉成 WGS84 才能畫在 Leaflet 上；欄位名稱各資料集都不一樣，要逐一對應 |
| **檔案大小** | 公園基本資料 7.2MB、停車場描述 4.1MB、防空避難 3.0MB、今日施工 2.7MB | 在後端精簡欄位、依位置篩選後再回傳 |
| **日期格式** | 今日施工用民國年（`107/07/11 10:00:50`） | 解析時要加 1911 |
| **下載網址** | 資料集頁面上的「資料存取網址」是 `https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=<rid>`；部分資源會轉址到 Azure blob | 下面表格的網址都是實測可用的 |

### data.taipei API（從官網前端找出來的，非官方文件）

```bash
# 列出資料集（關鍵字參數無效，資料集只有 2,816 筆，直接全部抓回來在本機篩選）
curl -X POST https://data.taipei/api/v2/frontstage/tpeod/dataset.search \
  -H 'Content-Type: application/json' \
  -d '{"page_num":1,"page_limit":500,"sort":"metadata_changed.date_desc","post_filter":{"type":["dataset"]}}'
# 資料集明細（含 resources 的 rid、更新頻率、授權）
curl 'https://data.taipei/api/frontstage/tpeod/dataset.view?id=<pid>'
# 下載資源
curl -L 'https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=<rid>'
```

---

## 2. 即時資料

| 資料集 | 更新 | 筆數 | 格式／編碼 | 座標 | CORS | 資料網址 |
|---|---|---|---|---|---|---|
| [YouBike 2.0 即時資訊](https://data.taipei/dataset/detail?id=c6bc8aed-557d-41d5-bfb1-8da24f78f2fb) | 每 1 分 | 1,824 站 | JSON | `latitude`、`longitude` | ✅ | `https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json` |
| [停車場剩餘車位](https://data.taipei/dataset/detail?id=d5c0656b-5250-4179-a491-c94daa56ef2c) | 約每 5 分 | 1,230 場 | XML | 無（用 ID 對應停車場描述） | ✅ | `https://tcgbusfs.blob.core.windows.net/blobtcmsv/TCMSV_allavailable.xml` |
| 停車場描述（同上資料集） | 每月 | — | XML，4.1MB | `TW97X`／`TW97Y`（TWD97） | ✅ | `https://tcgbusfs.blob.core.windows.net/blobtcmsv/TCMSV_alldesc.xml` |
| [今日施工資訊](https://data.taipei/dataset/detail?id=c208dabd-2da0-4e6d-8dbd-a004b9782b0a) | 每 10 分 | 1,085 件 | GeoJSON，2.7MB | `X`／`Y`（TWD97） | ❌ | `https://tpnco.blob.core.windows.net/blobfs/Todaywork.json` |
| [即時交通訊息](https://data.taipei/dataset/detail?id=a6fae9f8-8d0f-4605-98ac-577388a7734f) | 不定期 | 數則 | JSON | 無 | ✅ | `https://tcgbusfs.blob.core.windows.net/dotapp/news.json` |
| [捷運列車到站站名](https://data.taipei/dataset/detail?id=6556e1e8-c908-42d5-b984-b3f7337b139b) | 每 30 秒 | 45 筆 | JSON | 無 | ❌ | `https://tcgmetro.blob.core.windows.net/stationnames/stations.json` |
| [空氣品質即時污染指標](https://data.taipei/dataset/detail?id=73991c2a-9ced-48cc-aa1f-6fbf60c435ff) | 每小時 | 216 筆 | JSON | 無（只有站名） | ❌ | `https://tpdep.blob.core.windows.net/techdep/tldep_AQI_DAYHour.json` |
| [捷運車站無障礙設施異常公告](https://data.taipei/dataset/detail?id=d884a9c6-f86c-4854-8da7-e6516ddbe612) | 不定期 | 有異常才有資料 | CSV（Big5） | 無 | ❌ | resource.download?rid=`649c44eb-60b5-4746-…`（見 JSON） |

> 公車、捷運的完整動態請改用 **TDX**（要申請金鑰）。data.taipei 的「預估到站時間（公車）」是 CSV，不適合即時查詢。

## 3. 地點資料（可以畫在地圖上）

| 資料集 | 筆數 | 編碼 | 座標欄位 | 特色欄位 |
|---|---|---|---|---|
| [公廁點位資訊](https://data.taipei/dataset/detail?id=ca205b54-a06f-4d84-894c-d6ab5079ce79) | 1,531 | UTF-8 | 經度、緯度 | 公廁類別、等級（特優～改善）、無障礙廁座數、親子廁座數、照護床 |
| [哺集乳室](https://data.taipei/dataset/detail?id=5d1d34d8-1b81-4162-87b6-05e0896af958) | 526 | Big5 | **沒有座標**（只有地址） | 開放時間、位置指引、基本設備、友善設備、輪椅使用、優良認證效期 |
| [AED 設置地點](https://data.taipei/dataset/detail?id=cd050577-115f-4299-b37a-012ff490a632) | 2,729 | UTF-8 | 緯度、經度 | 場所分類、AED 放置地點、地點描述 |
| [公共場所飲水機](https://data.taipei/dataset/detail?id=f158e1bc-8400-44c2-a93a-e09361ddb7f5) | 144 | Big5 | 緯度、經度 | 開放時間、飲水台數、設置地點 |
| [親子友善廁所](https://data.taipei/dataset/detail?id=9d7488f5-0f19-45c3-adf9-badf686dda18) | 393 | Big5 | 經度、緯度 | 尿布臺、兒童座椅數量 |
| [性別友善廁所](https://data.taipei/dataset/detail?id=af60ee5b-4c97-437a-9db8-ec9bd6caf4ae) | 84 | UTF-8 | 緯度、經度 | 各類便器、無障礙設施數量 |
| [垃圾車點位路線](https://data.taipei/dataset/detail?id=6bb3304b-4f46-4bb0-8cd1-60c66dcd1cae) | 4,012 | UTF-8 | 經度、緯度 | **抵達時間、離開時間**、路線、車次、里別（2026-10-30 更新） |
| [垃圾、資源、廚餘限時收受點](https://data.taipei/dataset/detail?id=1acf38f3-1509-4cb1-898a-9b1d4f31a3af) | 30 | Big5 | 經度、緯度 | 備註（收受時間） |
| [藥局](https://data.taipei/dataset/detail?id=6fa3ed67-e60e-44d9-a366-ce7008e322de) | 894 | UTF-8 | 經度、緯度 | 機構名稱、權屬別 |
| [友善店家](https://data.taipei/dataset/detail?id=d807396c-e41f-4005-be42-0160280783a1) | 993 | UTF-8 | 經度、緯度 | **行動裝置充電**、無障礙、性別友善、友善廁所、英日韓語友善、素食、便利支付（中英文兩版） |
| [市立圖書館各分館](https://data.taipei/dataset/detail?id=43772803-6504-469c-894d-35904342a53b) | 70 | UTF-8 | 緯度、經度 | 電話、地址 |
| [各區運動中心](https://data.taipei/dataset/detail?id=80be7612-593f-4795-9935-a10ce0f7b75b) | 12 | UTF-8 | 經度、緯度 | 網址 |
| [共融式遊戲場](https://data.taipei/dataset/detail?id=2704f07d-4d1d-4cef-b53a-c44aef326d96) | 108 | UTF-8 | longitude、latitude | 連結 |
| [公園基本資料](https://data.taipei/dataset/detail?id=ea732fb5-4bec-4be7-93f2-8ab91e74a6c6) | 813 | UTF-8，**7.2MB** | pm_Longitude、pm_Latitude | 開放時間、運動／遊憩設施（`https://parks.gov.taipei/parks/api/`） |
| [公園設施](https://data.taipei/dataset/detail?id=68afe2b1-fe17-45a7-a9c9-d8b4919b32c0) | 3 個檔案 | UTF-8 | X坐標、Y坐標（TWD97） | 體健設施、兒童遊戲場遊具 |
| [捷運出入口無障礙電梯／坡道](https://data.taipei/dataset/detail?id=0a3bb422-9eb5-459b-a9d4-138456516183) | 193 | Big5 | 經度、緯度 | 出入口編號 |
| [防空疏散避難設施](https://data.taipei/dataset/detail?id=70a6216e-3730-4d1d-b334-62fca2dd71cd) | 22,443，3MB | UTF-8 | 「緯經度」單一欄位 | 可容納人數、地下樓層數 |
| [河濱自行車租借站](https://data.taipei/dataset/detail?id=f63886b7-7627-4e2a-94c0-27a2c0f55c60) | 9 | UTF-8 | 同時有 TWD97 與 WGS84 | 營業時間、租借費率、免費飲水／打氣（**可以拿來驗證座標轉換**） |

### 3.1 長輩服務：避難、照顧家人、打疫苗做篩檢（2026-11-07 實際下載，作品 repo 已接進代理）

都沒有座標，用行政區（或里）篩選。代理 id 寫在括號裡。

| 資料集 | 筆數 | 編碼 | 行政區怎麼來 | 注意 |
|---|---|---|---|---|
| [可供避難收容處所一覽表](https://data.taipei/dataset/detail?id=aaf97773-3631-40e2-b3cc-da87bf2ce1d5)（`shelters`） | 419 | **ODS 試算表**（目錄寫 CSV） | 「鄉鎮」欄位 | 第一張工作表「清冊」才是清單，第二張是里名譯名；檔尾 2 列加總沒有編號。「服務里別」列出負責的里，用台北通帳號的 `village` 就能對到。水災、震災的值是「是／否／備用」。**有聯絡人、管理人的姓名與電話，代理不傳給前端** |
| [失智症篩檢、確診評估及關懷服務計畫合約醫院](https://data.taipei/dataset/detail?id=1417e9ae-4c86-4f74-88a2-d7031712db44)（`dementia-screening`） | 11 家 | UTF-8 BOM | 醫院地址 | ⚠️ **左右兩份清單並排**：「12區健康服務中心」＋電話是 12 區健康服務中心，右邊醫院欄位是另一份清單，同一列沒有對應（例如「萬華區」那列是北投的關渡醫院、「北投區」那列醫院是空的）。只能當全市清單用 |
| [長照喘息服務特約單位](https://data.taipei/dataset/detail?id=959c34b2-9698-4d99-8987-d389efe18c04)（`ltc-respite-providers`） | 巷弄式 26、社區式 56、居家式 165、住宿式 65 | Big5 | 行政區域代碼 | 4 個資源。「服務區別」大多是「全區」，要依服務範圍篩，不能用地點篩。住宿式含新北市機構（65000…），代理沒收 |
| [家庭照顧者服務中心](https://data.taipei/dataset/detail?id=e3cec007-4212-4944-989e-5078e4f5f3bb)（`caregiver-centers`） | 4 | UTF-8 BOM | 地址 | 東西南北 4 區中心，全市都列 |
| [健康服務中心](https://data.taipei/dataset/detail?id=d4c6d4e0-c2b4-48e3-99b4-f670d820326b)（`health-centers`） | 12 | Big5 | 「行政區」欄位是代碼（63000040） | 有網址 |
| [流感疫苗合約醫療院所(成人)](https://data.taipei/dataset/detail?id=0db13d34-51e3-497a-a023-286d5ef692ea)（`flu-vaccine-adult`） | 382 | UTF-8 BOM | 行政區域代碼 | 有「語音預約」欄位（多數是空的） |
| [公費肺炎鏈球菌疫苗合約醫療院所名單](https://data.taipei/dataset/detail?id=92934ab2-3509-4a6b-9cee-9ac556ca2f65)（`pneumococcal-vaccine`） | 288 | UTF-8 BOM | 行政區域代碼 | |
| [五癌篩檢醫療院所](https://data.taipei/dataset/detail?id=ae20d75c-dffb-4d4f-85e1-9c512189005c)（`cancer-screening`） | 481 | UTF-8 BOM | 「行政區」欄位是代碼 | 子宮頸癌、口腔癌、大腸癌、乳癌、肺癌各一欄（Y／空白），「貼心小提醒」是官方提醒文字 |
| [假牙補助醫療院所名單](https://data.taipei/dataset/detail?id=76b8b514-e793-4cca-8dcf-065d5af4b760)（`denture-clinics`） | 6 | Big5 | 地址（「區域」欄位是院區所在區） | 聯醫 6 院區；資格與流程見 `taipei-subsidies.md` A.12 |

### 3.2 公車預估到站（M16，2026-11-07 實測，作品 repo 的 `/api/bus/*`）

data.taipei 的資料集頁面只放一份說明用的小 CSV，真正的資料在臺北市公運處的 blob（gzip 壓縮的 UTF-8 JSON，回應沒有 `Content-Encoding`，也沒有 CORS 標頭，只能從伺服器端抓再自己解壓）。臺北是 `https://tcgbusfs.blob.core.windows.net/blobbus/<檔名>`，新北把 `blobbus` 換成 `ntpcbus`。

| 檔案 | 資料集 | 大小（gz／解壓） | 用途 |
|---|---|---|---|
| `GetEstimateTime.gz` | [臺北市預估到站時間(公車)](https://data.taipei/dataset/detail?id=f11a5af0-7b37-48ef-98cc-f6f102ed43c6)、[新北市預估到站時間](https://data.taipei/dataset/detail?id=1e26ecf6-d5b4-494b-b94f-bee64938dd64) | 157 KB／2 MB | 即時預估，**每 15～20 秒更新**（說明 CSV 寫「每年」是指規格） |
| `GetRoute.gz` | [臺北市路線](https://data.taipei/dataset/detail?id=6a03b03d-90d1-4d9e-a952-c940fd869772)、[新北市路線](https://data.taipei/dataset/detail?id=1f5998d2-d9e4-4d9f-8cbb-fe2d29b99c3c) | 77 KB／1 MB | RouteID → 路線名、起訖站。同一個 Id 會因聯營、附屬路線重複，要去重 |
| `GetStop.gz` | [臺北市站牌](https://data.taipei/dataset/detail?id=62bc76da-6e6b-46ee-8976-c1945092d504)、[新北市站牌](https://data.taipei/dataset/detail?id=010244b7-c4ed-4b03-9436-c6cbe634d483) | 1.4 MB／9.4 MB | StopID → 站名、站序、方向 |

- **一個 StopID 就是「某路線、某方向、某一站」**（全檔不重複）。設定只要記 `{ 市別, RouteID, StopID }`；不能只用站名＋路線＋方向（環狀路線同方向就有同名站）。
- **方向看站牌檔的 `goBack`**（0 去程「往 destinationZh」、1 返程「往 departureZh」）。預估檔的 `GoBack` 是「車子目前在跑哪個方向」，實測有 2,929 筆和站牌方向不同，不能拿來判斷。
- `EstimateTime` 是字串、單位秒；`-1` 尚未發車、`-2` 交管不停靠、`-3` 末班車已過、`-4` 今日未營運（公運處〈臺北市Data.Taipei平台API說明文件〉V6.3）。
- 臺北、新北兩份的 RouteID、StopID 沒有交集；307 在臺北那份（RouteID 16111），新北主管的路線（例如藍1）只在新北那份。
- ⚠️ 資料集頁面直接列的 `TstStop.json` 只有 1 筆範例、`TstRoute.json` 停在 2025-12，不能用；一律用 `Get*.gz`。
- ⚠️ 站牌裁撤後 StopID 會消失（預估檔有 571 筆在站牌檔找不到），查不到時請家人重新設定。
- 〈臺北市敬老愛心卡補助搭乘公車捷運路線表〉停在 2025-06，起迄站以路線檔為準。

## 4. 不建議使用（名稱和內容不符）

| 資料集 | 問題 |
|---|---|
| 各區戶政事務所等候人數 | CSV 只有戶所地址、電話、網址，**沒有等候人數** |
| 臺北市立聯合醫院門診進度查詢 | 只有各院區的查詢網址，沒有進度資料 |
| 各運動中心場地開放使用情形 | 年度統計，不是即時人數 |
| 夜間急診動物醫院 | 沒有座標，最後更新 2024-12 |

---

## 5. 題目方向（依資料組合）

| 方向 | 資料組合 | 備註 |
|---|---|---|
| **「急了，附近哪裡有？」** | 哺集乳室 + AED + 友善店家（行動裝置充電）+ 公廁 + 飲水機 | 和指引 #36 的案例二完全對應（哺乳、AED、行動電源）。哺集乳室沒有座標，要先處理地址 |
| **垃圾車到哪了／提醒倒垃圾** | 垃圾車點位路線（抵達時間）+ 限時收受點 | 搭配 App 的 `notify` 或自訂 Handler 做本機排程提醒（類似往屆 ParkFlow 的做法） |
| **親子出門地圖** | 親子友善廁所 + 共融式遊戲場 + 哺集乳室 + 公園 + 飲水機 | 主要使用者明確：帶小孩的家長 |
| **無障礙出行** | 捷運無障礙電梯／坡道 + 無障礙異常公告 + 公廁（無障礙廁座）+ 友善店家（無障礙） | 呼應城市通的無障礙設計（指引 #30） |
| **停車** | 停車場剩餘車位 + 描述 | 往屆 2024 ParkFlow 已經做過，要找出差異化 |
| **YouBike** | YouBike 即時 + 今日施工 + AQI | 往屆 2025 RideFlow 已經做過，要找出差異化 |

> 任何題目的 README 都要寫出資料集名稱、連結和授權。非核心資料可以用模擬資料，但要標示清楚。
