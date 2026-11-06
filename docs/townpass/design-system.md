# 城市通設計系統（Town Pass UI Kit）

> 來源：《2026 城市通入門指引》#28～#30、#47；`lib/util/tp_colors.dart`、`lib/util/tp_text_styles.dart`；Town Pass 開發文件〈無障礙設計〉（tpe-guideline.web.app/docs/accessibility/）。
> 所有介面開發（Flutter 端與微服務網頁端）都必須照這份文件做。

---

## 1. 原則

1. **視覺依據 = Figma「城市通 Town Pass Open Source Gov Mobile App UI kit and design system」**
   - URL：<https://www.figma.com/design/lIjV2gObcion4O2nbOvEe1/>
   - fileKey：`lIjV2gObcion4O2nbOvEe1`，起始頁 node：`1:2`（URL 裡寫成 `1-2`）
   - 規模：45+ 個畫面、100+ 個元件，包含色彩、字級、元件
2. **實作依據 = repo 裡的 token**：Flutter 用 `TPColors`／`TPTextStyles`；網頁用 §4 的 CSS 變數（官方 Vue 範例放在 `tailwind.config.js`）。**禁止寫死色碼和字級。**
3. Figma 和程式碼不一致時，**不要自己挑一邊**。把差異記在 §7，然後問使用者。
4. 優先使用現成元件：Flutter 有 `lib/util/tp_*.dart`，網頁則照 UI Kit 的元件來刻，不要自創風格。
5. 設計系統相關的套件同樣受 `CLAUDE.md` §0 允許清單約束。例如網頁端要用 UI 元件庫，必須先問。

---

## 2. 讀取 Figma 的方法

### 2.1 額度限制（先看這裡）

官方 Figma MCP 的讀取工具有額度限制，**而且是看「檔案所在的 team 方案」**，不是只看你自己的 seat：

| 方案／seat | 額度 |
|---|---|
| Starter（免費）、View／Collab seat | **每月約 6 次 tool call** |
| Professional／Organization／Enterprise 的 Dev 或 Full seat | 每分鐘限制（和 REST API Tier 1 相同） |

（資料來源：[Figma MCP rate limits](https://developers.figma.com/docs/figma-mcp-server/rate-limits-access/)，2026/11 查詢；數字可能變動，以官方頁面為準。）

**所以策略是：每個節點只讀一次，讀到的結果全部存進 `docs/townpass/figma/`，之後一律讀快取，不要重複呼叫 MCP。**

### 2.2 方法 A：官方 Figma MCP（推薦，要有額度）

```bash
# 推薦做法：在 Claude Code 安裝 Figma 官方 plugin（內含 MCP 設定與 agent skills）
# 或者手動加入 remote MCP：
claude mcp add --transport http figma https://mcp.figma.com/mcp
# 接著在 Claude Code 裡執行 /mcp → figma → 完成 OAuth 登入（只需要做一次）
```

- 社群檔（Community file）要先 **Duplicate 到自己的 drafts 或 team**，才讀得到。上面的 URL 應該已經是複製後的版本，若讀取失敗先確認權限。
- 主要會用到的工具（實際名稱以 `/mcp` 列出的為準）：
  - `get_metadata`：列出頁面上的 frame、元件結構和 node id（最省額度，先用這個）
  - `get_variable_defs`：取得 token（顏色、字級、間距）
  - `get_screenshot`：取得畫面截圖
  - `get_design_context`：取得單一節點的設計細節／參考程式碼（最貴，只對真的要實作的元件呼叫）

### 2.3 方法 B：Figma REST API（Personal Access Token）

```bash
# Figma → Settings → Security → Personal access tokens（只勾 file_content:read）
export FIGMA_TOKEN=...   # 不要 commit
curl -s -H "X-Figma-Token: $FIGMA_TOKEN" \
  "https://api.figma.com/v1/files/lIjV2gObcion4O2nbOvEe1" > docs/townpass/figma/file.json
# 匯出指定節點的圖片
curl -s -H "X-Figma-Token: $FIGMA_TOKEN" \
  "https://api.figma.com/v1/images/lIjV2gObcion4O2nbOvEe1?ids=1:2&format=png&scale=2"
```

- 一次就能拿到整份檔案的 JSON（節點、樣式、元件），很適合用來建清單。
- `variables` endpoint 只有 Enterprise 能用，所以 token 要從 `styles` 和節點的 fill／text style 解析。
- REST API 一樣有依方案的額度限制，所以同樣「抓一次、存檔」。

### 2.4 方法 C：瀏覽器截圖（額度用完時的備案）

用 Claude in Chrome 開 Figma 檔，對 frame 截圖，再把截圖、色票、字級一起交給 AI 產生元件（指引 #47 建議的做法）。這個方法不消耗 API 額度，但拿不到精確數值，數值一律以 §4 的 token 為準。

---

## 3. 建立設計系統的步驟（第一次）

產出放在 `docs/townpass/figma/`：

1. **盤點**：`get_metadata(fileKey, nodeId='1:2')`，或用 REST API 抓 `file.json`
   → 產出 `inventory.md`：每個頁面／frame／元件的名稱、node id、用途。實作時要回頭查的 node id 都記在這裡
2. **Token**：`get_variable_defs`，或從 `file.json` 的 styles 解析
   → 產出 `tokens.json`，並和 §4 的程式碼 token 逐項比對；有差異就寫進 §7
3. **關鍵畫面截圖**：只截我們服務會用到的畫面（列表、表單、地圖、Dialog、空狀態…）→ 存成 `screens/*.png`
4. **元件規格**：只對要實作的元件呼叫 `get_design_context` → 產出 `components/<name>.md`，記下尺寸、間距、圓角、狀態（default／pressed／disabled）
5. **網頁端 token**：產生 `tokens.css`（§4.1）與 Tailwind 設定（§4.2），放進微服務專案
6. 視需要：把上面的結論濃縮回本文件，讓之後的工作不必再讀 Figma

---

## 4. Token（目前程式碼裡的值，已核對）

### 4.1 色彩（`TPColors`）

主色 Primary 500 `#5AB4C5`、輔色 Secondary 500 `#F5BA4B`、灰階 Grayscale 500 `#738995`。每個色系有 50～950 共 11 階，另有 red、orange 兩組狀態色。微服務網頁使用同一組色票：

```css
/* tokens.css —— 由 lib/util/tp_colors.dart 轉換 */
:root {
  --tp-primary-50: #EDF8FA;  --tp-primary-100: #DBF1F5; --tp-primary-200: #B4E2EA; --tp-primary-300: #93D4DF;
  --tp-primary-400: #71C5D5; --tp-primary-500: #5AB4C5; --tp-primary-600: #468D9B; --tp-primary-700: #356C77;
  --tp-primary-800: #22474E; --tp-primary-900: #112629; --tp-primary-950: #081315;

  --tp-secondary-50: #FDF8ED;  --tp-secondary-100: #FCF2DF; --tp-secondary-200: #F8E3BC; --tp-secondary-300: #F4D69E;
  --tp-secondary-400: #F0C87C; --tp-secondary-500: #F5BA4B; --tp-secondary-600: #E7A43C; --tp-secondary-700: #AD7B2B;
  --tp-secondary-800: #74521B; --tp-secondary-900: #3C2B0B; --tp-secondary-950: #1C1304;

  --tp-grayscale-50: #F1F3F4;  --tp-grayscale-100: #E3E7E9; --tp-grayscale-200: #CAD1D5; --tp-grayscale-300: #ADB8BE;
  --tp-grayscale-400: #91A0A8; --tp-grayscale-500: #738995; --tp-grayscale-600: #5E6D76; --tp-grayscale-700: #475259;
  --tp-grayscale-800: #30383D; --tp-grayscale-900: #171B1D; --tp-grayscale-950: #0B0D0E;

  --tp-red-50: #FAEEEE;  --tp-red-100: #F5DCDD; --tp-red-200: #EBB6B6; --tp-red-300: #E29494;
  --tp-red-400: #D45251; --tp-red-500: #D45251; --tp-red-600: #C2332F; --tp-red-700: #912522;
  --tp-red-800: #5F1715; --tp-red-900: #310B0B; --tp-red-950: #180505;

  --tp-orange-50: #FDF3EC;  --tp-orange-100: #FBE7D9; --tp-orange-200: #F7CFB2; --tp-orange-300: #F4B992;
  --tp-orange-400: #F1A26D; --tp-orange-500: #FD853A; --tp-orange-600: #E6692C; --tp-orange-700: #AE501F;
  --tp-orange-800: #713311; --tp-orange-900: #391A06; --tp-orange-950: #1C0C02;

  --tp-white: #FFFFFF; --tp-black: #000000;

  --tp-font-family: "PingFang TC", "Roboto", system-ui, -apple-system, sans-serif;
}
```

### 4.2 Tailwind（官方 Vue 範例的做法）

```js
// tailwind.config.js（節錄）——數值引用 tokens.css 的變數
const scale = (n) => Object.fromEntries([50,100,200,300,400,500,600,700,800,900,950].map(s => [s, `var(--tp-${n}-${s})`]));
export default {
  theme: {
    extend: {
      colors: { primary: scale('primary'), secondary: scale('secondary'), grayscale: scale('grayscale'), red: scale('red'), orange: scale('orange') },
      fontFamily: { sans: ['var(--tp-font-family)'] },
      fontSize: { h1: '36px', h2: '24px', title: '18px', h3: '16px', body: '14px', caption: '12px' },
    },
  },
};
```

### 4.3 字級（`TPTextStyles`，單位是 Flutter 邏輯像素，相當於 CSS px）

| Token | 大小 | 字重 | Flutter |
|---|---|---|---|
| h1 | 36 | 400／600 | `h1Regular`、`h1SemiBold` |
| h2 | 24 | 400／600 | `h2Regular`、`h2SemiBold` |
| title | 18 | 600 | `titleSemiBold` |
| h3 | 16 | 400／600 | `h3Regular`、`h3SemiBold` |
| body | 14 | 400／600 | `bodyRegular`、`bodySemiBold` |
| caption | 12 | 600（見 §7） | `caption` |

字體：中文 **PingFang TC**，英數 **Roboto**。

- Flutter 端：已內建在 `fonts/`，使用 `FontFamily.pingFangTC`。
- **網頁端：不要把 `fonts/` 裡的 PingFang 檔案拿去網頁用**（字型授權不明）。直接用上面的系統字型 stack 即可：iOS 有 PingFang，Android 會回退到系統的 Roboto／Noto CJK。

### 4.4 Flutter 現成元件（`lib/util/`）

`TPAppBar`、`TPButton`（`.primary` 等）、`TPCard`、`TPDialog`、`TPBottomSheet`、`TPCheckbox`、`TPCheckboxListTile`、`TPSwitch`、`TPTabView`、`TPText`、`TPTextSpan`、`TPSvgIcon`、`TPSettingList`、`TPShimmerLoading`、`TPLine`、`TPCachedNetworkImage`、`TPBottomNavigationBar`、`TPWebView`。

### 4.5 微服務網頁的版面約定

- 網頁跑在 `TPWebView` 裡，App 已經提供 **primary500 底、白字的 AppBar**（含返回和關閉按鈕），標題來自 `<title>` 或 `forceWebViewTitle`。
  → **網頁不要再做一條重複的標題列**（無障礙 ST：每頁只有一個 AppBar 標題）。頁內如果需要分頁，用 tab 或 section 標題。
- 以手機寬度 360～430px 為主要範圍，用 Chrome DevTools 的裝置模擬檢查。Figma frame 的基準寬度等盤點時（§3-1）再確認。
- 加上 `<meta name="viewport" content="width=device-width, initial-scale=1">`，並且**不要禁止縮放**（無障礙 DT）。

---

## 5. 無障礙設計：12 類規範（#30）

城市通依數位發展部的無障礙規範逐項檢視過 App，微服務也要做到：

| 代碼 | 類別 | 城市通做法 | 微服務網頁怎麼做 |
|---|---|---|---|
| AT | 替代文字 | 圖示可朗讀，裝飾圖已隱藏 | `<img alt>`；裝飾圖用 `alt=""` 或 `aria-hidden="true"`；只有圖示的按鈕要加 `aria-label` |
| AV | 時序媒體 | 沒有影音，也沒有自動播放 | 不自動播放；有影音的話提供字幕和暫停控制 |
| NT | 通知 | 系統通知和 Dialog 都能被朗讀 | Dialog 用 `role="dialog"` 並管理焦點；toast 用 `aria-live` |
| TS | 觸控 | 觸控目標至少 48dp × 48dp | 可點擊區域至少 `48px × 48px` |
| FC | 焦點 | 焦點順序由上到下、由左到右 | DOM 順序等於視覺順序；不用正數 `tabindex` |
| FM | 表單 | 欄位標籤清楚，鍵盤對應格式 | 每個欄位都有 `<label>`；用正確的 `type`／`inputmode`（tel、email、numeric） |
| LK | 連結 | 描述明確，重複連結合併 | 不用「點這裡」；同一目的地的連結只放一個 |
| DC | 動態內容 | 不使用閃爍內容 | 不閃爍；支援 `prefers-reduced-motion` |
| ST | 結構 | 每頁一個 AppBar 標題 | 見 §4.5；頁內使用語意化的 heading 層級 |
| AD | 可調適 | 內容順序合乎邏輯 | 不靠 CSS 重排來改變閱讀順序 |
| DT | 可辨識 | 文字放大到 200% 仍可閱讀 | 字級用 rem；版面不寫死高度；放大 200% 後不截字 |
| PD | 可預期 | 導覽順序和圖示保持一致 | 同一種操作用同一個圖示與位置 |

另外：文字和背景的對比要足夠。例如 primary500 `#5AB4C5` 底配白字的對比偏低，內文不要用這個組合，只用在大字或 AppBar 上（實際數值實作時再檢查）。

---

## 6. 實作一個畫面的流程

1. 在 `figma/inventory.md` 找到對應的 frame 和 node id（沒有的話，先用快取的截圖比對）
2. 列出需要的元件，確認哪些已有 `TP*` 元件或已經刻過的網頁元件
3. 只讀還沒快取過的元件規格（省額度）
4. 實作時只用 token（顏色、字級），間距和圓角照 Figma
5. 對照 §5 的 12 類規範自我檢查，並在實機上用 200% 字級測一次
6. 在 App 內實測（不要只在瀏覽器看）

---

## 7. 已知差異／待確認（Figma 盤點後更新）

| 項目 | 程式碼 | 待確認 |
|---|---|---|
| `red400` 與 `red500` | 兩個都是 `#D45251` | 疑似原始碼筆誤，以 Figma 為準 |
| `caption` 字重 | 註解寫 regular(w400)，實際是 `w600` | 以 Figma 為準 |
| Figma frame 基準寬度 | — | 盤點後填入 |
| 間距、圓角 scale | 程式碼沒有統一的 token（例如卡片圓角是 6.0） | 盤點後整理 |
