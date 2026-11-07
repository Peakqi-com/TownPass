# CLAUDE.md — TownPass（城市通）參賽專案

本 repo 是「2026 臺北秋季程式設計節 · 城市通微服務大黑客松」的參賽專案，以 [taipei-doit/TownPass](https://github.com/taipei-doit/TownPass) main（2026/10，Flutter 3.47.6）為基礎。
規則來源：`2026 城市通入門指引 2.html`（賽前工作坊投影片，2026/10/25）與競賽須知（115.08.27 版）。

回應一律使用繁體中文（台灣用語）。

---

## 0. 最高原則：技術棧不得超出指引範圍

**本專案只能使用下面「允許清單」裡的技術。** 清單外的語言、框架、套件、雲端服務、AI 模型，一律**先停下來問使用者**，不得自行引入；即使只是「順手裝一個小工具」也一樣。

新增任何依賴前必須確認：
1. 在允許清單內，或已經得到使用者同意
2. 開源且免費，授權為 **MIT／BSD／Apache-2.0**（可納入 AGPL 專案）。標示「僅供個人使用」「不得再散布」的套件禁用
3. 把「套件名稱＋授權」記到 README 的第三方套件清單

### 0.1 允許清單

| 層 | 允許 | 備註 |
|---|---|---|
| App | Flutter **3.47.6**（FVM，見 `.fvmrc`）、Dart ≥ 3.13 | iOS 最低 15（UIScene、SPM）；Android AGP 9.1.0、Kotlin 2.4.0、Gradle 9.3.1、Java 17 |
| App 狀態／路由 | 沿用現有的 GetX、`TPRoute` | 不要另外引入 Riverpod、Bloc、go_router 等 |
| App 新套件 | pub.dev 上 MIT／BSD／Apache 的套件 | iOS 優先選支援 Swift Package Manager 的（CocoaPods 已進入維護模式） |
| App 新套件（已核准） | **flutter_tts**（MIT，`speak` Handler）、**speech_to_text**（BSD-3-Clause，`listen` Handler） | 2026-11-07 隊長核准。speech_to_text 一定要用 `onDevice: true`，並先檢查裝置是否支援離線辨識，不支援就回錯誤，**不可退回雲端辨識** |
| 微服務新套件（已核准） | **qrcode**（MIT，家人代設定產生 QR code） | 2026-11-07 隊長核准 |
| 微服務前端 | **Vue 3 + Vite + Pinia + Tailwind + TypeScript**（官方範例）；React；**Next.js（React）**；純 HTML／CSS／JS | 必須能在 WebView 中執行。指引原文：「語言、框架不限」 |
| 後端（選配） | Java：**Spring Boot 4.x + Java 21 + Maven**（指引範例；競賽須知列 Spring、Hibernate、Tomcat）；Python：FastAPI、Flask（往屆得獎作品）；Node：**Next.js Route Handlers**（和前端同一個專案） | 指引原文：「語言不限」。一定要附 `Dockerfile`（「可移轉、可維運、可上架」）；埠號讀環境變數 `PORT`；前後端不同網域時要設定 CORS |
| 資料庫 | **指引未指定**（只有 #49 寫「一般後端：登入、資料庫…」屬於允許事項；#11 提到 Hibernate） | 選型前**先問使用者**。條件：免費、開源、可移轉（建議用 PostgreSQL／MySQL 之類，附 Docker 設定）。能直接即時抓開放資料的話，就不需要資料庫 |
| 地圖 | **Leaflet** 或 **MapLibre**，搭配 **OpenStreetMap** 或**國土測繪中心**圖資 | **禁用** Google Maps、`google_maps_flutter`、Mapbox |
| 圖表 | 開源、免費的套件（指引沒指定，選用前先問） | |
| 裝置端 AI | **flutter_edge_ai**（原 flutter_gemma，MIT）、**llamadart**（MIT）；模型 Gemma 4 E2B／E4B、Gemma 3n、Phi-4 Mini | 見 §0.2 |
| 傳統 ML | 往屆用過 XGBoost（開源） | 推論同樣不能呼叫雲端 |
| 前端部署 | Firebase Hosting、GitHub Pages、Cloudflare Pages、**Vercel** | 一定要 HTTPS；只能用免費方案。指引原文：「部署平台不限，請使用免費方案」 |
| 後端部署 | **Cloud Run，區域 `asia-east1`**（`gcloud run deploy --source .`）、Render、Fly.io、**Vercel（限 Next.js 一體式架構）**；比賽期間可用 ngrok | 映像檔推到 Artifact Registry（`pkg.dev`）。`gcr.io`（Container Registry）已在 2025/3 停止服務，不要再用。用 Vercel 的條件見 `docs/townpass/deployment.md` §3 |
| 開發工具 | VS Code（或 AI 編輯器）、Android Studio、Xcode、FVM、Git、Docker、Postman、Chrome DevTools | |
| 開放資料 | **data.taipei**（優先）、data.gov.tw、TDX（tdx.transportdata.tw，要申請金鑰）、臺北城市儀表板 | |

### 0.2 AI 規範（競賽須知 AI 使用規範）

- **開發階段**：可以用雲端 AI（Claude Code 等）來企劃、寫程式、除錯、整理資料。
- **執行階段**：作品執行時，所有 LLM／模型推論都**必須在裝置端完成**。不可呼叫任何雲端推論 API 或遠端模型（OpenAI、Anthropic、Gemini API 等都不行），處理使用者輸入的推論也一樣。
- 評審可能**關閉網路**現場出題來驗證，所以 AI 功能必須能離線運作。Demo 前要用飛航模式完整測一次。
- **禁用**「危害國家資通安全清單」上的 AI 工具與模型（含大陸廠牌，例如 DeepSeek、Qwen 系列）。
- 建議架構：網頁 `postMessage({name:'llm_ask'})` → App 的自訂 Handler → 裝置端推論 → 回傳結果。開放資料可以放進 prompt（RAG）。
- README 必須揭露：**模型名稱、版本、量化格式、推論框架、來源**。
- 允許事項：一般後端（登入、資料庫、檔案、排行榜、同步），以及**預先生成**的固定文字、圖片、程式碼（要如實說明）。

### 0.3 資料規範

- 核心資料必須是**合法的開放資料**，並註明出處；非核心資料可以用模擬資料，但要標示清楚。
- README 和 Demo 要寫出資料集名稱與連結。
- **AI 產生的 API 網址、資料集名稱、欄位都要實際打開來源確認**，禁止憑印象編造。

### 0.4 授權與繳交

- 參賽作品放在**公開 repo**，授權 **AGPL-3.0**，並附上主辦指定的授權聲明；得獎公布後要保持公開至少一年。（TownPass 本體是 GPL-3.0。）
- 繳交項目：所有原始碼（微服務、後端、修改過的 TownPass）、LICENSE、README（照著做就能建置）、資料來源清單、第三方套件清單（名稱＋授權）、AI 模型揭露。
- 不要 commit 金鑰（TDX key、Firebase 設定等），改用環境變數或 `.env`，並列入 `.gitignore`。

---

## 1. 常用指令

```bash
fvm install                                              # 依 .fvmrc 安裝 Flutter 3.47.6
fvm flutter pub get
fvm dart run build_runner build --delete-conflicting-outputs   # 產生 lib/gen/assets.gen.dart 與 JSON 序列化
fvm flutter run
fvm flutter analyze
fvm flutter clean                                         # Android build 出問題時先試這個
```

- `*.gen.dart` 已列入 `.gitignore`。新增 SVG／mock 檔或修改 `@JsonSerializable` model 之後，都要重跑 build_runner。
- 沒有 FVM 的話，把指令開頭的 `fvm` 拿掉，並確認 `flutter --version` 是 3.47.6。

## 2. 專案結構與常改的位置

```
lib/
├─ bean/        資料模型（json_serializable）
├─ page/        各頁面；city_service/ 是「服務」頁，city_service_edit/ 是編輯置頂
├─ service/     帳號（讀 mock）、定位、通知、裝置資訊、SharedPreferences
├─ util/        TP 元件（tp_colors、tp_text_styles、tp_button…）、tp_web_view、web_message_handler/
└─ gen/         build_runner 產生（不進版控）
assets/mock_data/  account.json 等 5 個假資料
assets/svg/        108 個圖示（snake_case）
```

| 要做的事 | 位置 |
|---|---|
| 新增服務 | `lib/page/city_service/model/my_service_model.dart` |
| 熱門區塊 | `lib/page/city_service/model/trending_service_model.dart` |
| 服務拼貼四張卡 | `lib/page/city_service/widget/official_service_card/` |
| 預設置頂 | `lib/page/city_service/widget/pinned_service_widget_controller.dart` |
| 擴充 App 能力（Handler） | `lib/util/web_message_handler/` |
| 切換測試帳號 | `assets/mock_data/account.json`（改完要**重啟** App） |

## 3. 詳細文件（動手前先讀）

- 新增服務、雙向溝通、自訂 Handler、WebView 注意事項：[`docs/townpass/adding-a-service.md`](docs/townpass/adding-a-service.md)
- UI 設計系統（Figma UI Kit、色票、字級、無障礙、Figma MCP 讀取流程）：[`docs/townpass/design-system.md`](docs/townpass/design-system.md)
- 後端與部署（Firebase／Cloud Run／Next.js + Vercel、串回城市通）：[`docs/townpass/deployment.md`](docs/townpass/deployment.md)
- 開放資料（data.taipei 已驗證的 30 個資料集、編碼／座標／CORS 問題、題目方向）：[`docs/townpass/open-data.md`](docs/townpass/open-data.md)。找新資料集時先搜尋 `docs/townpass/open-data/data-taipei-catalog.csv`（全部 2,816 筆）
- 往屆得獎作品（2024、2025 共 12 件的點子、技術、今年規則下的踩線點與發想觀察）：[`docs/townpass/past-winners.md`](docs/townpass/past-winners.md)
- **長輩模式功能規格（開發時以這份為準）**：模組、服務清單 JSON 規格、介面規範、架構與串接流程、開發順序：[`docs/townpass/elder-mode-spec.md`](docs/townpass/elder-mode-spec.md)
- 本屆題目「數位平權 × 友善共融／用不了」的用戶研究（三份，每條主張標 ✅ 已查證／⚠️ 未查證；未查證的不可寫成「研究指出」）：
  - 長輩、視障、聽障的使用障礙、WCAG 規範、**WebView 技術限制**（TTS／語音辨識／麥克風／字級放大）：[`docs/townpass/accessibility-research.md`](docs/townpass/accessibility-research.md)
  - 長輩的數位習慣、臺北市近四年長者服務、微服務做法：[`docs/townpass/taipei-elderly-services.md`](docs/townpass/taipei-elderly-services.md)
  - 視障、聽障的使用習慣、臺北市相關服務與溝通管道、微服務做法：[`docs/townpass/taipei-disability-services.md`](docs/townpass/taipei-disability-services.md)

## 4. 開發慣例

- **UI 一律照 Figma「Town Pass UI Kit」**。Flutter 端使用 `TPColors`、`TPTextStyles`、`TPText`、`TPButton`、`TPAppBar` 等既有元件，不要寫死色碼和字級；微服務網頁使用同一組 token（CSS 變數或 Tailwind config）。詳見 design-system.md。
- 無障礙：觸控目標 ≥ 48×48、文字放大到 200% 仍可閱讀、圖示要有語意標籤、每頁一個 AppBar 標題、不使用閃爍內容。
- 自訂 Handler 的 `name` 不可和內建的 9 個重複（見 adding-a-service.md §3）。
- 套件或版本資訊不確定時，以 `pubspec.yaml`、`pubspec.lock` 和官方文件為準，不要依賴模型記憶（Flutter 3.47、AGP 9 都很新）。
- 寫出來的程式碼要讓隊員看得懂；決選有問答環節，評審會問到設計考量。
- Demo 流程：開啟 App → 服務 › 更多 → 找到服務 → 完成一條流程 → 回到首頁。一律用實機測試。
