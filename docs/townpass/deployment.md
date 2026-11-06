# 後端與部署

> 整理自《2026 城市通入門指引》#53～#58（含講者備註），並補上「Next.js + Vercel」路線的分析。

---

## 1. 規則到底限制了什麼

指引對**平台和框架都沒有指定**，原文如下：

- 前端（#10）：「微服務前端不限語言與框架，只要能在 WebView 中執行即可；官方範例採用 Vue 3 + Vite + Pinia + Tailwind，可作為參考」
- 後端（#9）：「需要存資料或處理邏輯時再加入，語言不限」
- 部署（#54）：「平台不限，GitHub Pages、Render 等亦可」；頁尾：「部署平台不限，請使用免費方案」

真正的硬限制只有這幾條：

| 限制 | 出處 |
|---|---|
| 必須 **HTTPS** | #54（前端「須支援 HTTPS」） |
| 只能用**免費方案** | #54 頁尾 |
| **可移轉、可維運、可上架**：資訊局拿到 repo 後要能自己執行與維運，「準備 Dockerfile 即可達成」 | #54 |
| 執行期間**不能呼叫雲端 AI 推論** | 第 06 章 |
| 套件要開源、免費（MIT／BSD／Apache） | #5、#21 |

所以 **Next.js + Vercel 沒有違反任何一條規則**。指引的 Firebase + Cloud Run 只是「示範路線」，不是唯一選項。

---

## 2. 路線 A：指引的示範路線（Vue SPA + Firebase Hosting + Cloud Run）

```
Vue 3 SPA ──build──► Firebase Hosting（https://xxx.web.app）
                            │ fetch（跨網域，要設定 CORS）
Spring Boot / FastAPI ──►  Cloud Run asia-east1（https://xxx.asia-east1.run.app）
```

### 2.1 前端：Firebase Hosting（#55）

```bash
npm install -g firebase-tools && firebase login
firebase init hosting     # public 填 dist（Vite）；single-page app 選 Yes；覆蓋 index.html 選 No
npm run build && firebase deploy --only hosting
```

### 2.2 後端：Cloud Run（#56）

```bash
gcloud auth login && gcloud config set project [PROJECT-ID]
gcloud run deploy my-service --source . --region asia-east1
# 第一次執行會問：啟用 API → y；允許未驗證存取 → y
```

- `--source`：由 Cloud Build 在雲端建置。有 Dockerfile 就照 Dockerfile 建，沒有就用 buildpacks 自動判斷語言，再推到 Artifact Registry。
- **`gcr.io` 已在 2025/3 關閉**，去年的 `docker build -t gcr.io/…` 教學不能再用。
- `asia-east1` 在彰化，是臺灣延遲最低的區域。
- 依請求計費，閒置時不收費。

### 2.3 Spring Boot 範例（#57）

```dockerfile
FROM eclipse-temurin:21-jdk AS build
WORKDIR /app
COPY . .
RUN ./mvnw -q package -DskipTests

FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=build /app/target/*.jar app.jar
ENV PORT=8080
CMD ["java", "-jar", "app.jar"]
```

四個重點：
1. 用 start.spring.io 建立專案：Spring Boot 4.x、Java 21、Maven，加入 Spring Web
2. 寫 `@RestController`，例如 `GET /hello`
3. `application.properties` 設 `server.port=${PORT:8080}`，因為 Cloud Run 會用 `PORT` 指定埠號
4. **設定 CORS**：網頁在 `web.app`、API 在 `run.app`，屬於不同網域

---

## 3. 路線 B：Next.js 一體式 + Vercel

```
Next.js（App Router）
 ├─ app/**/page.tsx        前端頁面（在 WebView 裡跑）
 └─ app/api/**/route.ts    後端 API（Route Handlers）
        └──► Vercel Hobby（https://xxx.vercel.app）
```

### 3.1 優點

- 前後端在**同一個 repo、同一次部署**，比賽時間緊的時候省事
- 頁面和 API 同網域，**不需要設定 CORS**
- API key（例如 TDX）可以放在 server 端的環境變數，不會外洩到網頁
- 前端用的是 React，指引 #10 明列 React 可以用

### 3.2 必須遵守的條件

| # | 條件 | 原因 |
|---|---|---|
| 1 | **一定要附 `Dockerfile`**（`output: 'standalone'`），並在 README 寫清楚怎麼在 Cloud Run 或任何容器環境跑起來 | 「可移轉、可維運」：得獎後資訊局要自己接手部署 |
| 2 | **不使用 Vercel 專屬服務**：Vercel KV、Blob、Postgres、Edge Config 等 | 會綁死平台，資訊局無法移轉 |
| 3 | **不用 Vercel AI SDK 去呼叫雲端模型**（OpenAI、Anthropic、Gemini…） | 違反「執行時推論須在裝置端」 |
| 4 | 只用 **Hobby 免費方案** | 免費規則。Hobby 條款限非商業用途，比賽期間可用；整併後由資訊局自行部署 |
| 5 | Function 區域設成離臺灣近的地方，例如 `vercel.json` 設 `"regions": ["hnd1"]`（東京）或 `"hkg1"`（香港） | Vercel 沒有臺灣區，預設是美東，延遲很高 |
| 6 | 不要依賴本機檔案系統存資料 | Serverless 環境沒有持久化磁碟（Cloud Run 也一樣）。指引**沒有指定資料庫服務**，選型前**先問使用者**（必須開源、免費、可移轉） |

### 3.3 Next.js 在 WebView 裡的坑

- **`window.flutterObject` 只存在於瀏覽器端**。呼叫 App 的程式碼一定要放在 `'use client'` 元件的 `useEffect`（或事件 handler）裡，不能在 server component 或 SSR 階段存取 `window`。
- 雙向溝通 helper 直接用 `adding-a-service.md` §3.2 的 `callApp()`。
- 如果完全不需要 API，可以改用 `output: 'export'` 輸出成純靜態檔（`out/`），部署到 Vercel 或 Firebase Hosting 都可以。

### 3.4 Dockerfile 範例（standalone）

```js
// next.config.js
module.exports = { output: 'standalone' };
```

```dockerfile
FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-alpine
WORKDIR /app
ENV NODE_ENV=production PORT=8080 HOSTNAME=0.0.0.0
COPY --from=build /app/.next/standalone ./
COPY --from=build /app/.next/static ./.next/static
COPY --from=build /app/public ./public
CMD ["node", "server.js"]
```

這個映像檔可以直接 `gcloud run deploy --source . --region asia-east1`，等於同一份程式碼兩條路都能走。

---

## 4. 怎麼選

| 情況 | 建議 |
|---|---|
| 隊伍熟 Vue，或想直接用官方範例的 composables 和 Tailwind 設定 | 路線 A |
| 隊伍熟 React／Next.js，想一個專案搞定前後端 | 路線 B（遵守 §3.2） |
| 有 Java／Python 專長，或需要重運算（例如 XGBoost 預測） | 前端任選，後端用 Cloud Run |
| 只有靜態頁面，資料直接從開放資料 API 抓 | 不需要後端。前端直接部署，但注意開放資料 API 有沒有開 CORS；沒開的話還是需要一層後端代理 |

不管選哪一條：**賽前先部署一個 Hello World**，把網址填進 `destinationUrl`，在 App 內測過一次。

---

## 5. 串回城市通（#58）

1. 把 `my_service_model.dart` 的 `destinationUrl` 改成正式網址，例如 `https://xxx.web.app/` 或 `https://xxx.vercel.app/`
2. 用 `fvm flutter run` 安裝到**實機**（模擬器也可以，但定位、掃碼、通知只有實機能完整呈現）
3. 服務 › 更多 › 加入我的服務，打開服務，確認雙向溝通正常
4. 完整跑一次流程：開啟 App → 找到服務 → 完成操作 → 回到首頁（這就是 Demo 的流程）

Demo 用的手機要事先裝好 App、加好服務，並確認網路正常。置頂清單重啟後會重置，見 `adding-a-service.md` §6.3。
