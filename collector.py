# Kayser Cloud Collector - laeuft stuendlich auf GitHub-Servern (unabhaengig vom Mac)
import json, os, datetime, urllib.request
import xml.etree.ElementTree as ET

UA = {"User-Agent": "Mozilla/5.0 (KayserCloud/1.0)"}

def get(url, timeout=25):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "ignore")

now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

# 1) Kurse (Yahoo Chart API)
quotes = {}
syms = [("USDCHF=X","USDCHF"),("USDJPY=X","USDJPY"),("GBPCAD=X","GBPCAD"),("AUDJPY=X","AUDJPY"),
        ("EURUSD=X","EURUSD"),("GBPCHF=X","GBPCHF"),("CL=F","WTI"),("BZ=F","BRENT"),
        ("GC=F","GOLD"),("ES=F","SPX_FUT"),("NQ=F","NAS_FUT")]
for ysym, name in syms:
    try:
        j = json.loads(get("https://query1.finance.yahoo.com/v8/finance/chart/" + ysym + "?range=5d&interval=1d"))
        r = j["chart"]["result"][0]; m = r["meta"]
        closes = [x for x in r["indicators"]["quote"][0]["close"] if x is not None]
        price = m.get("regularMarketPrice") or (closes[-1] if closes else None)
        prev = closes[-2] if len(closes) > 1 else None
        quotes[name] = {"price": round(price, 5) if price else None,
                        "chg1d_pct": round((price/prev - 1) * 100, 2) if price and prev else None}
    except Exception as e:
        quotes[name] = {"err": str(e)[:60]}

# 2) News (Google News RSS, deutsch)
heads = []
try:
    rss = get("https://news.google.com/rss/search?q=(forex%20OR%20oil%20OR%20iran%20OR%20fed%20OR%20yen%20OR%20intervention)&hl=de&gl=DE&ceid=DE:de")
    root = ET.fromstring(rss)
    for it in root.iter("item"):
        t = it.find("title"); l = it.find("link"); p = it.find("pubDate")
        heads.append({"t": t.text if t is not None else "",
                      "link": l.text if l is not None else "",
                      "pub": p.text if p is not None else ""})
        if len(heads) >= 12: break
except Exception as e:
    heads = [{"t": "RSS-Fehler: " + str(e)[:60]}]

# 3) Schreiben: latest.json + wachsende History (Langzeit-Trainingsdaten fuer VECTOR)
os.makedirs("data/history", exist_ok=True)
latest = {"collected_at": now, "source": "GitHub Actions Cloud (laeuft auch bei Mac aus)",
          "quotes": quotes, "headlines": heads}
open("data/latest.json", "w").write(json.dumps(latest, ensure_ascii=False, indent=1))
with open("data/history/" + now[:10] + ".jsonl", "a") as f:
    f.write(json.dumps({"z": now, "quotes": quotes, "n_headlines": len(heads)}, ensure_ascii=False) + "\n")
print("OK", now)
