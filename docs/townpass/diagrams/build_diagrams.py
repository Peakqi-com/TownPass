"""產生 elder-mode-spec.md 的架構圖與流程圖（SVG）。

只用 Python 標準函式庫。色彩、字型取自城市通 UI Kit（lib/util/tp_colors.dart、PingFang TC）。
圖的內容要改時，改這支程式再重跑：

    python3 docs/townpass/diagrams/build_diagrams.py

每張圖畫在白色圓角卡片上，GitHub 深色模式也看得清楚。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from html import escape

OUT = os.path.dirname(os.path.abspath(__file__))

# ---- 城市通 UI Kit 色票（tp_colors.dart） ----
C = {
    "primary50": "#EDF8FA", "primary100": "#DBF1F5", "primary200": "#B4E2EA", "primary300": "#93D4DF",
    "primary500": "#5AB4C5", "primary600": "#468D9B", "primary700": "#356C77", "primary800": "#22474E",
    "secondary50": "#FDF8ED", "secondary100": "#FCF2DF", "secondary500": "#F5BA4B", "secondary700": "#AD7B2B",
    "secondary900": "#3C2B0B",
    "gray50": "#F1F3F4", "gray100": "#E3E7E9", "gray200": "#CAD1D5", "gray300": "#ADB8BE", "gray400": "#91A0A8",
    "gray500": "#738995", "gray600": "#5E6D76", "gray700": "#475259", "gray800": "#30383D",
    "orange50": "#FDF3EC", "orange500": "#FD853A", "orange700": "#AE501F",
    "red500": "#D45251", "white": "#FFFFFF",
}
FONT = "'PingFang TC','Noto Sans TC','Microsoft JhengHei',system-ui,sans-serif"

# 節點樣式：底色、框線、主文字色、副文字色
KINDS = {
    "ours": (C["primary50"], C["primary500"], C["gray800"], C["primary700"]),
    "official": (C["gray50"], C["gray200"], C["gray800"], C["gray600"]),
    "decision": (C["secondary50"], C["secondary500"], C["secondary900"], C["secondary700"]),
    "result": (C["primary500"], C["primary500"], C["white"], C["primary50"]),
    "warn": (C["orange50"], C["orange500"], C["gray800"], C["orange700"]),
    "data": (C["secondary100"], C["secondary700"], C["secondary900"], C["secondary700"]),
    "user": (C["primary800"], C["primary800"], C["white"], C["primary100"]),
    "plain": (C["white"], C["gray200"], C["gray800"], C["gray600"]),
}


def text_width(s: str, size: float) -> float:
    w = 0.0
    for ch in s:
        if ord(ch) > 0x2E80:  # 中日韓與全形符號
            w += size
        elif ch == " ":
            w += size * 0.3
        elif ch in "il.,:;|'!()[]{}/":
            w += size * 0.34
        elif ch.isupper() or ch in "mwMW@_":
            w += size * 0.68
        else:
            w += size * 0.56
    return w


@dataclass
class Box:
    cx: float
    cy: float
    w: float
    h: float

    @property
    def left(self): return self.cx - self.w / 2

    @property
    def right(self): return self.cx + self.w / 2

    @property
    def top(self): return self.cy - self.h / 2

    @property
    def bottom(self): return self.cy + self.h / 2

    def side(self, s: str, offset: float = 0):
        return {
            "t": (self.cx + offset, self.top), "b": (self.cx + offset, self.bottom),
            "l": (self.left, self.cy + offset), "r": (self.right, self.cy + offset),
        }[s]


class Diagram:
    TITLE = 20
    MAIN = 15
    SUB = 12.5

    def __init__(self, width: int, height: int, title: str, subtitle: str = ""):
        self.w, self.h = width, height
        self.title, self.subtitle = title, subtitle
        self.back: list[str] = []   # 群組底色
        self.edges: list[str] = []
        self.nodes: list[str] = []
        self.front: list[str] = []  # 線上的標籤

    # ---- 文字 ----
    def _text(self, x, y, s, size, color, weight=400, anchor="middle"):
        return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" fill="{color}" '
                f'text-anchor="{anchor}" dominant-baseline="central">{escape(s)}</text>')

    # ---- 群組 ----
    def group(self, x, y, w, h, title, tone="primary"):
        fill, stroke, color = (C["primary50"], C["primary200"], C["primary700"]) if tone == "primary" else (
            C["gray50"], C["gray200"], C["gray600"])
        self.back.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="{fill}" fill-opacity="0.55" '
                         f'stroke="{stroke}" stroke-width="1.5" stroke-dasharray="6 5"/>')
        self.back.append(self._text(x + 20, y + 22, title, 14, color, 700, "start"))

    # ---- 節點 ----
    def box(self, cx, cy, lines, kind="ours", w=None, pill=False, min_w=0, step=None):
        """lines[0] 是主文字（粗體），其餘是副文字。step 會在左上角畫編號圓點。"""
        fill, stroke, main, sub = KINDS[kind]
        widths = [text_width(lines[0], self.MAIN)] + [text_width(s, self.SUB) for s in lines[1:]]
        bw = w or max(min_w, max(widths) + 36)
        lh_main, lh_sub = 21, 18
        bh = 22 + lh_main + lh_sub * (len(lines) - 1)
        b = Box(cx, cy, bw, bh)
        r = bh / 2 if pill else 12
        sw = 1.5 if kind in ("official", "plain") else 2
        self.nodes.append(f'<rect x="{b.left:.1f}" y="{b.top:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="{r:.1f}" '
                          f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
        y = b.top + 11 + lh_main / 2
        self.nodes.append(self._text(cx, y, lines[0], self.MAIN, main, 700))
        y += lh_main / 2 + lh_sub / 2
        for s in lines[1:]:
            self.nodes.append(self._text(cx, y, s, self.SUB, sub))
            y += lh_sub
        if step is not None:
            self.nodes.append(f'<circle cx="{b.left:.1f}" cy="{b.top:.1f}" r="12" fill="{C["primary600"]}" stroke="white" stroke-width="2"/>')
            self.nodes.append(self._text(b.left, b.top, str(step), 12, C["white"], 700))
        return b

    def db(self, cx, cy, lines, w=200):
        """資料庫（圓柱）"""
        fill, stroke, main, sub = KINDS["data"]
        h = 26 + 21 + 18 * (len(lines) - 1) + 12
        top, e = cy - h / 2, 9
        self.nodes.append(
            f'<path d="M{cx - w / 2:.1f},{top + e:.1f} a{w / 2:.1f},{e} 0 0,1 {w:.1f},0 v{h - 2 * e:.1f} '
            f'a{w / 2:.1f},{e} 0 0,1 {-w:.1f},0 z" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
        self.nodes.append(f'<path d="M{cx - w / 2:.1f},{top + e:.1f} a{w / 2:.1f},{e} 0 0,0 {w:.1f},0" fill="none" stroke="{stroke}" stroke-width="2"/>')
        y = top + 2 * e + 8 + 10.5
        self.nodes.append(self._text(cx, y, lines[0], self.MAIN, main, 700))
        y += 19.5
        for s in lines[1:]:
            self.nodes.append(self._text(cx, y, s, self.SUB, sub))
            y += 18
        return Box(cx, cy, w, h)

    # ---- 連線 ----
    def edge(self, pts, label=None, label_at=None, dashed=False, both=False, color=None, label_side="c", head=True):
        color = color or C["gray400"]
        d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        dash = ' stroke-dasharray="5 5"' if dashed else ""
        start = ' marker-start="url(#arrow-start)"' if both else ""
        self.edges.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.8" stroke-linejoin="round"{dash}'
                          f'{start}{' marker-end="url(#arrow)"' if head else ""}/>')
        if label:
            if label_at is None:
                (x1, y1), (x2, y2) = pts[len(pts) // 2 - 1], pts[len(pts) // 2]
                label_at = ((x1 + x2) / 2, (y1 + y2) / 2)
            self.label(*label_at, label, anchor={"c": "middle", "l": "end", "r": "start"}[label_side])

    def label(self, x, y, s, anchor="middle", color=None):
        w = text_width(s, self.SUB) + 14
        rx = {"middle": x - w / 2, "start": x, "end": x - w}[anchor]
        self.front.append(f'<rect x="{rx:.1f}" y="{y - 11:.1f}" width="{w:.1f}" height="22" rx="11" fill="white" '
                          f'stroke="{C["gray100"]}"/>')
        self.front.append(self._text(rx + w / 2, y, s, self.SUB, color or C["gray600"], 600))

    def note(self, x, y, s, anchor="start", color=None, size=None):
        self.front.append(self._text(x, y, s, size or self.SUB, color or C["gray500"], 400, anchor))

    def legend(self, x, y, items):
        for kind, s in items:
            fill, stroke, *_ = KINDS[kind]
            self.front.append(f'<rect x="{x}" y="{y - 7}" width="18" height="14" rx="4" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')
            self.front.append(self._text(x + 26, y, s, 12.5, C["gray600"], 400, "start"))
            x += 26 + text_width(s, 12.5) + 28

    # ---- 輸出 ----
    def svg(self) -> str:
        head = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}" font-family="{FONT}" role="img" aria-label="{escape(self.title)}">
<title>{escape(self.title)}</title>
<defs>
  <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{C["gray500"]}"/></marker>
  <marker id="arrow-start" viewBox="0 0 10 10" refX="1" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M10,0 L0,5 L10,10 z" fill="{C["gray500"]}"/></marker>
</defs>
<rect x="1" y="1" width="{self.w - 2}" height="{self.h - 2}" rx="20" fill="white" stroke="{C["gray100"]}" stroke-width="2"/>
<rect x="1" y="1" width="{self.w - 2}" height="6" rx="3" fill="{C["primary500"]}"/>
'''
        title = self._text(32, 38, self.title, self.TITLE, C["gray800"], 700, "start")
        sub = self._text(32, 64, self.subtitle, 13, C["gray500"], 400, "start") if self.subtitle else ""
        body = "\n".join(self.back + self.edges + self.nodes + self.front)
        return head + title + sub + "\n" + body + "\n</svg>\n"

    def save(self, name: str):
        path = os.path.join(OUT, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.svg())
        print("寫入", os.path.relpath(path))


# =====================================================================
# 5.1 架構圖
# =====================================================================
def architecture():
    d = Diagram(1180, 954, "長輩模式架構", "① 城市通 App 開啟 → ② 長輩模式微服務 → ③ App 原生能力；資料來自 data.taipei")
    user = d.box(250, 110, ["長輩・視障者・聽障者"], "user", pill=True, w=230)

    d.group(40, 150, 780, 128, "① 城市通 App", "gray")
    svc = d.box(250, 222, ["服務頁「長輩模式」", "my_service_model.dart，預設置頂"], "ours", w=300)
    wv = d.box(610, 222, ["TPWebView", "TownPass fork・Flutter 3.47.6"], "official", w=300)
    d.edge([user.side("b"), svc.side("t")])
    d.edge([svc.side("r"), wv.side("l")])

    d.group(40, 330, 780, 250, "② 長輩模式微服務")
    pages = d.box(610, 400, ["前端頁面 M1～M12", "townpass2026-peakqi・Next.js 16", "React 19・Tailwind 4・Vercel 東京"], "ours", w=330)
    data = d.box(170, 515, ["services.json", "M3 服務清單 27 筆", "打包在前端，斷網可用"], "ours", w=220)
    bridge = d.box(420, 515, ["bridge.ts・elder.ts", "呼叫 App 能力", "一般瀏覽器改用 mock"], "ours", w=220)
    api = d.box(680, 515, ["後端 /api/opendata", "白名單代理・Big5 轉碼", "TWD97 換算・CDN 快取"], "ours", w=230)
    od = d.db(1000, 515, ["data.taipei", "開放資料 28 個來源"], w=220)
    d.edge([wv.side("b"), pages.side("t")], "HTTPS 載入網頁", (610, 304))
    bus_y = 466
    d.edge([pages.side("b"), (610, bus_y), (170, bus_y), data.side("t")])
    d.edge([(610, bus_y), (420, bus_y), bridge.side("t")])
    d.edge([(610, bus_y), (680, bus_y), api.side("t")], "fetch", (680, 446))
    d.edge([api.side("r"), (od.left, 515)], "HTTPS", (840, 497))

    d.group(40, 632, 1100, 268, "③ App 原生能力", "gray")
    lis = d.box(420, 706, ["flutterObject ⇄ TPWebMessageListener", "依訊息名稱分派給 Handler，再回覆網頁"], "official", w=340)
    d.edge([bridge.side("b"), lis.side("t")], "postMessage 雙向溝通", (440, 606), dashed=True, both=True, label_side="r")
    row_y = 830
    handlers = [
        ("speak", "flutter_tts", "語音朗讀"), ("a11y_state", "報讀軟體", "系統字級"), ("haptic", "HapticFeedback", "震動回饋"),
        ("open_external", "url_launcher", "LINE・簡訊"), ("listen", "speech_to_text", "只在手機上辨識"),
        ("reminder", "local_notifications", "排程手機通知"),
    ]
    built = d.box(165, row_y, ["內建 Handler（官方）", "userinfo・location", "phone_call・1999agree", "open_link・launch_map", "notify・qr_code_scan"], "official", w=220)
    xs = [358 + i * 146 for i in range(6)]
    boxes = [d.box(x, row_y, list(h), "ours", w=134) for x, h in zip(xs, handlers)]
    fan_y = 752
    d.edges.append(f'<path d="M{lis.cx},{lis.bottom} V{fan_y} M{built.cx},{fan_y} H{xs[-1]}" fill="none" stroke="{C["gray400"]}" stroke-width="1.8"/>')
    for b in [built] + boxes:
        d.edge([(b.cx, fan_y), b.side("t")])
    d.legend(40, 926, [("ours", "我們新增或修改"), ("official", "城市通原有"), ("data", "外部開放資料"), ("user", "使用者")])
    d.save("architecture.svg")


# =====================================================================
# M5 叫車分流
# =====================================================================
def ride():
    d = Diagram(1080, 470, "M5 我要叫車：最多兩題就分流", "復康巴士只限有身障證明的人搭；不知道也有路可走")
    q1 = d.box(170, 190, ["有身心障礙證明嗎？", "有／沒有／不知道"], "decision", pill=True, w=250)
    q2 = d.box(170, 340, ["家裡申請過長照，", "2 級以上嗎？", "是／不是／不知道"], "decision", w=250)
    r1 = d.box(820, 140, ["復康巴士", "預約網站・電話訂車（8:00–17:00 受理）"], "result", w=380)
    r2 = d.box(820, 250, ["長照交通接送", "每月給付上限 1,680 元"], "result", w=380)
    r3 = d.box(820, 340, ["敬老愛心計程車", "撥 55850，接通後按 0；每趟最多扣 85 點"], "result", w=380)
    r4 = d.box(820, 430, ["先問 1966，也先列出敬老計程車", "長照等級不確定時，由 1966 幫忙查"], "warn", w=380)
    d.edge([q1.side("r"), (470, 190), (470, 140), r1.side("l")], "有", (530, 140))
    d.edge([q1.side("b"), q2.side("t")], "沒有、不知道", (170, 262))
    d.edge([q2.side("r"), (470, 340), (470, 250), r2.side("l")], "是", (530, 250))
    d.edge([(470, 340), r3.side("l")], "不是", (560, 340))
    d.edge([(470, 340), (470, 430), r4.side("l")], "不知道", (545, 430))
    d.note(40, 452, "聽不清楚模式：結果是只能打電話的服務時，另外給「手語視訊轉譯」", "start")
    d.save("m5-ride.svg")


# =====================================================================
# M12 補助小幫手
# =====================================================================
def subsidy():
    d = Diagram(1080, 560, "M12 補助小幫手：三題篩出「可能可以申請」的補助", "答案只存在手機的記憶體裡，不上傳；最後由社會局審核")
    auto = d.box(540, 125, ["自動帶入（不用問）", "年齡・原住民身分（門檻降 10 歲）・行政區 ← 台北通帳號"], "official", w=560)
    qs = [
        (190, ["① 有身心障礙證明嗎？", "有 → 看不清楚／聽不清楚／其他", "沒有・不知道"]),
        (540, ["② 家裡收入", "有低收或中低收證明", "沒有，但收入不高・不知道"]),
        (890, ["③ 家裡有人需要別人照顧嗎？", "要・不要・不知道"]),
    ]
    qb = [d.box(x, 255, lines, "decision", w=320) for x, lines in qs]
    d.edges.append(f'<path d="M540,{auto.bottom} V190 M190,190 H890" fill="none" stroke="{C["gray400"]}" stroke-width="1.8"/>')
    for b in qb:
        d.edge([(b.cx, 190), b.side("t")])
    rs = [
        (190, ["您可能可以申請", "老人津貼・身障生活補助・長照…", "收入「不知道」也列出，標「要看家裡收入」"], "result"),
        (540, ["不用申請，會自動入帳或減免", "例如已是低收、中低收的身障生活補助"], "ours"),
        (890, ["答「不知道」的提示", "例如照顧題附 1966 按鈕"], "warn"),
    ]
    rb = [d.box(x, 400, lines, kind, w=320) for x, lines, kind in rs]
    d.edges.append(f'<path d="M190,{qb[0].bottom} V318 M540,{qb[1].bottom} V318 M890,{qb[2].bottom} V318 M190,318 H890" fill="none" stroke="{C["gray400"]}" stroke-width="1.8"/>')
    for b in rb:
        d.edge([(b.cx, 318), b.side("t")])
    card = d.box(540, 505, ["每張卡片：一句話＋大約金額・要準備什麼（勾選）・戶籍地社會課地址電話・家人能不能代辦・申請準備單（可複製傳給家人）"], "plain", w=1000)
    d.edge([rb[0].side("b"), (190, 470)])
    d.save("m12-subsidy.svg")


# =====================================================================
# 5.2 主要流程
# =====================================================================
def flow_open():
    d = Diagram(1180, 300, "① 開啟長輩模式", "打開時先在首頁前墊一筆「選模式」的瀏覽紀錄，城市通的返回鍵就能回去換模式")
    steps = [
        (["台北通「我的服務」", "點「長輩模式」"], "official"),
        (["WebView 載入網頁", "Vercel 東京"], "official"),
        (["向 App 要資料", "userinfo：姓名・生日・行政區", "a11y_state：報讀軟體・字級"], "ours"),
        (["讀手機裡的設定", "模式・語速・家人設定的按鈕"], "ours"),
        (["算年齡、篩選", "首頁按鈕・權益卡片 → 畫面"], "result"),
    ]
    xs = [140 + i * 225 for i in range(5)]
    bs = [d.box(x, 175, lines, kind, w=200, step=i + 1) for i, (x, (lines, kind)) in enumerate(zip(xs, steps))]
    for a, b in zip(bs, bs[1:]):
        d.edge([a.side("r"), b.side("l")])
    d.note(40, 270, "第一次使用（還沒選模式）會先到「選模式」頁；同時預載全部頁面，之後斷網也能在各頁之間切換。", "start")
    d.save("flow-1-open.svg")


def flow_press():
    d = Diagram(1180, 410, "② 按一顆大按鈕", "每個回饋至少兩種感官：震動＋大字＋聲音；開著報讀軟體時不自己唸，避免唸兩次")
    tap = d.box(110, 150, ["點按"], "user", pill=True, w=110)
    hap = d.box(280, 150, ["震動", "haptic"], "ours", w=140)
    q = d.box(490, 150, ["報讀軟體開著嗎？"], "decision", pill=True, w=200)
    s1 = d.box(760, 100, ["唸出名稱＋大字", "speak・role=\"status\""], "ours", w=230)
    s2 = d.box(760, 200, ["只顯示大字", "報讀軟體自己會唸"], "ours", w=230)
    conf = d.box(1040, 150, ["需要時先確認", "例如撥號確認頁"], "ours", w=200)
    d.edge([tap.side("r"), hap.side("l")])
    d.edge([hap.side("r"), q.side("l")])
    d.edge([q.side("r"), (620, 150), (620, 100), s1.side("l")], "沒開", (620, 125), label_side="c")
    d.edge([(620, 150), (620, 200), s2.side("l")], "開著", (620, 178))
    d.edge([s1.side("r"), (900, 100), (900, 150), conf.side("l")])
    d.edge([s2.side("r"), (900, 200), (900, 150)], head=False)
    run = d.box(720, 320, ["依服務的 action 執行", "phone_call・1999agree・open_link", "open_external・切換頁面"], "result", w=320)
    ok = d.box(1060, 320, ["完成"], "result", pill=True, w=120)
    fail = d.box(250, 320, ["打不開時", "改用 fallback；聽不清楚模式先給文字管道", "失敗訊息留在按鈕下方，不會 4 秒就消失"], "warn", w=360)
    d.edge([conf.side("b"), (1040, 255), (720, 255), run.side("t")])
    d.edge([run.side("r"), ok.side("l")], "成功", (940, 320))
    d.edge([run.side("l"), fail.side("r")], "失敗", (500, 320))
    d.save("flow-2-press.svg")


def flow_find():
    d = Diagram(1180, 480, "③ 找服務", "比對完全在手機上執行，不用 AI 模型；頁面打開後斷網也能用")
    t1 = d.box(150, 125, ["打字"], "ours", w=200)
    t2 = d.box(150, 215, ["點一下開始說話", "再點一下停止"], "ours", w=200)
    t3 = d.box(150, 420, ["點分類", "看病・交通・權益…"], "ours", w=200)
    lis = d.box(430, 215, ["listen", "在手機上辨識，不上傳"], "ours", w=220)
    err = d.box(430, 330, ["手機不支援離線辨識", "提示改用打字"], "warn", w=220)
    norm = d.box(720, 165, ["正規化、比對", "services.json 的長輩說法 phrases"], "ours", w=270)
    top3 = d.box(1010, 125, ["「你是說：…？」", "最多三個大按鈕"], "result", w=240)
    none = d.box(1010, 245, ["都對不上", "「要不要打 1999 問問看」"], "warn", w=240)
    cat = d.box(1010, 420, ["該分類的服務清單"], "result", w=240)
    d.edge([t2.side("r"), lis.side("l")])
    d.edge([lis.side("b"), err.side("t")], "不支援", (430, 290))
    d.edge([t1.side("r"), (560, 125), (560, 165), norm.side("l")])
    d.edge([lis.side("r"), (560, 215), (560, 165)], "辨識出的文字", (572, 215), label_side="r", head=False)
    d.edge([norm.side("r"), (870, 165), (870, 125), top3.side("l")], "找到", (870, 108))
    d.edge([(870, 165), (870, 245), none.side("l")], "沒有", (870, 222))
    d.edge([t3.side("r"), cat.side("l")])
    d.save("flow-3-find.svg")


def flow_places():
    d = Diagram(1180, 380, "④ 附近據點（M9 吃飯上課、M10 視障出門）", "開放資料由後端代理：解決跨網域、Big5 亂碼、TWD97 座標與檔案太大的問題")
    src = d.box(150, 150, ["行政區或目前位置", "userinfo 地址・location"], "official", w=230)
    req = d.box(430, 150, ["fetch /api/opendata/…", "?q=中山區 或 ?near=緯度,經度"], "ours", w=270)
    wl = d.box(720, 150, ["白名單檢查", "只代理登記過的 28 個來源"], "ours", w=240)
    hit = d.box(1010, 150, ["快取有就直接回", "CDN 快取"], "ours", w=230)
    od = d.db(1010, 290, ["data.taipei", "沒有快取才抓"], w=230)
    conv = d.box(720, 290, ["Big5 轉碼・座標換算", "依距離或行政區篩選"], "ours", w=240)
    out = d.box(330, 290, ["一句話摘要＋大字電話按鈕", "斷網或讀不到：說明並給 1999"], "result", w=330)
    d.edge([src.side("r"), req.side("l")])
    d.edge([req.side("r"), wl.side("l")])
    d.edge([wl.side("r"), hit.side("l")])
    d.edge([hit.side("b"), (od.cx, od.top)], "沒有快取", (1010, 220))
    d.edge([(od.left, 290), conv.side("r")])
    d.edge([conv.side("l"), out.side("r")], "回傳前幾筆", (560, 272))
    d.save("flow-4-places.svg")


def flow_family():
    d = Diagram(1180, 400, "⑤ 家人代設定（M7）", "設定內容直接編在 QR code 裡，全程不經過伺服器")
    d.group(40, 86, 1100, 124, "家人的手機", "gray")
    d.group(40, 246, 1100, 124, "長輩的手機")
    f1 = d.box(200, 162, ["長輩模式「我是家人」", "幫長輩設定"], "ours", w=240)
    f2 = d.box(520, 162, ["勾首頁按鈕", "填家人電話與行政區"], "ours", w=240)
    f3 = d.box(860, 162, ["產生 QR code", "設定內容在 QR 裡"], "result", w=240)
    e1 = d.box(200, 322, ["「家人幫我設定」"], "ours", w=240)
    e2 = d.box(520, 322, ["qr_code_scan 掃描", "檢查格式、版本、隱藏字元"], "ours", w=260)
    e3 = d.box(860, 322, ["存在手機裡", "首頁按鈕換好・唸「設定好了」"], "result", w=260)
    for a, b in [(f1, f2), (f2, f3), (e1, e2), (e2, e3)]:
        d.edge([a.side("r"), b.side("l")])
    d.edge([(f3.right, 162), (1060, 162), (1060, 228), (520, 228), e2.side("t")], "長輩的手機對準 QR 掃描", (790, 228), dashed=True)
    d.save("flow-5-family.svg")


def flow_benefit():
    d = Diagram(1180, 330, "⑥ 權益提醒（M6）", "由生日自動判斷資格；重陽禮金可以設定手機通知，App 關掉也會跳出來")
    a = d.box(150, 165, ["台北通帳號的生日", "userinfo"], "official", w=210)
    b = d.box(400, 165, ["算年齡、比對資格", "原住民門檻降 10 歲"], "ours", w=220)
    c = d.box(680, 165, ["權益卡片", "「可能可以領 3,000 元，還有 6 天截止」"], "result", w=300)
    d1 = d.box(1010, 110, ["線上申請匯款", "open_external 開社會局網站"], "ours", w=250)
    d2 = d.box(1010, 220, ["提醒我申請", "reminder：11/12 早上 9 點通知"], "ours", w=250)
    d.edge([a.side("r"), b.side("l")])
    d.edge([b.side("r"), c.side("l")])
    d.edge([c.side("r"), (860, 165), (860, 110), d1.side("l")])
    d.edge([(860, 165), (860, 220), d2.side("l")])
    d.note(40, 300, "也可以打給戶籍地的區公所社會課（撥號前有確認頁）。", "start")
    d.save("flow-6-benefit.svg")


if __name__ == "__main__":
    architecture()
    ride()
    subsidy()
    flow_open()
    flow_press()
    flow_find()
    flow_places()
    flow_family()
    flow_benefit()
