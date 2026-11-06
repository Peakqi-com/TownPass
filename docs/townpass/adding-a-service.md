# 把自己的微服務加進城市通

> 整理自《2026 城市通入門指引》投影片 #13、#15～#28（含講者備註），並逐項對照本 repo 的原始碼（taipei-doit/TownPass main，2026/10）。
> 標 **⚠️ 程式碼實測** 的項目是投影片沒提、但讀原始碼時發現的坑。

---

## 0. 整體架構（#9）

```
┌─────────────┐   postMessage / onmessage   ┌──────────────┐   API   ┌──────────┐   抓資料  ┌──────────┐
│ 城市通 App   │ ◄─────────────────────────► │ 你的微服務網頁 │ ──────► │ 後端(選配) │ ───────► │ 開放資料  │
│ Flutter      │       （WebView 內）         │ 語言框架不限   │         │ 語言不限   │          │          │
│ 帳號/定位/    │                             │              │         │           │          │          │
│ 通知/掃碼     │                             │              │         │           │          │          │
└─────────────┘                             └──────────────┘         └──────────┘          └──────────┘
```

- 參賽作品通常是**一個在 WebView 裡跑的網頁**，視需要搭配後端。
- App 本身**不一定要改**。只有在需要硬體能力（NFC、藍牙…）或裝置端 AI 時，才需要在 App 加 Handler。
- 把服務「掛」進 App 只要改一個檔案：`my_service_model.dart`。

---

## 1. 專案結構與常改位置（#13）

見根目錄 `CLAUDE.md` §2。比賽中最常改的有三處：

| 用途 | 檔案 |
|---|---|
| 新增服務 | `lib/page/city_service/model/my_service_model.dart` |
| 擴充 App 能力 | `lib/util/web_message_handler/` |
| 切換測試帳號 | `assets/mock_data/account.json` |

---

## 2. 用 Mock 資料測試（#15）

`assets/mock_data/` 裡有 5 個檔案：

| 檔案 | 用途 |
|---|---|
| `account.json` | 帳號資料。微服務呼叫 `userinfo` 時，回傳的就是這個檔案的 `data` |
| `activity.json` | 首頁活動 |
| `home_banner.json` | 首頁橫幅 |
| `message.json` | 訊息頁 |
| `subscription.json` | 訂閱範例 |

- 要展示「非市民」或「長者」情境：修改 `citizen`、`birthday`。
- `AccountService.init()` 在 App 啟動時用 `rootBundle` 讀取一次，所以**改完要完全重啟 App**，hot reload 不會生效。
- 裡面的個資都是測試用的假資料。

---

## 3. App ↔ 微服務雙向溝通（#17～#19）

### 3.1 運作流程（#18）

```
網頁                                              App（Flutter）
① window.flutterObject.postMessage(JSON字串) ──►  ② TPWebMessageListener：jsonDecode，依 name 找 Handler
                                                  ③ TPWebMessageHandler.handle(...)：執行定位、掃碼…
⑤ flutterObject 'message' 事件：JSON.parse      ◄── ④ replyWebMessage() → {"name","data"} JSON 字串
```

- JS 物件名稱：`flutterObject`（在 `tp_web_message_listener.dart` 的 `jsObjectName` 設定）
- 訊息格式：`{ name, data }`，**一定要先用 `JSON.stringify` 轉成字串**再傳
- 底層是 `flutter_inappwebview` 的 `WebMessageListener`，在 `TPInAppWebView.onWebViewCreated` 註冊

### 3.2 網頁端寫法（#19）

最精簡的寫法：

```js
// 送出：postMessage 只能傳字串
window.flutterObject.postMessage(JSON.stringify({ name: 'location', data: null }));

// 接收：App 回傳的也是 JSON 字串
const onReply = (event) => {
  const { name, data } = JSON.parse(event.data);
  if (name === 'location') console.log(data.latitude, data.longitude);
};
window.flutterObject.addEventListener('message', onReply);
// 用完要移除，避免重複觸發
window.flutterObject.removeEventListener('message', onReply);
```

建議包成一個 Promise 版的 helper，並在一般瀏覽器（沒有 `flutterObject`）裡改用 mock：

```ts
// src/lib/townpass.ts
type Reply<T> = { name: string; data: T };

export const inTownPass = () => typeof (window as any).flutterObject !== 'undefined';

export function callApp<T = unknown>(name: string, data: unknown = null, mock?: T, timeoutMs = 10000): Promise<T> {
  if (!inTownPass()) {
    return mock !== undefined ? Promise.resolve(mock) : Promise.reject(new Error(`not in TownPass: ${name}`));
  }
  const fo = (window as any).flutterObject;
  return new Promise<T>((resolve, reject) => {
    const timer = setTimeout(() => { fo.removeEventListener('message', onMsg); reject(new Error(`timeout: ${name}`)); }, timeoutMs);
    function onMsg(e: MessageEvent) {
      let msg: Reply<T>;
      try { msg = JSON.parse(e.data); } catch { return; }
      if (msg.name !== name) return;
      clearTimeout(timer);
      fo.removeEventListener('message', onMsg);
      resolve(msg.data);
    }
    fo.addEventListener('message', onMsg);
    fo.postMessage(JSON.stringify({ name, data }));
  });
}
```

> 官方 Vue 範例已封裝成 composables：`src/composables/useConnectionMessage.ts`、`useHandleConnectionData.ts`，可以參考。
> 注意：同一個 `name` 的請求如果同時發出多個，回覆無法分辨是哪一個請求的。要嘛避免並發，要嘛在自訂 Handler 的 data 裡帶 request id。

### 3.3 內建的 9 個 Handler（依 `tp_web_message_handler.dart` 實際程式碼）

| `name` | 送出的 `data` | App 回覆的 `data` | 備註 |
|---|---|---|---|
| `userinfo` | `null` | account 物件（`account.json` 的 `data`） | 沒有帳號時回 `[]` |
| `location` | `null` | geolocator `Position.toJson()`：`latitude`、`longitude`、`accuracy`、`timestamp`… | **失敗時回 `[]`，不是 null**；首次會跳權限詢問 |
| `deviceinfo` | `null` | device_info_plus 的 data map | 沒資料時回 `[]` |
| `qr_code_scan` | `null` | 掃描到的字串 | 會開啟 App 的掃碼頁；使用者直接返回時可能回 `null` |
| `notify` | `{ title, content }`（物件） | 成功時**不回覆**；格式錯誤回 `false` | ⚠️ `content` 符合「已訂閱X」或「已取消訂閱X」時，會改動 App 的訂閱清單 |
| `open_link` | URL 字串 | 成功時不回覆；`null` 時回 `false` | 用 `TPRoute.openUri` 在 App 內開**新的 WebView 頁**；`local://<route>` 會導到 App 內頁 |
| `launch_map` | URL 字串 | `bool`（能不能開啟） | 用外部 App 開啟（`url_launcher`） |
| `phone_call` | 電話號碼字串 | `bool` | 開啟 `tel://` |
| `1999agree` | 任意非 null 值 | 失敗時回 `false` | 先走使用者同意頁，再跳出 1999 撥號對話框 |

### 3.4 ⚠️ 程式碼實測：雙向溝通的坑

1. **非 JSON 字串會讓 Listener 出錯**：Listener 直接對 `webMessage.data` 做 `jsonDecode`，傳錯格式會丟例外，而且不會有任何回覆。
2. **Listener 會跑過所有 Handler**：`name` 相同的 Handler 會全部執行，所以自訂名稱絕對不能和上表重複。
3. **`launch_map`、`phone_call`、`1999agree` 收到 `null` 時**：回覆 `false` 之後沒有 `return`，接著會丟例外。網頁端一定要傳有效的 data。自己寫的 Handler **回覆錯誤後要記得 `return`**。
4. 回覆不保證一定會來（例如 `notify`、`open_link` 成功時不回覆）。網頁端要設 timeout，不能無限等待。

---

## 4. 自訂 Handler 擴充 App 能力（#20～#21）

### 4.1 四個步驟

```dart
// lib/util/web_message_handler/tp_web_message_handler.dart（或新增檔案）
class GreetingMessageHandler extends TPWebMessageHandler {
  @override
  String get name => 'greeting';            // ② 對應網頁送出的 name，不可和內建重複

  @override
  Future<void> handle({
    required Object? message,
    required WebUri? sourceOrigin,
    required bool isMainFrame,
    required Function(WebMessage reply)? onReply,
  }) async {
    if (message is! String) {
      onReply?.call(replyWebMessage(data: false));
      return;                                // 記得 return
    }
    onReply?.call(replyWebMessage(data: '哈囉，$message！'));
  }
}
```

1. 繼承 `TPWebMessageHandler`（去年叫 `CPWebMessageHandler`，網路上的舊範例要注意改名）
2. 用 `name` 對應網頁端送出的 `name`
3. **加進 `TPWebMessageListener._cachedMessageHandlers` 清單**（`tp_web_message_listener.dart`），沒加的話網頁送出的訊息不會被處理
4. 網頁端呼叫：`postMessage(JSON.stringify({ name: 'greeting', data: '市民' }))`

### 4.2 擴充硬體能力的流程（#21）

可擴充的項目：NFC、藍牙、陀螺儀、健康資料、音訊、IoT、Wi-Fi、AR/VR、**裝置端 AI**。

1. **選套件**：在 pub.dev 搜尋，授權必須是 MIT／BSD／Apache（見 `CLAUDE.md` §0），iOS 優先選支援 SPM 的
2. **包成 MessageHandler**：照上面的範例，取一個自訂 name 並加進清單
3. **設定雙平台權限**：
   - iOS `ios/Runner/Info.plist`：補上 `NS…UsageDescription` 的用途說明，**沒寫的話 App 會直接閃退，或拿不到權限**
   - Android `android/app/src/main/AndroidManifest.xml`：加入 `<uses-permission>`

> ⚠️ 程式碼實測：`INTERNET` 權限只寫在 `android/app/src/debug/AndroidManifest.xml`。如果要 build **release** APK，先確認合併後的 manifest 有 INTERNET 權限（可能由外掛帶入），否則 WebView 連不上網路。

---

## 5. WebView 開發注意事項（#16）

| 項目 | 說明 |
|---|---|
| 釋放記憶體 | 切換頁面或進入背景時要釋放 WebView 資源。內建的 `TPWebView` 是一個 route，關閉時就會 pop 掉；如果在自己的頁面裡嵌 `TPInAppWebView`，要自己處理 dispose |
| 雙平台測試 | 彈出視窗在 iOS 預設會被擋，Android 要自己處理 |
| 在 App 內實測 | 開發時可以用 Chrome DevTools 的裝置模擬看版面，但**雙向溝通只能在 App 內運作**，完成後一定要在 App 裡實測 |

⚠️ 程式碼實測補充：

- **不要用 `window.open()`／`target="_blank"`**：`TPWebView` 沒有實作 `onCreateWindow`，新視窗不會開。要開連結請改用 `open_link`（App 內）或 `launch_map`（外部）。
- **避免 `alert()`／`confirm()`**：在 App 內的行為不一致，請用網頁內自己做的 Dialog（照 UI Kit 樣式）。
- **WebView 標題**：沒設 `forceWebViewTitle` 時，AppBar 會顯示網頁的 `<title>`，所以 `<title>` 要寫成正式的服務名稱。
- **網址必須是 HTTPS**：Android 9+ 預設擋明文 HTTP，iOS 有 ATS，而本 repo 沒有放寬任何一邊。開發時要讓手機連到本機的 dev server，請用 **ngrok 之類的 HTTPS tunnel**，或部署到 Firebase Hosting 的 preview channel（`firebase hosting:channel:deploy dev`），不要用 `http://192.168.x.x`。
- **定位權限**：`onGeolocationPermissionsShowPrompt` 一律自動允許，網頁也可以直接用 `navigator.geolocation`。不過建議統一走 `location` Handler，雙平台的行為比較一致。
- 要用 chrome://inspect 或 Safari Web Inspector 除錯網頁時，可以在 `TPInAppWebView` 的 `initialSettings` 設 `InAppWebViewSettings(isInspectable: kDebugMode)`。

---

## 6. 新增一個服務（#22～#25）

### 6.1 「服務」頁的四個區塊（#23）

| # | 區塊 | 說明 | 原始碼 |
|---|---|---|---|
| 1 | 我的服務 | 使用者自己置頂的常用服務（最多 12 個） | `widget/pinned_service_*` |
| 2 | 更多／新增 | 進入服務列表選擇要置頂的服務。**服務要先加進列表** | `lib/page/city_service_edit/` |
| 3 | 服務拼貼 | 中央區塊，四張重要市政服務卡片 | `widget/official_service_card/` |
| 4 | 熱門 | 使用頻率較高的服務 | `model/trending_service_model.dart` |

微服務通常放在「服務列表」和「熱門」。

### 6.2 修改 `my_service_model.dart`（#24）

```dart
enum MyServiceItemId {
  // …現有的 21 個服務
  zoo,
  myService,   // ① 新增 id
  ;
}

// ② 在 MyServiceIdExt 的 switch 補一個 case（switch 必須窮舉，漏寫會編譯失敗）
MyServiceItemId.myService => MyServiceItem(
  title: '我的新服務',
  description: '一句話介紹這個服務',
  icon: Assets.svg.iconMyService.svg(),
  category: MyServiceCategory.cityLife,
  destinationUrl: 'https://my-service.web.app/',
  // forceWebViewTitle: '我的新服務',   // 選填
),
```

| 欄位 | 說明 |
|---|---|
| `title` | 服務名稱 |
| `description` | 一句話說明 |
| `icon` | SVG 圖示（`Assets.svg.xxx.svg()`） |
| `category` | 分類：`cityService` 市政服務、`healthCare` 防疫醫療、`cityLife` 城市生活、`explore` 探索臺北、`other` 其他服務 |
| `destinationUrl` | 點選後開啟的微服務網址（HTTPS）。**空字串的話點了沒有反應** |
| `forceWebViewTitle` | 選填，強制指定 WebView 標題 |

### 6.3 四個步驟（#25）

1. **新增圖示**：SVG 放進 `assets/svg/`，檔名用 snake_case，然後跑 `build_runner`
2. **新增 id**：在 `MyServiceItemId` enum 加一行
3. **填內容**：在 `MyServiceIdExt` 加 case，`destinationUrl` 先填測試網址（例如 `https://www.gov.taipei/`），部署後再換成正式網址
4. **執行並加入**：`fvm flutter run` → 服務 › 更多 → 加入我的服務

> ⚠️ 程式碼實測：**置頂清單只存在記憶體裡**（`PinnedServiceWidgetController` 的 `RxList`，沒有寫進 SharedPreferences），App 重啟後會回到預設的 3 個（找地點、申辦服務、市政資訊儀表板）。
> 想讓 Demo 時一打開就看到自己的服務，就把 `MyServiceItemId.myService` 加進 `pinned_service_widget_controller.dart` 的預設清單。

---

## 7. 「熱門」與「服務拼貼」（#26）

### 熱門：`model/trending_service_model.dart`

在清單尾端（註解 `// 在此列表後加入新熱門按鈕` 的位置）加一筆：

```dart
TrendingService(
  title: '我的新服務',
  icon: Assets.svg.iconMyService.svg(),
  url: 'https://my-service.web.app/',
  // forceWebViewTitle: '我的新服務',
),
```

每列 2 個按鈕。如果要改每列的數量，`trending_service_widget.dart` 的 `_tableRowList` 邏輯也要跟著改。

### 服務拼貼：`widget/official_service_card/`

| 檔案 | 卡片 |
|---|---|
| `official_service_card_top_left.dart` | 市政服務 |
| `official_service_card_top_right.dart` | 有話要說・警政報警 |
| `official_service_card_bottom_left.dart` | 防疫醫療・市政 APP |
| `official_service_card_bottom_right.dart` | 城市生活 |

四張卡片各是一個 Widget，`onTap` 目前還是 `// TODO: add url`。要導到自己的服務，就填入：

```dart
onTap: () async => await TPRoute.openUri(uri: 'https://my-service.web.app/'),
```

（去年用 JSON 設定，今年改成 Widget，網路上的舊教學已經不適用。）

---

## 8. 圖示的新增與使用（#27）

```
assets/svg/icon_my_service.svg  ──build_runner──►  lib/gen/assets.gen.dart  ──►  Assets.svg.iconMyService.svg()
```

- 只用 **SVG**，檔名 **snake_case**，放在 `assets/svg/`
- 新增之後一定要重跑：`fvm dart run build_runner build --delete-conflicting-outputs`
- 換算規則：`icon_dashboard_reports.svg` → `Assets.svg.iconDashboardReports.svg()`
- 專案裡已經有 108 個圖示，先找現成的用（`ls assets/svg`）；新圖示的風格要和 UI Kit 一致
- 圖示要加語意標籤，例如 `Semantics(label: '…', child: icon)`，或使用 `TPSvgIcon`（無障礙 AT 類）

---

## 9. 設計資源（#28）

UI 要照 Figma 上的 **Town Pass UI Kit**（45+ 個畫面、100+ 個元件，包含色彩、字級、元件）。做法、token 和 Figma MCP 讀取流程，見 [`design-system.md`](design-system.md)。

---

## 10. 賽前練習清單（#32）

- [ ] clone 專案、`fvm install`、完成建置
- [ ] 新增一張 SVG，重跑 build_runner
- [ ] 新增 `MyServiceItemId` 與 `MyServiceItem`
- [ ] `destinationUrl` 先填 `https://www.gov.taipei/`
- [ ] 在 App 裡加入「我的服務」
- [ ] 用自己的手機完成一次測試（iOS 要先處理好簽章）
- [ ] 部署一個 Hello World 到 Firebase Hosting，把網址填進 `destinationUrl`，在 App 內確認雙向溝通（例如呼叫 `userinfo`）正常
