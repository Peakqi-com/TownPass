# 往屆得獎作品整理（2024、2025）

> 整理日期：2026-11-07。名次依 [taipei-doit](https://github.com/taipei-doit?tab=repositories) 各 repo 的描述（例如「第一名得獎團隊：Wee Won」），作品內容整理自各 repo 的 README 與目錄結構。
>
> 城市通微服務黑客松從 **2024 年**開始舉辦（TownPass repo 建立於 2024/8）。2023 年秋季的是「城市儀表板黑客松」，主題不同，因此不列入。

---

## 1. 冠軍作品

### 2024 第一名：捐血資訊整合服務（團隊：Wee Won）

repo：[taipei-doit/townpass2024-blood-donation](https://github.com/taipei-doit/townpass2024-blood-donation)

**點子**：用公益加遊戲化來鼓勵市民捐血。

| 功能 | 說明 |
|---|---|
| 捐血查詢 | 顯示血庫即時庫存；在地圖上標出捐血室、捐血車和使用者位置 |
| 捐血場所 | 列出附近 1 公里內的捐血點，附距離、營業時間、電話和當期活動 |
| 個人紀錄 | 推算下次可以捐血的日期，記錄每次捐血的時間和地點 |
| 吉祥物「小血怪」 | 每捐一次血就累積經驗值，小血怪會長大；可以餵牠、摸頭；另有成就徽章 |
| 捐血優惠 | 整合周邊商家的優惠（資料是從 PTT 省錢版爬下來後整理的） |
| 捐血聯誼 | 連結區公所的單身聯誼活動 |

**技術**：前端 Next.js（Pages Router）、Tailwind、SCSS、Mapbox；後端 FastAPI 加 PostgreSQL（附 Dockerfile）；`crawler/` 放爬蟲用的 notebook 和整理好的 CSV；另外改了 Flutter App（定位、推播）。

### 2025 第一名：詐騙及風險網站檢測（團隊：DROP TABLE）

repo：[taipei-doit/townpass2025-url-risk-analyzer](https://github.com/taipei-doit/townpass2025-url-risk-analyzer)

**點子**：民眾貼上一個網址，服務告訴他這個網址可不可信，並附上判斷依據。

**做法**：分三層檢測，加總成 0–100 分：

1. 比對 PhishTank 已確認的釣魚網址，通過加 25 分
2. Random Forest 模型判斷（用 UCI Phishing Websites 資料集訓練，25 個特徵，準確率約 95%），通過加 25 分
3. 查 WHOIS 網域年齡、DNS 和主機所在地；政府和學術網站直接給 100 分，其他安全網站加 35 分

分數分成四級建議：< 50 高度風險；50–84 建議謹慎；85–99 基本安全但建議謹慎；100 是政府或學術網站。

**技術**：直接在 Flutter 寫原生頁面 `page/anti_fraud/anti_fraud_view.dart`，沒有用 WebView；後端 Flask，用 Redis 快取檢測結果（存 1 小時），讓回應從 5 秒以上縮到 1 秒內。README 附有 mermaid 架構圖、時序圖和快取策略說明。README 也自己寫明「**無使用政府資料**」。

---

## 2. 其他得獎作品

| 年 | 名次 | 作品 | 點子 | 技術重點 |
|---|---|---|---|---|
| 2024 | 2 | [recycling](https://github.com/taipei-doit/townpass2024-recycling)（光頭的朋友們） | 拍照或打字問垃圾怎麼分類，加上垃圾車地圖和優惠券 | Vue（atoms／molecules／organisms 分層）、Express |
| 2024 | 3 | [parking](https://github.com/taipei-doit/townpass2024-parking) ParkFlow | 找車位、查附近黃線，停車後計時，快到時推播提醒 | Vue 3、FastAPI、App 端自訂 `timer_set` Handler |
| 2024 | 佳作 | [weather](https://github.com/taipei-doit/townpass2024-weather) 即時雨晴 | 以所在地為中心顯示雷達回波，加上未來 1 小時雨量預測 | Flask、純 HTML/JS、Leaflet + OSM |
| 2024 | 佳作 | [venue-rental](https://github.com/taipei-doit/townpass2024-venue-rental) 有球必in | 台北球場租借，加上線上組隊 | data.gov.tw 球場資料集 |
| 2024 | 佳作 | [welfare](https://github.com/taipei-doit/townpass2024-welfare)（MSP Player） | 從名稱看是社福相關；README 只有 Vite 範本，沒有說明 | React + Vite |
| 2025 | 2 | [carbon-notebook](https://github.com/taipei-doit/townpass2025-carbon-notebook) 咔嘣筆記 | 用電子發票載具和 GPS 交通模式自動算碳排，用「地球心情」遊戲化呈現 | Next.js 15、MapLibre、Hono、Prisma、Postgres；發票 API 是 Mock |
| 2025 | 3 | [stampquest](https://github.com/taipei-doit/townpass2025-stampquest)（假面喵喵隊） | 集章活動數位化：NFC、問答、優惠券三種集章方式，再加上類似 AirTag 的方向和距離尋寶 | React 19、FastAPI、PostgreSQL；說明在 `README.stamp.md` |
| 2025 | 佳作 | [RideFlow](https://github.com/taipei-doit/townpass2025-RideFlow) 騎妙 | 告訴你現在適不適合騎 YouBike，並預測目的地站 15／30／45 分鐘後的空位 | Vue 3、FastAPI、XGBoost |
| 2025 | 佳作 | [cloud-temple](https://github.com/taipei-doit/townpass2025-cloud-temple) 城心誠靈 | 搖手機抽籤、擲筊、線上拜拜，最後推薦台北廟宇和周邊景點 | Flutter、加速度感測器、觀光局 API |
| 2025 | 佳作 | [art-pass](https://github.com/taipei-doit/townpass2025-art-pass) 藝文足跡 | 整合文化快遞的展演資訊，加上地圖和藝術護照時間軸 | Next.js 16、FastAPI、Leaflet + OSM |

ParkFlow、RideFlow、即時雨晴已經整併進台北通，詳細介紹見入門指引 #41–#45。

---

## 3. 觀察（給今年發想題目用）

### 3.1 冠軍的共同點：在「有用」之外多了情感或信任的鉤子

- **2024 捐血**：功能本身是查詢，真正讓人記住的是「小血怪」養成、徽章和聯誼，把一次性的行為變成持續參與的動機。
- **2025 防詐**：題目是高痛點、人人有感的議題，而且一句話就說得清楚：「這個網址能不能信」。
- 兩者都符合指引 #45 歸納的「需求一句話說得清楚、主流程單純」。

### 3.2 2025 冠軍在今年規則下會踩線，不能照抄

| 問題 | 今年規則 |
|---|---|
| ML 推論在後端執行（Flask + Random Forest） | CLAUDE.md §0.2：所有模型推論必須在裝置端完成，傳統 ML 也一樣不能呼叫雲端；評審可能關閉網路驗證 |
| 「無使用政府資料」 | CLAUDE.md §0.3：核心資料必須是合法的開放資料，並註明出處 |
| 呼叫 PhishTank、WHOIS 等外部服務 | 不是推論的話可以用，但離線時要有退路 |

如果想做類似的題目，可以考慮：模型改成在裝置端執行；核心資料改用政府開放資料（例如 165 反詐騙相關資料集，**使用前要實際查證確實存在**）。

### 3.3 地圖選擇

2024 冠軍用 Mapbox，2025 RideFlow 用 Google Maps，這兩個今年都**禁用**，要改用 Leaflet 或 MapLibre。2025 年的 art-pass、carbon-notebook 已經用開源地圖，可以參考它們的寫法。

### 3.4 遊戲化與集章是評審買單的方向，但撞題風險高

10 多件得獎作品裡，有 4 件用了「累積、收集」的機制：捐血（小血怪、徽章）、碳排（地球心情）、集章（stampquest）、藝文（藝術護照）。這代表評審接受這個方向，但今年很可能有多隊做類似的東西，**要有明確的差異點**。

### 3.5 善用 App 的原生能力是加分項

推播（ParkFlow 的 `timer_set`）、定位（即時雨晴）、加速度感測器（城心誠靈）、NFC（stampquest），以及 2025 冠軍直接在 Flutter 寫原生頁面，都是 WebView 做不到的體驗。今年還多了裝置端 AI 可以用。

### 3.6 README 的寫法也是評分的一部分

2025 年的作品明顯照著主辦的 README 範本寫：專案簡介、架構圖、Tech Stack 表、安裝方式、功能與資料來源表。冠軍還多寫了快取策略和模型規格。2024 年有幾件作品的 README 只有預設範本，結果停在佳作。這只是相關，不一定是因果，但完整的 README 確實有助於整併。

### 3.7 咔嘣筆記是和我們同架構的先例（Next.js + Vercel + Dockerfile）

`taipei-doit/townpass2025-carbon-notebook` 只是一個殼，實際程式碼放在兩個 submodule：[face-on-keyboard/web](https://github.com/face-on-keyboard/web) 和 [face-on-keyboard/townpass](https://github.com/face-on-keyboard/townpass)。查 `web` repo 的結果（2026-11-07）：

- **部署在 Vercel**：GitHub Deployments 紀錄是 `vercel[bot]` 建立的 Production／Preview；repo 的 homepage 寫 `https://codefest.cwh.me`，但這個網域現在已經解析不到。
- **有附 Dockerfile**：用 Next.js 官方的 standalone 範本（`node:22-alpine` 多階段建置，`next.config.js` 設 `output: 'standalone'`，容器跑 `node server.js`、`PORT=3000`）。
- **docker-compose.yml 只啟動資料庫**（PostGIS 16），沒有包含 web 服務本身。
- **後端寫在 Next.js 裡**：Hono 掛在 `src/app/api/[[...route]]/route.ts`（catch-all Route Handler），和我們規劃的「Next.js Route Handlers 一體式」相同；資料庫用 Prisma + Postgres。
- 主辦方的殼 repo README 完全沒提到 Vercel 或 Dockerfile，要點進 submodule 才看得到。

可以借鏡：Vercel 負責 Demo，Dockerfile 證明「可移轉」，兩者可以並存。可以避免：README 沒寫部署方式；Dockerfile 的 `ENV PORT=3000` 是寫死的（Cloud Run 會注入 `PORT`，其實沒問題，但建議在 README 說明）；`typescript.ignoreBuildErrors: true` 會讓評審問到程式品質。

---

## 4. 資料來源

- 得獎 repo 列表：<https://github.com/taipei-doit?tab=repositories>
- 2024 冠軍報導：<https://hao.cnyes.com/post/108444>
- 2023 年是城市儀表板黑客松（不同賽事）：<https://doit.gov.taipei/ct.aspxItem=44376&ctNode=5601&mp=121001>、<https://www.storm.mg/article/11042748>
- 入門指引 #41–#45（往屆作品介紹）：根目錄 `2026 城市通入門指引 2.html`
