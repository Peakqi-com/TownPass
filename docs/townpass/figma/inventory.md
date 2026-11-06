# Town Pass UI Kit 元件清單

> 來源：Figma MCP `get_metadata`（fileKey `lIjV2gObcion4O2nbOvEe1`，page `1:2`），2026-11-06。
> 原始 XML：[`metadata-1-2.xml`](metadata-1-2.xml)（所有節點的 id、名稱、尺寸）。**要查 node id 時先讀這兩份，不要再呼叫 MCP。**
> 需要元件的精確樣式時，才對下表的 node id 呼叫 `get_design_context`，讀到的結果存成 `components/<name>.md`。

## 檔案結構

| page id | 名稱 | 內容 |
|---|---|---|
| `1:3` | Cover | 封面（略過） |
| `0:1` | 🫶About Us | 介紹（略過） |
| `1:2` | 📱Foundation & UI kit | **Foundation（色彩、字級、圖示）＋ 元件庫**（共 261 個 component） |

這份檔案裡沒有完整的 App 畫面，指引 #28 說的「45+ 畫面」不在這裡。設計基準寬度是 **375px**（iPhone）。

---

## Foundation

| 區塊 | node id | 內容 | 狀態 |
|---|---|---|---|
| Typography | `3:15` | 中文 PingFang（蘋方）、英文 Roboto、數字 Roboto；字級樣式表 | 部分 token 已讀（見 `tokens.json`） |
| Main colors | `3:141` | Primary、Secondary、Grey、Red、Orange，**另有 Green 色系**（`3:313` 標題） | 程式碼已有前五組；**Green 色值未讀** |
| Semantic colors | `3:390` | 文字、背景、停用、Alarm、Reminder 語意色 | ✅ 已讀（`tokens.json`） |

## 元件

| 區塊 | node id | 元件（node id：variant） | 對應 Flutter | 網頁實作 |
|---|---|---|---|---|
| button | `3:4828` | **M 175×48**：`3:4834` Primary、`3:4840` Second、`3:4846` Alarm、`3:4852` Reminder、`3:4858` Disable（各有 Hover）<br>**L 366×56**：`3:4862` Primary、`3:4867` Second、`3:4873` Alarm、`3:4879` Reminder、`3:4885` Disable<br>底部按鈕區：`3:4892`／`3:4901`／`3:4912`／`3:4920` | `TPButton` | 待做 |
| pop up | `3:4927` | `3:4934` type1（327×310）、`3:4949` type2（327×434）、`3:4964` type3（327×374） | `TPDialog` | 待做 |
| list item | `3:4717` | 單行 `3:4729`～`3:4757`（H2、H3、H3+item、H3+icon）；雙行 `3:4765`、`3:4774`；已讀/未讀 `3:4784`、`3:4794`；活動 `3:4804`；標題列 `3:4812`～`3:4823` | `TPSettingList` 等 | 待做 |
| menu | `3:4979` | `3:4983` grey、`3:4989` primary、`3:4995` white（395×48） | — | 待做 |
| search bar | `3:5002` | `3:5005`（343×80） | — | 待做 |
| tag | `3:5016` | `3:5019`（136×40） | — | 待做 |
| card | `3:5024` | `3:5027`（328×400） | `TPCard` | 待做 |
| text field | `3:5149` | `3:5150` default、`3:5159` focus、`3:5168` error、`3:5177` disable（366×110） | — | 待做 |
| tab | `3:5036` | single `3:5044`～`3:5051`（primary/secondary × default/select）；double `3:5054`、`3:5057`；triple `3:5061`、`3:5065` | `TPTabView` | 待做 |
| top navigation | `3:5071` | `3:5075` with logo、`3:5085` two iconbtn+logo、`3:5098` two iconbtn、`3:5110` text button、`3:5117` without iconbtn | `TPAppBar` | **網頁不做**（App 已有 AppBar） |
| foot tab bar | `3:5124` | `3:5129`（375×94） | `TPBottomNavigationBar` | 網頁不做 |
| device system | `3:4518` | 狀態列、home indicator、鍵盤（設計稿用） | — | 不做 |

## 圖示

| 區塊 | node id | 內容 |
|---|---|---|
| Logo | `3:1652`、`3:1654` | `logo_townpass_horizontal`、`logo_townpass` |
| 一般圖示（24×24） | `3:1591` | check／cancel（有無外圈、顏色、填色）、add／remove、方向（left/right/up/down）、back／forward、sound／view on-off、trash、notification toggle（40×26）、scan、like／bookmark、phone、question、person、check-square，以及 others：file_add、camera、file_search、map、dashboard、print、calendar、filter、edit、info、money、alert、share_ios、settings、case done／accept、sort、ticket、store、file、pin、mic、mail、paper_clip、time、clock、compass、temperature、mobile、id card、signout、hide、visibility、search、location、coupon_ticket |
| Tab bar 圖示 | `3:2126`～`3:2178` | card、service、home、coupon、account（default／select） |
| Pop up 圖示（100×100） | `3:2198`、`3:2205` | alert、check |
| **地圖圖示** | `3:2227` | 小圖示（16×16）：mappin（藍／紅／綠／黃）、vaccine、ubike、wifi、AED、parking、refuge（避難所）、search<br>**地圖大頭針（40×60，pressed）**：refuge、parking、taipeifree（Taipei Free Wi-Fi）、ubike、vaccine，各有多種顏色<br>其他：`3:2799` 定位我的位置（54×54）、`3:2801`／`3:2815` mark-pointer（72×72）、`3:2830`～`3:2840` 圓形等級（level 1～3）、`3:2846`／`3:2854` route（close／show）、垃圾車 |
| 插圖 | `3:5683` | `illustration_icon_*`：booking（L/M/S）、location_lost、mailbox、gov、sales、ticket sales、phone_upload、wallet、info、box、satisfy、mobile pay（多為 160×160） |

> 地圖大頭針和小圖示可以直接拿來當 Leaflet／MapLibre 的 marker，風格就會和城市通一致。
> repo 的 `assets/svg/` 已經有其中一部分（例如 `icon_location_search`、`illustrations_gov`）。要匯出新圖示時，先比對 `ls assets/svg`。

## MCP 呼叫紀錄（Starter 方案，每月約 6 次）

| 日期 | 工具 | 目標 | 結果 |
|---|---|---|---|
| 2026-11-06 | `get_metadata` | 檔案（無 nodeId） | 列出 3 個頁面 |
| 2026-11-06 | `get_metadata` | `1:2` | ✅ 已存成 `metadata-1-2.xml` |
| 2026-11-06 | `get_variable_defs` | `1:2` | ❌ canvas 不能當目標，要指定圖層 |
| 2026-11-06 | `get_variable_defs` | `3:390` | ✅ 已存成 `tokens.json` |

建議接下來的呼叫（等題目確定後再用）：
1. `get_variable_defs` `3:141`：補上 Green 色系，以及完整的字級行高
2. `get_design_context`：只讀我們服務真正用到的元件（例如 button L `3:4862`、text field `3:5150`、pop up）
