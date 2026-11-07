# 用戶研究：聽障、視障、高齡者（子題「用不了 #身體限制」）

> 整理日期：2026-11-07（比賽當天）。範圍：本屆題目「數位平權 × 友善共融」的子題「用不了 #身體限制」，聚焦**聽障、視障、高齡者**三類客群，對照隊伍提案《台北通長輩模式》（repo 根目錄 `台北通長輩模式_提案簡報_AI城市起風_兩分鐘版_v2.pdf`）。
>
> 原則：只引用一手來源（政府統計原始頁面、論文本身、W3C／Apple／Google／MDN／Chromium／WebKit 官方文件、套件原始碼）。標記方式：**✅** 表示已親自打開原始頁面、PDF 或原始碼確認；**⚠️** 表示只看到搜尋摘要、頁面擋爬蟲，或尚未查證，引用前要再確認。
>
> 分工：本文只處理**用戶障礙與證據、規範、介面與互動層的建議、WebView 技術可行性、提案風險**。市府服務盤點與服務層的功能建議分成兩份：長者服務見 [`taipei-elderly-services.md`](taipei-elderly-services.md)；視障、聽障服務（1999 文字與手語管道、119 簡訊報案、手語翻譯、同步聽打、輔具、交通無障礙、相關資料集）見 [`taipei-disability-services.md`](taipei-disability-services.md)。

---

## 三句話結論

1. **語音功能不能放在網頁裡做。** Android WebView 不支援 `speechSynthesis`。Web Speech 的語音辨識預設會把音訊送到雲端，違反「執行時只能在裝置端推論」的規則。whisper.cpp 的多執行緒 WASM 在 Android WebView 也跑不動（沒有 `SharedArrayBuffer`）。所以唸出按鈕名稱和按住說話都要改走 **App 端自訂 Handler**。
2. **TownPass 現在的 WebView 設定對三類客群都不友善。** `flutter_inappwebview` 把 Android 的 `textZoom` 寫死成 100，所以**系統字體放大不會影響微服務網頁**；iOS WKWebView 也不跟隨 Dynamic Type。麥克風權限在兩個平台**預設都會被拒絕**，而 App 沒有宣告 `RECORD_AUDIO`，也沒有 `NSMicrophoneUsageDescription`。這幾點都要改 App 端，網頁端改不了。
3. **提案只為長輩設計，而且只有「說」一條路；但三類客群其實大幅重疊，同一個介面就能照顧到。** 全國聽障、視障者有超過五成年逾 60 歲，聽障者 90% 用口語溝通、只有 1.3% 主要用手語（衛福部 2021、數發部 2024）。所以「大按鈕＋語意化 HTML＋語音和打字兩種輸入＋每個聲音提示都配文字」就能同時服務三類人。要避免的是自製 TTS 跟 VoiceOver／TalkBack 搶著講話，以及只能「按住說話」。

## 建議優先做的 5 件事（今天做得完、Demo 有說服力）

| # | 做什麼 | 為什麼（證據） | 工作量 |
|---|---|---|---|
| 1 | **大按鈕首頁用語意化 HTML 重做**：`<button>` 配可見文字；圖示加 `aria-hidden`；觸控目標 ≥ 48px（建議 ≥ 72px，約 14mm 以上）；字級用 rem；對比 ≥ 4.5:1 | WCAG 1.4.3、2.5.8、4.1.2；高齡者按鍵小於 14mm 時正確率顯著下降（Leitão & Silva 2012）；45.9% 的 Android App 圖片按鈕幾乎都沒標籤（Ross 2018） | 網頁端，半天 |
| 2 | **App 端修 WebView 兩個設定**：Android `textZoom` 改成跟系統字級；`onPermissionRequest` 只對自己的網域授權麥克風（若要錄音） | §5.2、§5.4（原始碼確認） | App 端，1 小時 |
| 3 | **自訂 Handler `tts_speak`**：網頁送文字，App 用裝置端 TTS 唸出。**偵測到螢幕閱讀器開啟時不要自己唸**，交給 VoiceOver／TalkBack | Android WebView 不支援 `speechSynthesis`（MDN BCD、blink-dev）；Flutter 的 `MediaQuery.accessibleNavigation` 可以判斷螢幕閱讀器是否開啟 | App＋網頁，2～3 小時；**要裝 flutter_tts（MIT），需隊伍確認** |
| 4 | **「找服務」同時提供三種輸入**：按住說話、點一下開始／再點一下結束、打字，結果都只回 3 個大按鈕（圖示＋短文字），全部用關鍵字比對，離線可用 | 以手語為母語的聾人不使用語音（邱曉萍 2009）；VoiceOver 使用者難以「按住不放」；高齡語音的辨識錯誤率明顯較高（Vipperla 2008） | 網頁端，2 小時（先做關鍵字比對與打字，語音辨識最後接） |
| 5 | **每個回饋都至少有兩種感官**：語音提示同時有大字文字（放在 `role="status"`）；點按有觸覺回饋（Android `navigator.vibrate`，iOS 走 `haptic` Handler）；「撥電話」這類只有聲音的動作，旁邊要有文字替代入口（入口清單見 `taipei-disability-services.md`） | 聽障者「主要困境為無法接聽電話、無法語音溝通」（邱曉萍 2009）；WCAG 4.1.3；iOS 不支援 vibrate（MDN BCD） | 網頁端 1 小時；`haptic` Handler 用 Flutter 內建 API，不需要新套件 |

---

## 1. 用戶分析

### 1.0 三類共通：同一套設計可以同時照顧

- W3C WAI 指出，老化會讓精細動作控制變差，因此「難以點擊小目標」，而且這些問題「和身心障礙者的無障礙需求重疊」（✅ [W3C WAI, Older Users and Web Accessibility, 2025-11 更新](https://www.w3.org/WAI/older-users/)）。
- W3C 的〈Developing Websites for Older People〉把高齡需求逐條對應到 WCAG：1.4.4 文字放大 200%、2.2.1 時間限制可調整，以及 3.2.3／3.2.4 一致的導覽，並說後者「對部分有認知衰退的高齡者特別重要」（✅ [W3C WAI](https://www.w3.org/WAI/older-users/developing/)）。
- **對設計的意義**：提案的「大按鈕、少選項、固定位置」本身就是共通設計。缺的是三種感官通道的備援：視覺上的文字和圖示、聽覺上的語音、觸覺上的震動，三者要能互相替代。

### 1.0b 人數總表（官方統計，全部打開原始頁面或原檔確認 ✅）

| 指標 | 全國 | 臺北市 | 時點 | 來源 |
|---|---|---|---|---|
| 65 歲以上人口占比 | **20.70%**（4,806,053 人） | **24.86%**（全國最高） | 2026-09 底 | [內政部戶口統計分析](https://www.moi.gov.tw/News_Content.aspx?n=9&s=342353) |
| 同上（前一期） | 20.06% | 24.18% | 2025-12 底 | [內政部](https://www.moi.gov.tw/News_Content.aspx?n=9&s=335870) |
| 身心障礙者總數 | 1,258,972 人（5.42%） | 122,346 人（5.04%） | 2026-06 底 | [衛福部統計處 表 1.1.1](https://dep.mohw.gov.tw/dos/cp-5224-62359-113.html)（[xlsx](https://www.mohw.gov.tw/dl-69410-3372b4eb-e96d-4b84-ad30-b9f88d657042.html)） |
| 聽覺機能障礙（舊制類別） | 144,701 人 | **14,702 人** | 2026-06 底 | 同上 |
| 視覺障礙（舊制類別） | 54,374 人 | **5,769 人** | 2026-06 底 | 同上 |
| 個人上網率：全國／65 歲以上 | 90.3%／**63.3%**（2024 年為 51.5%） | 臺北市整體 93.0% | 2025-05～07 調查 | [數發部 114 年數位近用調查](https://moda.gov.tw/digital-affairs/digital-service/dv-survey/18672) |
| 上網率依年齡 | 60–64 歲 89.4%、65–69 歲 83.1%、70–74 歲 67.2%、**75 歲以上 41.4%** | — | 同上 | 同上，附錄表 B-1 |
| 身障者個人上網率 | **54.1%**（全國 87.6%，差 33.5 個百分點；2021 年 54.9%，三年沒有改善） | — | 2024-11 調查 | [數發部 113 年身障者數位近用調查](https://moda.gov.tw/digital-affairs/digital-service/dv-survey/15548) |
| 聽障／視障者上網率 | 聽障 **40.3%**、視障 **50.9%**；60 歲以上分別只有 30.8%、35.0%；40 歲以下都在九成以上 | — | 同上 | 同上，附表 A3、表 4-1 |

注意：
- 臺北市 65 歲以上的**人數**沒有核對到。提案寫的「23.9%、約 58.4 萬人（民政局 2025-09）」沒有打開原文（⚠️），建議改用內政部 2026-09 的 **24.86%**。
- 新制第 2 類「眼、耳及相關構造與感官功能及疼痛」（全國 202,577 人）也包含平衡障礙與疼痛，**不能當作視障加聽障的人數**，要用上表的舊制類別。
- 兩份數發部調查的身障者上網率差很多（78.1% 對 54.1%）。114 年調查是一般民眾電訪、受訪者自述是否有障礙；113 年是依障別配額抽樣。**描述身障者時以 113 年專案調查為準。**
- 數發部 113 年調查指出，聽障、視障者有**超過五成年逾 60 歲**，上網率低主要和年齡有關。所以「高齡」和「聽障／視障」在臺北其實是同一群人的不同面向。

### 1.1 高齡者

**人數與趨勢**：臺北市 65 歲以上占 24.86%，是全國最高（2026-09）。75 歲以上上網率只有 41.4%。但已經上網的 65 歲以上長者，有 96.5% 用過政府線上公共服務（分母是「網路族」，不是全體長者；數發部 114 年調查）。**這代表「會上網的長輩願意用政府服務」，卡關的是介面。**

**使用手機的具體障礙（研究證據）**

| 障礙 | 證據 |
|---|---|
| 按鍵太小就點錯 | 40 位高齡者的實驗中，按鍵小於 **14 mm** 時正確率顯著下降，**14–17.5 mm 見方**表現最好；當時官方指引建議的 7–9 mm 明顯偏小。目標間距則似乎不影響表現（✅ [Leitão & Silva, PLoP 2012](https://mural.maynoothuniversity.ie/6045/1/PS-Target-Spacing.pdf)）。換算：14 mm ≈ 79 CSS px（以 1 CSS px ≈ 0.177 mm 估算，各機型不同，屬推估） |
| 虛擬按鍵太靈敏、誤觸；看不懂圖示 | 「虛擬按鍵的操作具有很高的靈敏度，對於中高齡使用者而言容易產生誤觸」，「觸控螢幕上所顯現的資訊必須讓中高齡的使用者能充分瞭解文字或符號的意義」（✅ 摘要，[胡齊元、陳立杰 2013](https://www.airitilibrary.com/Article/Detail/20713630-201303-201306210023-201306210023-112-124)）。這兩句支持**圖示一定要配文字** |
| 多指手勢困難 | 雙指手勢對高齡者不易使用，建議改用單指操作（✅ 摘要，[劉說芳、王明宏 2018](https://doi.org/10.6283/JOCSG.201812_6(4).353)） |
| 資訊層級太深 | 文獻回顧轉述「淺層的資訊階層對高齡使用者效果較好」，並指出高齡者普遍偏好較大字級（✅ [Arch, W3C WAI-AGE Literature Review, 2008](https://www.w3.org/TR/wai-age-literature/)；這是 2008 年的桌面網頁研究） |
| 語音助理的實際使用 | 7 位低科技使用度高齡者在家使用 Echo Dot 三週，查詢健康等線上資訊的用量一直穩定；提醒、計時等功能起初被認為有用，但因為擔心可靠性，實際用得很少（✅ [Pradhan, Lazar, Findlater, ACM TOCHI 2020](https://doi.org/10.1145/3373759)）。這支持「語音找服務」的方向，但**結果必須可靠**，答錯一次就會失去信任 |
| 長輩聲音較難辨識 | 高齡語音的 WER 顯著高於一般成人，而且隨年齡上升：成人 36.4%、高齡 47.8%（女性 46.8% 對 61.2%）；做說話者調適後差距縮小但仍存在（✅ [Vipperla et al., Interspeech 2008](https://www.cstr.inf.ed.ac.uk/downloads/publications/2008/vipperla_is08.pdf)；語料是美國最高法院錄音，系統是 2008 年的 HMM）。近年有中文高齡語音資料集指出同樣的困難（✅ 摘要，[WildElder 2025](https://arxiv.org/abs/2510.09344)、[SeniorTalk 2025](https://arxiv.org/abs/2503.16578)） |

**實際使用的輔助方式**：放大字體與顯示大小、語音輸入、家人代操作。**數位使用習慣詳見 `taipei-elderly-services.md`**。

### 1.2 視障者

**人數**：臺北市視覺障礙 5,769 人（2026-06）。上網率 50.9%，60 歲以上只有 35.0%。視障者擁有輔助軟體的比率是每百人 20 人，硬體輔具每百人 8 人（數發部 113 年調查）。最主要的溝通方式仍是口語（98.36%），使用語音報讀的有 0.62%、點字 0.18%（[衛福部 110 年身障者生活狀況調查](https://dep.mohw.gov.tw/DOS/lp-5096-113-xCat-y110.html)，表 1-1-10）。**含意：多數視障者是低視力或後天視力退化的長者，大字、高對比、語音念出的重要性不輸給螢幕閱讀器相容。**

**使用手機的具體障礙**

| 障礙 | 證據 |
|---|---|
| 按鈕沒有標籤，螢幕閱讀器只會念「按鈕」 | 5,753 個 Android App 中，**45.9%** 的 App 只有不到 1 成的圖片按鈕有標籤。依元件類型，缺標籤的比例是 Floating Action Button 92.0%、Image Button 54.7%、Clickable Image 86.3%（✅ [Ross et al., ASSETS 2018](https://doi.org/10.1145/3234695.3236364)）。另一項研究分析 10,408 個 App，「超過 77% 有缺少標籤的問題」（✅ [Chen et al., ICSE 2020](https://arxiv.org/abs/2003.00380)） |
| 無障礙錯誤普遍存在 | 100 個熱門 Android App **全部**至少有一類無障礙錯誤，72% 有五或六類（✅ [Ross et al., ASSETS 2017](https://doi.org/10.1145/3132525.3132547)） |
| 手勢學習成本高 | 5 位新手盲人追蹤八週，「學會這些裝置是艱難而漫長的過程」；TalkBack 內建教學只有 1 人完成（✅ [Rodrigues et al., ASSETS 2015](https://doi.org/10.1145/2700648.2809842)）。**含意：不要發明新手勢，按住說話要有「點一下」的替代方式** |
| 動態內容沒有被念出 | 沒有找到一手論文（⚠️ 未查證），但技術面的做法見 §5.5 |

**實際使用的輔助方式**：iOS VoiceOver、Android TalkBack（單指點選後念出、雙擊啟動、左右滑動切換焦點）、放大鏡、高對比與粗體字。

### 1.3 聽障者

**人數**：臺北市聽覺機能障礙 14,702 人（2026-06），是視障者的 2.5 倍。上網率 40.3%，60 歲以上只有 30.8%（數發部 113 年調查）。
- 最主要的溝通方式（衛福部 110 年調查，表 1-1-10）：口語 **90.35%**、手勢 2.98%、筆寫或打字 2.79%、讀唇 1.32%、**手語 1.28%**（推估 4,169 人）。
- 聽障者「需要輔具」的比率是 70.01%（同上）。
- **含意**：大多數聽障者是會說話、後天聽損的長者，所以「按住說話」對他們其實可用，但**回饋不能只有聲音**，一定要有大字文字。少數以台灣手語為母語的聾人，則需要打字輸入和簡單的文字。

**使用手機的具體障礙**

| 障礙 | 證據 |
|---|---|
| 不能打電話是最大困境 | 22 位聽障手機使用者的訪談與觀察：「主要困境為無法接聽電話、無法語音溝通」，次要困擾包括「仰賴簡訊為非即時通訊」（✅ 摘要，[邱曉萍，交大博士論文 2009](https://www.airitilibrary.com/Publication/Index/U0030-0309201012100799)）。**含意：任何「撥打 1999／1966」按鈕，對聽障者都要有文字或視訊的替代入口** |
| 書面中文不是母語 | 啟聰學校學生的故事理解表現是「自然手語（台灣手語）優於書面語，書面語優於文法手語」（✅ 摘要，[劉秀丹等，特殊教育研究學刊 2006](https://doi.org/10.6172/BSE200603.3001006)）。**含意：文字要短、用常用字，搭配圖示；長段說明對部分聾人不友善** |
| 手機與簡訊高度普及 | 有學位論文寫「聽障者行動電話持有率 90%」「96% 使用簡訊進行文字溝通」（⚠️ 只見於搜尋摘要，[劉倩秀，交大博士論文 2009](https://ir.lib.nycu.edu.tw/handle/11536/81672)，引用前要開原文核對） |

**實際使用的輔助方式**：助聽器或人工電子耳（⚠️ 衛福部報告本文沒有按輔具品項分的使用率）、LINE 等文字訊息、簡訊、視訊手語、同步聽打。臺北市社會局 2026Q2 的手語翻譯服務 1,536 人次、同步聽打 781 人次（✅ 已下載 data.taipei [`45b47513…`](https://data.taipei/dataset/detail?id=45b47513-6004-4285-8cd8-7e528bb68c73)、[`1296e695…`](https://data.taipei/dataset/detail?id=1296e695-36a2-47ff-a52c-6bc08042e7aa)）。

---

## 2. 規範依據

### 2.1 WCAG 2.2 中與三類客群最相關的成功準則

標題已和 [W3C WCAG 2.2](https://www.w3.org/TR/WCAG22/) 原文核對（✅）。等級：A／AA 是一般要求，AAA 是加強。

| 編號 | 名稱（等級） | 高齡 | 視障 | 聽障 | 本專案怎麼做 |
|---|---|:-:|:-:|:-:|---|
| 1.1.1 | Non-text Content（A） | ○ | ● | ○ | 圖示按鈕要有可讀名稱；裝飾圖 `aria-hidden` |
| 1.2.2／1.2.4 | Captions（A／AA） | | | ● | 有影音（例如教學影片）就要附字幕 |
| 1.2.6 | Sign Language（AAA） | | | ● | 有餘力時，重要說明附手語影片 |
| 1.3.1 | Info and Relationships（A） | | ● | | 用 `<h1>`、`<ul>`、`<button>`，不要用 `<div onclick>` |
| 1.3.3 | Sensory Characteristics（A） | ○ | ● | ○ | 不要寫「按右下角綠色按鈕」 |
| 1.4.1 | Use of Color（A） | ● | ● | | 狀態不能只靠顏色表示 |
| 1.4.3／1.4.6 | Contrast（AA 4.5:1／AAA 7:1） | ● | ● | | 長輩模式建議以 7:1 為目標 |
| 1.4.4 | Resize Text（AA，200%） | ● | ● | | 見 §5.2，要 App 端配合 |
| 1.4.10 | Reflow（AA） | ● | ● | | 放大後不出現水平捲動 |
| 1.4.11 | Non-text Contrast（AA，3:1） | ● | ● | | 按鈕邊框與圖示 |
| 2.2.1 | Timing Adjustable（A） | ● | ● | ○ | 語音錄音、結果頁不要自動逾時跳走 |
| 2.4.6 | Headings and Labels（AA） | ● | ● | ● | 標題與按鈕文字要能直接看懂 |
| 2.5.1 | Pointer Gestures（A） | ● | ● | | 不要求多指或軌跡手勢 |
| 2.5.2 | Pointer Cancellation（A） | ● | ● | | 「按住說話」要能取消（例如滑出按鈕就取消） |
| 2.5.3 | Label in Name（A） | ○ | ● | | 可見文字要和無障礙名稱一致 |
| 2.5.5／2.5.8 | Target Size（AAA 44px／AA 24px） | ● | ● | | 長輩模式應遠高於 44px（見 §1.1） |
| 3.1.5 | Reading Level（AAA） | ● | | ● | 用簡單字詞（對聾人尤其重要，見 §1.3） |
| 3.2.6 | Consistent Help（A，2.2 新增） | ● | ● | ● | 「打給家人／求助」固定在同一位置 |
| 3.3.7 | Redundant Entry（A，2.2 新增） | ● | ● | | 不要讓使用者重複輸入 |
| 3.3.8 | Accessible Authentication（AA，2.2 新增） | ● | ● | | 不要求記憶或辨認圖形驗證碼 |
| 4.1.2 | Name, Role, Value（A） | | ● | | 自製元件要有 role 和狀態 |
| 4.1.3 | Status Messages（AA） | ○ | ● | | 「辨識中…」「找到 3 個服務」用 `role="status"` |

●＝關鍵，○＝相關。

### 2.2 數位發展部（國內規範）

- 現行的「**網站無障礙規範（110.07）**」自 110 年 7 月 1 日起實施認證標章檢測，參考 WCAG 2.1。另有「**行動化應用軟體無障礙檢測指引**」（110-03-24 公發布，112-07-14 修正），共 13 張檢測清單，對應網站規範的 13 條指引。114 年的推廣說明會已安排「WCAG 2.2 版新增重點暨後續因應說明」（⚠️ 以上都來自搜尋結果摘要。[accessibility.moda.gov.tw](https://accessibility.moda.gov.tw/News/Detail/4441?Category=43) 與 [law.moda.gov.tw](https://law.moda.gov.tw/LawContent.aspx?media=print&id=FL096186) 對自動抓取回 403 或 Cloudflare 驗證，**沒有親自打開**，請用瀏覽器確認）。
- 城市通 App 依數位發展部規範檢視過的 12 類項目（AT、TS、DT…）已整理在 [`design-system.md` §5](design-system.md)，微服務照那張表做即可。

### 2.3 平台指南的關鍵數字

| 項目 | Apple HIG | Android | WCAG 2.2 |
|---|---|---|---|
| 觸控目標 | iOS 預設 **44×44 pt**，最小 28×28 pt（✅ [HIG Accessibility](https://developer.apple.com/design/human-interface-guidelines/accessibility)） | 至少 **48×48 dp**，「越大越好」（✅ [Android Developers](https://developer.android.com/guide/topics/ui/accessibility/apps)） | 2.5.8 AA 24×24 CSS px；2.5.5 AAA 44×44 |
| 文字對比 | 17 pt 以下 **4.5:1**；18 pt 以上或粗體 **3:1**（✅ HIG） | 小於 18sp（粗體小於 14sp）**4.5:1**，其他 3:1（✅ Android） | 1.4.3 AA 4.5:1；1.4.6 AAA 7:1 |
| 字級 | iOS 內文預設 **17 pt**，最小 11 pt（✅ [HIG Typography](https://developer.apple.com/design/human-interface-guidelines/typography)）；HIG 建議讓使用者能把文字放大到**至少 200%** | 用 sp 單位跟隨系統字型（⚠️ 未逐字核對） | 1.4.4 放大到 200% |

---

## 3. 可串接的服務與資源

服務盤點見 [`taipei-elderly-services.md`](taipei-elderly-services.md) 與 [`taipei-disability-services.md`](taipei-disability-services.md)。

---

## 4. 介面與互動層建議

只談介面與互動：字級、對比、觸控、語音回饋、震動、字幕、螢幕報讀相容性。要串哪些服務、做哪些服務層功能，請看上面兩份文件。

優先順序：**P0**＝今天一定要做，是 Demo 主線；**P1**＝今天做得完，加分；**P2**＝決選問答時當作「下一步」說明。

### 4.1 三類共通

| 優先 | 建議 | 對應證據 |
|---|---|---|
| P0 | 首頁大按鈕：每個都是 `<button>`，配**可見文字**加圖示（圖示 `aria-hidden="true"`）。目標高度 ≥ 72px（≈ 14 mm 以上）、寬度占滿半個螢幕，按鈕間距 ≥ 8px | Leitão & Silva 2012（≥ 14 mm）；胡齊元 2013（圖示要配文字）；WCAG 2.5.8、1.1.1 |
| P0 | 字級用 `rem`，根字級跟隨系統（§5.2）。放大到 200% 時改成單欄、不截字、不出現水平捲動 | WCAG 1.4.4、1.4.10；HIG 建議至少能放大到 200% |
| P0 | 對比 ≥ 7:1（長輩模式的目標）；狀態不能只靠顏色表示。注意 `primary500 #5AB4C5` 配白字的對比偏低（見 design-system.md §5） | WCAG 1.4.3／1.4.6、1.4.1；視障者多為低視力長者（§1.2） |
| P0 | **輸入至少兩種**：語音加打字（系統鍵盤本身支援注音和手寫）。結果只回 3 個大按鈕，順序固定 | 聽障者無法語音溝通（邱曉萍 2009）；淺層資訊階層（WAI-AGE）；語音助理要可靠才會被持續使用（Pradhan 2020） |
| P0 | **回饋至少兩種感官**：每個語音提示都同步顯示大字；狀態訊息（「正在聽…」「找到 3 個服務」）放在初始 HTML 就存在的 `role="status"` 區域 | WCAG 4.1.3；聽障者 90% 用口語但聽不到提示音（§1.3）；MDN Live regions |
| P1 | 觸覺回饋：Android 用 `navigator.vibrate`（必須由使用者手勢觸發）；iOS 不支援，改走 `haptic` Handler 呼叫 `HapticFeedback` | MDN BCD（§5.3） |
| P1 | 「求助／打給家人」這類固定功能，每頁放在同一個位置、用同一個圖示 | WCAG 3.2.6；W3C 指出一致的導覽對高齡者特別重要 |
| P1 | 不自動逾時、不自動跳頁；錄音沒有時間限制，或可以延長 | WCAG 2.2.1 |
| P1 | 不閃爍；支援 `prefers-reduced-motion`；錄音中的動畫要能被文字取代 | WCAG 2.3.x；design-system.md §5 DC |

### 4.2 高齡者

| 優先 | 建議 | 對應證據 |
|---|---|---|
| P0 | 點按後唸出按鈕名稱（提案原有）：走 App 端 TTS Handler，**螢幕閱讀器開啟時不要唸** | §5.1；避免和 VoiceOver 重複播報 |
| P1 | 按住說話：放開才送出，**滑出按鈕就取消**；錄音中顯示大字「正在聽，放開就送出」 | WCAG 2.5.2；Vipperla 2008（辨識會錯，要能重來） |
| P1 | 先用大字顯示「你是說：叫復康巴士？」，再列出按鈕讓長輩確認；提供「重說一次」 | 高齡語音錯誤率高（Vipperla 2008、WildElder 2025） |
| P1 | 只用單指點一下，不用長按以外的手勢，也不用雙指或滑動 | 劉說芳 2018；WCAG 2.5.1 |
| P2 | 頁內提供「字大一點」按鈕，作為系統設定以外的第二條路 | Apple HIG（可用自訂 UI 支援放大） |

### 4.3 視障者（螢幕閱讀器相容）

| 優先 | 建議 | 對應證據 |
|---|---|---|
| P0 | 不用 `<div onclick>`；每頁一個 `<h1>`；DOM 順序等於視覺順序；按鈕的可見文字等於無障礙名稱 | Ross 2017／2018；WCAG 1.3.1、2.5.3、4.1.2 |
| P0 | 按住說話對 VoiceOver 使用者很難（要「雙擊並按住」），所以提供**「點一下開始、再點一下結束」**的切換模式；螢幕閱讀器開啟時預設用這個模式 | Rodrigues 2015（手勢學習成本高） |
| P1 | 自製 TTS 和螢幕閱讀器擇一：App 用 Flutter 的 `MediaQuery.accessibleNavigation` 判斷螢幕閱讀器是否開啟，透過 `a11y_state` Handler 告訴網頁 | ⚠️ 這個 Flutter API 的雙平台行為要實機確認 |
| P1 | 結果出現時，用 `role="status"` 念出「找到 3 個服務：…」，或把焦點移到第一個結果 | WCAG 4.1.3 |
| P1 | 低視力：粗體、大字、高對比優先於細線條圖示；圖示線寬與邊框對比 ≥ 3:1 | WCAG 1.4.11；§1.2 |

### 4.4 聽障者

| 優先 | 建議 | 對應證據 |
|---|---|---|
| P0 | 打字輸入一定要有（§4.1），而且放在和語音按鈕同樣顯眼的位置，不要藏在選單裡 | 邱曉萍 2009 |
| P0 | 所有語音提示和唸出的內容都要有同步字幕或大字顯示 | WCAG 1.2.x 的精神；§1.3 |
| P1 | 只有聲音的動作（撥電話）旁邊要有文字替代入口（替代管道見 `taipei-disability-services.md`） | 邱曉萍 2009 |
| P1 | 文字要短、用常用字，搭配圖示 | 劉秀丹 2006（以台灣手語為母語者讀書面語較吃力）；WCAG 3.1.5 |
| P1 | 若放教學影片，一定要附字幕 | WCAG 1.2.2 |
| P2 | 重要說明附台灣手語影片 | WCAG 1.2.6（AAA） |

---

## 5. WebView 技術可行性

TownPass 用 `flutter_inappwebview` **6.1.5**（`pubspec.lock`），`TPWebView` **沒有傳 `initialSettings`**（全部用預設值），也**沒有實作 `onPermissionRequest`**（✅ `lib/util/tp_web_view.dart`）。下面的「原始碼」指本機 `~/.pub-cache` 裡 flutter_inappwebview_android 1.1.3、flutter_inappwebview_ios 1.1.2 的原始碼（✅ 已親自核對 textZoom 與權限預設值）。

### 5.0 總表

| 能力 | Android WebView | iOS WKWebView | 結論 |
|---|---|---|---|
| `speechSynthesis`（TTS） | ❌ 不支援 | ✅ 支援 | **走 App Handler** |
| `SpeechRecognition` | ❌ 視為不可用；而且預設上雲 | ⚠️ 需要 `NSSpeechRecognitionUsageDescription`；預設上雲 | **不要用**（違反裝置端規則） |
| 系統字體放大 | ❌ 被 `textZoom=100` 擋住 | ❌ 不跟隨 Dynamic Type | **App 端設定加網頁 rem** |
| `navigator.vibrate` | ✅ 要使用者手勢與 VIBRATE 權限 | ❌ 不支援 | iOS 走 Handler（`HapticFeedback`） |
| `getUserMedia`（麥克風） | ⚠️ 預設拒絕；缺 `RECORD_AUDIO` | ⚠️ 預設拒絕；缺 `NSMicrophoneUsageDescription` | 若網頁錄音，要改 App 三處 |
| 螢幕閱讀器讀 DOM | ✅ | ✅（未找到 Apple 官方文件明寫） | 網頁端寫對 ARIA 即可 |
| 多執行緒 WASM（SharedArrayBuffer） | ❌ 不支援 | ⚠️ 要 COOP/COEP 標頭 | whisper.cpp WASM **不建議** |

### 5.1 Web Speech API

- **`speechSynthesis`**
  - Android WebView：MDN browser-compat-data 的 `SpeechSynthesis`、`speak`、`getVoices` 在 `webview_android` 都是 `version_added: false`（✅ [BCD SpeechSynthesis.json](https://raw.githubusercontent.com/mdn/browser-compat-data/main/api/SpeechSynthesis.json)）。Chromium blink-dev 的信也寫明 "Android WebView, which does not support Web Speech API"（✅ [blink-dev 2018](https://groups.google.com/a/chromium.org/g/blink-dev/c/XpkevOngqUs)）。
  - iOS WKWebView：BCD 沿用 Safari 7+，可用。`getVoices()` 初次回傳空陣列、靜音鍵的影響 ⚠️ 未查證，要實機測。
  - **結論**：雙平台不一致，TTS 一律走 Handler。
- **`SpeechRecognition`**
  - MDN 原文："By default, using speech recognition on a web page involves a server-based recognition engine. Your audio is sent to a web service for recognition processing, so it won't work offline."（✅ [MDN Using the Web Speech API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API/Using_the_Web_Speech_API)）。
  - 強制在裝置端處理的 `processLocally` 只有桌面 Chrome 139+ 支援，Chrome Android 和 Safari 都不支援（✅ BCD）。
  - iOS WKWebView 會暴露 `webkitSpeechRecognition`，但需要 `NSSpeechRecognitionUsageDescription`，否則出現 `service-not-allowed` 錯誤（✅ [WebKit Bug 239816](https://bugs.webkit.org/show_bug.cgi?id=239816)）。
  - **結論：不要用**，會違反 CLAUDE.md §0.2 的「執行時推論必須在裝置端」，斷網測試也會失敗。

### 5.2 系統字體放大

- **Android**：Chromium `AwSettings` 預設會「依系統字型縮放比例調整文字大小」，但 embedder 一旦呼叫 `setTextZoom()` 就不再跟隨（✅ [AwSettings.java](https://chromium.googlesource.com/chromium/src/+/main/android_webview/java/src/org/chromium/android_webview/AwSettings.java)）。flutter_inappwebview_android 1.1.3 的預設值是 `textZoom = 100`（`InAppWebViewSettings.java:63`），而且在 `InAppWebView.java:318` **無條件**呼叫 `settings.setTextZoom(...)`（✅ 原始碼）。
  - **結果**：在 TownPass 裡，使用者把系統字型調大，微服務網頁**不會**變大。
  - **改法**：`TPInAppWebView` 傳 `initialSettings: InAppWebViewSettings(textZoom: (MediaQuery.textScalerOf(context).scale(100)).round())`。這個設定只在 Android 生效。
- **iOS**：WebKit Bug 187013「WKWebView should support increasing text size for accessibility」是 **RESOLVED WONTFIX**，留言建議改用 `-apple-system-body` 之類的 CSS 關鍵字（✅ [WebKit Bug 187013](https://bugs.webkit.org/show_bug.cgi?id=187013)）。
  - **改法**：網頁 `html { font: 100% sans-serif; font: -apple-system-body; }`，其他字級一律用 `rem`。
- **最一致的做法**：新增 Handler `text_scale`，App 回傳 `textScaler` 的倍率，網頁設定 `document.documentElement.style.fontSize`。這樣雙平台行為相同，網頁內也可以自己提供「字大一點」按鈕。

### 5.3 `navigator.vibrate`

- Android WebView 4.4.3+ 支援，但 v60 起**必須由使用者手勢觸發**（✅ [BCD Navigator.json](https://raw.githubusercontent.com/mdn/browser-compat-data/main/api/Navigator.json)）。App 必須有 `VIBRATE` 權限，否則 Chromium 只會記錄錯誤、不會震動（✅ [VibrationManagerAndroid.java](https://chromium.googlesource.com/chromium/src/+/main/services/device/vibration/android/java/src/org/chromium/device/vibration/VibrationManagerAndroid.java)）。TownPass 自己沒有宣告這個權限，`flutter_local_notifications` 的 manifest 有宣告，合併後應該會帶進來（⚠️ 未實測）。
- iOS Safari／WKWebView 不支援（✅ BCD），要走 Handler 用 Flutter 內建的 `HapticFeedback`，不需要新增套件。

### 5.4 麥克風 `getUserMedia`

- **兩個平台預設都拒絕**：flutter_inappwebview 在 Dart 端沒有設定 `onPermissionRequest` 時會走 `defaultBehaviour`：Android 是 `request.deny()`（`InAppWebViewChromeClient.java`），iOS 是 `decisionHandler(.deny)`（`InAppWebView.swift`）（✅ 原始碼）。
- 如果一定要在網頁端錄音（例如 whisper WASM），要同時改三處：
  1. `TPWebView` 實作 `onPermissionRequest`，只對自己的網域回傳 `PermissionResponseAction.GRANT`
  2. Android 宣告 `RECORD_AUDIO`，並在執行期取得授權（⚠️ 執行期授權流程未實測）
  3. iOS `Info.plist` 加 `NSMicrophoneUsageDescription`
- 頁面要是 HTTPS（✅ [WebKit Bug 208667](https://bugs.webkit.org/show_bug.cgi?id=208667)）。iOS 的 `requestMediaCapturePermissionFor` 委派方法是 iOS 15+（✅ Apple 文件），TownPass 的最低版本剛好是 15。
- 注意：`mediaCapturePermissionGrantType` **不是** flutter_inappwebview 的設定（6.1.5 原始碼裡搜不到），不要照網路文章用。

### 5.5 TalkBack／VoiceOver 讀 WebView

- Android WebView 會透過 `AccessibilityNodeProvider` 把 DOM 轉成虛擬 view 樹交給 TalkBack（✅ [Chromium accessibility/android.md](https://chromium.googlesource.com/chromium/src/+/main/docs/accessibility/browser/android.md)）。iOS 沒有找到 Apple 官方文件明寫，但實務上 VoiceOver 可以讀 WKWebView（⚠️ 未查證官方出處）。
- 網頁端 ARIA 重點（✅ [MDN Live regions](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Guides/Live_regions)）：
  - live region 要**寫在初始 HTML**；用 JS 動態建立時，第一次更新要延到下一個 task
  - 一般訊息用 `role="status"`（建議同時加 `aria-live="polite"`）；`assertive` 只用在緊急訊息
  - `role="alert"` **不要**再加 `aria-live`，否則 iOS VoiceOver 會念兩次
  - live region 只會念出純文字
- 作品 repo 的 `src/components/BridgeDemo.tsx` 已經有 `aria-live="polite"`，可以沿用這個寫法。

### 5.6 建議：哪些能力改走 App 端自訂 Handler

依 [`adding-a-service.md` §4](adding-a-service.md) 的四個步驟新增。名稱不可和內建 9 個重複。

| Handler `name`（建議） | data | App 端做法 | 新套件 |
|---|---|---|---|
| `tts_speak` | `{ text, rate? }` | 用 flutter_tts 呼叫系統 TTS。要挑 `network_required=false` 的聲音，並在飛航模式下測試 | **flutter_tts 4.2.5（MIT），需隊伍確認**。Android 11+ 要在 `<queries>` 宣告 `TTS_SERVICE` |
| `a11y_state` | `null` | 回傳 `{ screenReader: MediaQuery.accessibleNavigation, textScale }` | 不需要 |
| `haptic` | `'light' \| 'medium'` | `HapticFeedback.lightImpact()` 等 | 不需要 |
| `stt_listen`（P1） | `{ locale: 'zh-TW' }` | 見下 | 需隊伍確認 |

**語音辨識要走哪條路，需隊伍決定**：

- 選項 A：**speech_to_text 7.5.0（BSD-3-Clause）** 搭配 `SpeechListenOptions(onDevice: true)`。先呼叫 `hasOnDeviceSupport('zh-TW')`，結果是 false 就停用功能、改成打字。原始碼註解提到，Android 在無法裝置端處理時可能「靜默退回網路辨識」，所以一定要先檢查（⚠️ 這是 GitHub main 分支的程式碼，和 7.5.0 是否一致未比對）。另外，系統的 Google／Apple 辨識引擎算不算規則裡的「模型推論」，**建議問主辦單位**。
- 選項 B：App 端原生跑 whisper.cpp（不經過 WebView）。**不在允許清單，需隊伍確認**；要整合原生程式，今天的時間風險高。
- 選項 C（今天最穩）：**先只做打字加關鍵字比對**，語音辨識當作加分項目，最後才接。

---

## 6. 對照提案

### 6.1 有研究支持的設計

| 提案設計 | 支持證據 |
|---|---|
| 首頁只留 4～6 個大按鈕 | Leitão & Silva 2012（≥ 14 mm）；WAI-AGE（淺層階層）；W3C（小目標難點） |
| 字大、對比強 | WCAG 1.4.3／1.4.6；HIG 建議能放大到 200% |
| 點按時唸出按鈕名稱 | 對低視力長輩有幫助，但**要避開螢幕閱讀器使用者**（見 6.2） |
| 只回三個大按鈕 | 淺層階層；Pradhan 2020（結果要可靠，選項越少越好確認） |
| 依需求找、不必依機關找 | 和 W3C 對 3.2.3／3.2.4 一致導覽的說明相符；但「跨局處清單」本身沒有找到使用者研究 |

### 6.2 風險與缺口

| 風險 | 說明 | 建議 |
|---|---|---|
| **R1：whisper.cpp WASM 在 WebView 裡跑不起來或太慢** | Android WebView 沒有 `SharedArrayBuffer`，也不支援 COOP，只能跑單執行緒。`ggml-base-q5_1.bin` 約 **57 MiB**（HuggingFace 官方 repo），base 模型執行時記憶體約 388 MB（whisper.cpp README），首次載入要下載 57 MiB。麥克風權限兩個平台預設也都拒絕（§5.4）。另外 **whisper.cpp 不在 CLAUDE.md 允許清單，需隊伍確認** | 改走 App 端（§5.6），或今天先做打字和關鍵字比對 |
| **R2：Whisper base 的中文、長輩口音與台語辨識率** | Whisper 原始論文的中文 CER：tiny 52.4／small 29.4／medium 23.2（Common Voice 9）、tiny 40.5／small 20.8／medium 12.1（FLEURS）（✅ [Radford et al. 2022](https://arxiv.org/abs/2212.04356) 附錄表）。**論文沒有列 base 的中文數字**，但 base 介於 tiny 和 small 之間，可以推估錯誤率很高（推論，未實測）。高齡語音會更差（Vipperla 2008）。台語：針對台語微調後 CER 仍約 30%，華語模型直接辨識台語約 50%（✅ [Breeze Taigi 2026](https://arxiv.org/abs/2603.19259)） | 顯示「你是說：…？」讓長輩確認；關鍵字同義詞表要容錯；不要宣稱支援台語 |
| **R3：提案只寫長輩，沒有處理聽障者** | 唸出按鈕、撥打 1999／1966 都只有聲音輸出，聽障者用不了（邱曉萍 2009）。按住說話對多數會說話的聽障長者仍然可用（口語溝通占 90.35%，§1.3），但對以手語為母語的聾人不可用 | 加打字輸入、每個聲音提示都配大字（§4.1、§4.4）；文字與手語替代管道見 `taipei-disability-services.md` |
| **R4：視障者的自製 TTS 和 VoiceOver 衝突** | 螢幕閱讀器開啟時，點一下是「聚焦並念出」，雙擊才是啟動；自製 TTS 在啟動時又念一次，就會重複播報。按住說話需要「雙擊並按住」，很難發現 | `a11y_state` Handler 加切換模式（§4.3） |
| **R5：系統字體放大不會傳到網頁** | §5.2，Android 被 `textZoom=100` 擋住 | App 端設定 `textZoom`，或用 `text_scale` Handler |
| **R6：地圖技術不在清單** | 提案寫 **flutter_map＋OpenStreetMap**，CLAUDE.md 允許的是 **Leaflet 或 MapLibre**。flutter_map 是 Flutter 套件，不是 Leaflet 本身，**需隊伍確認** | 微服務本來就是網頁，直接在網頁用 Leaflet＋OSM，就不用改 App |
| R7：「依實機效能挑選適合的裝置端模型」沒有寫明 | README 必須揭露模型名稱、版本、量化格式、框架、來源（CLAUDE.md §0.2） | 今天若沒有用 LLM，就如實寫「服務對應使用關鍵字比對」 |
| R8：簡報裡的「248 萬市民只下載 10 萬多次」 | 本次沒有查證出處 | ⚠️ 決選前補上議會原始紀錄 |

### 6.3 需隊伍確認的技術（不在 CLAUDE.md 允許清單）

| 技術 | 用途 | 授權 | 狀態 |
|---|---|---|---|
| whisper.cpp（WASM 或原生）＋ Whisper base q5_1 | 語音轉文字 | MIT | **需隊伍確認**；WebView 內不建議 |
| flutter_tts | App 端 TTS | MIT（pub.dev ✅） | **需隊伍確認**（屬於「pub.dev 上 MIT 的套件」類別，但 CLAUDE.md 要求新增依賴前先問） |
| speech_to_text | App 端語音辨識 | BSD-3-Clause（pub.dev ✅） | **需隊伍確認**，而且要確認裝置端辨識是否符合規則 |
| flutter_map | 地圖 | BSD-3 | **需隊伍確認**；建議改用網頁端 Leaflet |

---

## 7. 查不到或不確定的地方

1. **數位發展部規範頁面**：對自動抓取回 403 或 Cloudflare 驗證，版本資訊來自搜尋摘要，要用瀏覽器確認。
2. **VoiceOver 讀 WKWebView** 的 Apple 官方文件沒找到；Flutter `MediaQuery.accessibleNavigation` 的雙平台行為要實機確認。
3. **Android WebView 的 `webkitSpeechRecognition`**：BCD 標 37+ 可用，但 blink-dev 說 WebView 不支援 Web Speech。反正預設會上雲，本專案不用，所以沒有實測。
4. **Whisper base 的中文 CER**：論文沒有列。長輩對按住說話的接受度、長按手勢的困難，都沒有找到專門的一手研究。Whisper 在臺灣長輩華語或台語上的直接評估也沒有找到。
5. **聽障者手機持有率 90%、簡訊使用率 96%**（劉倩秀 2009）只見於搜尋摘要；助聽器、人工電子耳的使用率在衛福部報告本文找不到。
6. **臺北市 65 歲以上的人數**沒有核對到，只有比率 24.86%。提案的「58.4 萬人、23.9%」沒有打開原文。
7. **要實機測的項目**：`flutter_local_notifications` 的 VIBRATE 權限合併結果；`textZoom` 改法的實際效果；iOS `speechSynthesis` 的 `getVoices()` 與靜音鍵行為；flutter_tts 與 speech_to_text 在飛航模式下是否可用。
8. **speech_to_text 的 `onDevice` 行為**是讀 GitHub main 分支的程式碼，沒有和 7.5.0 比對。
9. 提案中「北市警政 App 248 萬市民只下載 10 萬多次」沒有查證出處。

---

## 來源清單

**政府統計**
- 內政部 戶口統計資料分析（2026-09）：https://www.moi.gov.tw/News_Content.aspx?n=9&s=342353
- 內政部 戶口統計資料分析（2025-12）：https://www.moi.gov.tw/News_Content.aspx?n=9&s=335870
- 衛福部統計處 身心障礙者人數按類別及縣市別分：https://dep.mohw.gov.tw/dos/cp-5224-62359-113.html （xlsx：https://www.mohw.gov.tw/dl-69410-3372b4eb-e96d-4b84-ad30-b9f88d657042.html）
- 衛福部 110 年身心障礙者生活狀況及需求調查：https://dep.mohw.gov.tw/DOS/lp-5096-113-xCat-y110.html （PDF：https://www.mohw.gov.tw/dl-83264-b27950da-58e4-44c8-94e8-04a515bec2b0.html）
- 數位發展部 114 年數位近用調查：https://moda.gov.tw/digital-affairs/digital-service/dv-survey/18672 （PDF：https://www-api.moda.gov.tw/File/Get/moda/zh-tw/UtFPqDu90WXGz2h）
- 數位發展部 113 年身心障礙者數位近用現況與需求調查：https://moda.gov.tw/digital-affairs/digital-service/dv-survey/15548 （PDF：https://www-api.moda.gov.tw/File/Get/moda/zh-tw/dZ4Jsu46Js6VBgN）
- data.taipei 臺北市身心障礙者手語翻譯服務成果：https://data.taipei/dataset/detail?id=45b47513-6004-4285-8cd8-7e528bb68c73
- data.taipei 臺北市身心障礙者同步聽打服務成果：https://data.taipei/dataset/detail?id=1296e695-36a2-47ff-a52c-6bc08042e7aa

**國內規範**
- 數位發展部 網站無障礙規範公告（⚠️ 未能直接打開）：https://accessibility.moda.gov.tw/News/Detail/4441?Category=43
- 行動化應用軟體無障礙檢測指引（⚠️ 未能直接打開）：https://law.moda.gov.tw/LawContent.aspx?media=print&id=FL096186

**規範與平台指南**
- W3C WCAG 2.2：https://www.w3.org/TR/WCAG22/
- W3C Understanding 2.5.2 Pointer Cancellation：https://www.w3.org/WAI/WCAG22/Understanding/pointer-cancellation.html
- W3C WAI Older Users：https://www.w3.org/WAI/older-users/
- W3C WAI Developing Websites for Older People：https://www.w3.org/WAI/older-users/developing/
- W3C WAI-AGE Literature Review（2008）：https://www.w3.org/TR/wai-age-literature/
- Apple HIG Accessibility：https://developer.apple.com/design/human-interface-guidelines/accessibility
- Apple HIG Typography：https://developer.apple.com/design/human-interface-guidelines/typography
- Android Developers, Make apps more accessible：https://developer.android.com/guide/topics/ui/accessibility/apps

**WebView 技術**
- MDN BCD SpeechSynthesis：https://raw.githubusercontent.com/mdn/browser-compat-data/main/api/SpeechSynthesis.json
- MDN BCD Navigator（vibrate、getUserMedia）：https://raw.githubusercontent.com/mdn/browser-compat-data/main/api/Navigator.json
- MDN Using the Web Speech API：https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API/Using_the_Web_Speech_API
- MDN ARIA Live regions：https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Guides/Live_regions
- Chromium blink-dev（WebView 不支援 Web Speech）：https://groups.google.com/a/chromium.org/g/blink-dev/c/XpkevOngqUs
- Chromium AwSettings.java：https://chromium.googlesource.com/chromium/src/+/main/android_webview/java/src/org/chromium/android_webview/AwSettings.java
- Chromium VibrationManagerAndroid.java：https://chromium.googlesource.com/chromium/src/+/main/services/device/vibration/android/java/src/org/chromium/device/vibration/VibrationManagerAndroid.java
- Chromium Android accessibility：https://chromium.googlesource.com/chromium/src/+/main/docs/accessibility/browser/android.md
- Android WebSettings.setTextZoom：https://developer.android.com/reference/android/webkit/WebSettings#setTextZoom(int)
- Android PermissionRequest：https://developer.android.com/reference/android/webkit/PermissionRequest
- WebKit Bug 187013（WKWebView 文字放大，WONTFIX）：https://bugs.webkit.org/show_bug.cgi?id=187013
- WebKit Bug 208667（WKWebView getUserMedia）：https://bugs.webkit.org/show_bug.cgi?id=208667
- WebKit Bug 239816（WKWebView Web Speech）：https://bugs.webkit.org/show_bug.cgi?id=239816
- WebKit Blog, Using the System Font in Web Content：https://webkit.org/blog/3709/using-the-system-font-in-web-content/
- whisper.cpp：https://github.com/ggml-org/whisper.cpp 、https://github.com/ggml-org/whisper.cpp/tree/master/examples/whisper.wasm
- flutter_inappwebview 6.1.5 原始碼：本機 `~/.pub-cache/hosted/pub.dev/flutter_inappwebview_android-1.1.3`、`flutter_inappwebview_ios-1.1.2`
- flutter_tts：https://pub.dev/packages/flutter_tts ；speech_to_text：https://pub.dev/packages/speech_to_text

**論文**
- Leitão & Silva (2012), Target and Spacing Sizes for Smartphone UIs for Older Adults, PLoP：https://mural.maynoothuniversity.ie/6045/1/PS-Target-Spacing.pdf
- 胡齊元、陳立杰（2013），〈中高齡操作觸控式行動電話手勢挫折與心智模式之研究〉：https://www.airitilibrary.com/Article/Detail/20713630-201303-201306210023-201306210023-112-124
- 劉說芳、王明宏（2018），〈高齡者使用界面手勢研究與創新〉：https://doi.org/10.6283/JOCSG.201812_6(4).353
- Pradhan, Lazar, Findlater (2020), Use of Intelligent Voice Assistants by Older Adults with Low Technology Use, ACM TOCHI：https://doi.org/10.1145/3373759
- Ross et al. (2017), Epidemiology as a Framework for Large-Scale Mobile Application Accessibility Assessment, ASSETS：https://doi.org/10.1145/3132525.3132547
- Ross et al. (2018), Examining Image-Based Button Labeling for Accessibility in Android Apps, ASSETS：https://doi.org/10.1145/3234695.3236364
- Chen et al. (2020), Unblind Your Apps, ICSE：https://arxiv.org/abs/2003.00380
- Rodrigues et al. (2015), Getting Smartphones to Talkback, ASSETS：https://doi.org/10.1145/2700648.2809842
- 邱曉萍（2009），《從聽障者日常生活探討行動電話使用需求與要求》，交大博士論文：https://www.airitilibrary.com/Publication/Index/U0030-0309201012100799
- 劉秀丹、曾進興、張勝成（2006），〈啟聰學校學生文法手語、自然手語及書面語故事理解能力之研究〉：https://doi.org/10.6172/BSE200603.3001006
- 劉倩秀（2009），《聽障者多功能行動電話之通用設計》（⚠️ 未打開）：https://ir.lib.nycu.edu.tw/handle/11536/81672
- Vipperla, Renals, Frankel (2008), Longitudinal study of ASR performance on ageing voices, Interspeech：https://www.cstr.inf.ed.ac.uk/downloads/publications/2008/vipperla_is08.pdf
- Radford et al. (2022), Robust Speech Recognition via Large-Scale Weak Supervision：https://arxiv.org/abs/2212.04356
- Lan et al. (2026), Breeze Taigi：https://arxiv.org/abs/2603.19259
- Wang et al. (2025), WildElder：https://arxiv.org/abs/2510.09344
- Chen et al. (2025), SeniorTalk：https://arxiv.org/abs/2503.16578
