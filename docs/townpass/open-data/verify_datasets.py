"""驗證 data.taipei 資料集：取得資源清單、實際下載、解析欄位與筆數、檢查 CORS。"""
import csv, io, json, re, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor

BASE = "https://data.taipei"
UA = {"User-Agent": "townpass-hackathon-research"}
PIDS = sys.argv[1].split(",")
OUT = sys.argv[2]


def get(url, timeout=40, maxbytes=8_000_000):
    req = urllib.request.Request(url, headers={**UA, "Origin": "https://townpass2026-peakqi.vercel.app"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, dict(r.headers), r.geturl(), r.read(maxbytes)


def decode(b):
    for enc in ("utf-8-sig", "big5", "cp950"):
        try:
            return b.decode(enc), enc
        except UnicodeDecodeError:
            pass
    return b.decode("utf-8", "replace"), "utf-8?"


def find_records(obj):
    """在 JSON 裡找出最大的 list of dict。"""
    best = None
    def walk(o, path):
        nonlocal best
        if isinstance(o, list) and o and isinstance(o[0], dict):
            if best is None or len(o) > len(best[1]):
                best = (path, o)
        if isinstance(o, dict):
            for k, v in o.items():
                walk(v, path + [k])
        elif isinstance(o, list):
            for v in o[:3]:
                walk(v, path + ["[]"])
    walk(obj, [])
    return best


GEO = re.compile(r"lat|lng|lon|經度|緯度|座標|坐標|^x$|^y$|twd97|wgs|_x$|_y$|longitude|latitude", re.I)


def check_resource(res):
    rid = res.get("rid")
    url = f"{BASE}/api/frontstage/tpeod/dataset/resource.download?rid={rid}" if res.get("url_type") != "" else res.get("url")
    info = {"rid": rid, "name": res.get("name"), "format": res.get("format"), "last_modified": res.get("last_modified"),
            "download_url": url, "datastore_api": f"{BASE}/api/v1/dataset/{rid}?scope=resourceAquire" if res.get("has_datastore") else None}
    try:
        status, headers, final, body = get(url)
        info.update(status=status, final_url=final, content_type=headers.get("Content-Type"),
                    cors=headers.get("Access-Control-Allow-Origin"), bytes=len(body))
        text, enc = decode(body)
        info["encoding"] = enc
        fields, rows = [], []
        t = text.lstrip()
        if t.startswith("{") or t.startswith("["):
            obj = json.loads(text)
            found = find_records(obj)
            if found:
                info["json_path"] = ".".join(found[0])
                rows = found[1]
                fields = list(rows[0].keys())
        elif t.startswith("<"):
            info["note"] = "XML"
            tags = re.findall(r"<([A-Za-z_][\w:.-]*)[ >]", text[:20000])
            info["xml_tags"] = list(dict.fromkeys(tags))[:30]
            info["records_estimate"] = text.count("<" + info["xml_tags"][1] + ">") if len(info["xml_tags"]) > 1 else None
        else:
            rdr = list(csv.DictReader(io.StringIO(text)))
            rows = rdr
            fields = list(rdr[0].keys()) if rdr else []
        if rows:
            info["records"] = len(rows)
            info["fields"] = fields
            info["sample"] = {k: (str(v)[:60] if v is not None else None) for k, v in list(rows[0].items())[:14]}
            info["geo_fields"] = [f for f in fields if f and GEO.search(str(f))]
    except Exception as e:  # noqa
        info["error"] = f"{type(e).__name__}: {e}"[:200]
    return info


def check_dataset(pid):
    out = {"pid": pid, "page": f"{BASE}/dataset/detail?id={pid}"}
    try:
        _, _, _, body = get(f"{BASE}/api/frontstage/tpeod/dataset.view?id={pid}")
        p = json.loads(body)["payload"]
        out.update(title=p.get("title"), org=p.get("org_name"), sub_org=p.get("sub_org_name"),
                   update_freq=p.get("update_frequency") or p.get("frequency"), license=p.get("license_title") or p.get("license"),
                   keys=list(p.keys()))
        res = p.get("resources") or []
        out["resources"] = [check_resource(r) for r in res[:4]]
        out["resource_count"] = len(res)
    except Exception as e:  # noqa
        out["error"] = f"{type(e).__name__}: {e}"[:200]
    return out


with ThreadPoolExecutor(6) as ex:
    results = list(ex.map(check_dataset, PIDS))
json.dump(results, open(OUT, "w"), ensure_ascii=False, indent=1)
for r in results:
    print("==", r.get("title"), "|", r.get("update_freq"), "|", r.get("error", ""))
    for s in r.get("resources", []):
        print("   ", s.get("format"), s.get("status"), "records=", s.get("records", s.get("records_estimate")), "geo=", s.get("geo_fields"),
              "cors=", s.get("cors"), "err=", s.get("error", ""))
