#!/usr/bin/env python3
"""Bản tin giữa phiên (mode "giua") và cuối ngày (mode "cuoi"), 1 ảnh khổ điện thoại 1080x1920.
Dùng chung logo, màu, font và cách tô số với weha_sang.py. Chạy: python3 weha_phien_dt.py du_lieu.json out"""
import json, os, sys, re, asyncio
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from weha_sang import LOGO, CSS, CSS_M, esc, rich, boldnum, news, tile

TITLE = {"giua": "CẬP NHẬT PHIÊN SÁNG", "cuoi": "TỔNG KẾT CUỐI NGÀY"}
NAME = {"giua": "trua", "cuoi": "cuoi"}

CSS_P = """
.page h2{margin:10px 0 6px;padding-top:8px} .page .strip{margin-top:6px}
.page .lede{white-space:normal;font-size:19px;line-height:1.45;margin:0 0 4px}
.page .tile4{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
.page .list p{font-size:calc(25px*var(--k));line-height:1.4;padding:7px 0}
.heat{display:grid;grid-template-columns:repeat(10,1fr);gap:5px}
.heat div{border-radius:5px;padding:5px 0 4px;text-align:center;line-height:1.15}
.heat b{display:block;font-size:19px;font-weight:700} .heat span{font-size:15px;font-weight:600}
.legend{display:flex;gap:16px;font-size:15px;color:#3D3C38;margin-top:8px;font-weight:600}
.legend i{display:inline-block;width:14px;height:14px;border-radius:3px;margin-right:6px;vertical-align:-2px}
.sec .r{display:grid;grid-template-columns:150px 1fr 96px;align-items:center;gap:10px;margin:5px 0;font-size:21px}
.sec .r b{font-weight:600;white-space:nowrap} .sec .bar{height:20px;border-radius:3px}
.sec .v{text-align:right;font-weight:700}
.sec.n .r{grid-template-columns:70px 1fr 74px;font-size:20px;margin:4px 0} .sec.n .bar{height:18px}
.chart svg{display:block;width:100%;height:auto}
.mac{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
.mac .card{text-align:center;padding:6px 6px} .mac .n{font-family:Lora,serif;font-size:32px;line-height:1.05}
.mac .t{font-size:17px;font-weight:600;color:#141413}
.note{font-size:17px;color:#3D3C38;margin:6px 0 0;font-weight:500}
"""

def vn(x, dec=0, sign=False):
    s = f"{abs(x):,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if x < 0: return "−" + s
    return ("+" + s) if sign and x > 0 else s

def clean(t):
    return re.sub(r"</?b[^>]*>|</?span[^>]*>", "", str(t))

def nb(t):
    return re.sub(r"(?<=\d)–(?=\d)", "–\u2060", str(t))

def line(t):
    return f"<p>{boldnum(rich(clean(nb(t))))}</p>"

def tone(v): return "up" if v > 0 else ("down" if v < 0 else "")

# ---------- tính toán từ danh sách stocks ----------
def contributions(d):
    st = d.get("stocks") or []
    chg = d.get("chg")
    if not st or chg is None: return [], []
    sc = [(s[0], s[2] * s[3] / (100 + s[3])) for s in st]
    tot = sum(v for _, v in sc)
    if abs(tot) < 1e-9: return [], []
    ct = [(s, chg * v / tot) for s, v in sc]
    ct.sort(key=lambda x: x[1], reverse=True)
    up = [x for x in ct if x[1] >= 0.05][:4]
    dn = sorted([x for x in ct if x[1] <= -0.05], key=lambda x: x[1])[:4]
    return up, dn

def sectors(d):
    agg = {}
    for s in d.get("stocks") or []:
        a = agg.setdefault(s[1], [0.0, 0.0])
        a[0] += s[2] * s[3]; a[1] += s[2]
    rows = [(k, v[0] / v[1]) for k, v in agg.items() if v[1] > 0]
    rows.sort(key=lambda x: x[1], reverse=True)
    return rows

# ---------- khối giao diện ----------
def bars(rows, unit, dec, signed=True):
    mx = max([abs(v) for _, v in rows] or [1]) or 1
    out = ""
    for s, v in rows:
        cls = "b" if v > 0 else "s"
        w = max(4, abs(v) / mx * 100)
        out += (f'<div class="r"><b>{esc(s)}</b><div><div class="bar {cls}" style="width:{w:.0f}%"></div></div>'
                f'<div class="v {"pos" if v > 0 else "neg"}">{vn(v, dec, signed)}{unit}</div></div>')
    return out

def card_bars(title, up, dn, unit, dec, hu="Kéo lên", hd="Kéo xuống"):
    return (f'<div class="card fl sec"><h3>{esc(title)}</h3><div class="h">{hu}</div>{bars(up, unit, dec)}'
            f'<div class="h">{hd}</div>{bars(dn, unit, dec)}</div>')

def side_cards(up, dn, title_up="Kéo lên", title_dn="Kéo xuống", unit="", dec=1):
    return (f'<div class="grid g2"><div class="card fl sec n"><h3>{title_up}</h3>{bars(up, unit, dec)}</div>'
            f'<div class="card fl sec n"><h3>{title_dn}</h3>{bars(dn, unit, dec)}</div></div>')

def sector_card(d, n=8):
    rows = sectors(d)
    if not rows: return ""
    if len(rows) > n:
        rows = rows[: n // 2] + rows[-(n - n // 2):]
    mx = max(abs(v) for _, v in rows) or 1
    out = ""
    for s, v in rows:
        out += (f'<div class="r"><b>{esc(s)}</b><div><div class="bar {"b" if v > 0 else "s"}" style="width:{max(4, abs(v)/mx*100):.0f}%;'
                f'background:{"#2F7D4F" if v > 0 else "#B8432F"}"></div></div><div class="v {"pos" if v > 0 else "neg"}">{vn(v, 2, True)}%</div></div>')
    return f'<div class="card sec">{out}</div>'

def heat(d):
    st = sorted(d.get("stocks") or [], key=lambda s: -s[2])[:60]
    if not st: return ""
    def col(p):
        a = min(abs(p) / 5.0, 1.0)
        if abs(p) < 0.05: return "#E4E2D8", "#141413"
        if p > 0:
            base = (47, 125, 79); lite = (214, 233, 220)
        else:
            base = (184, 67, 47); lite = (244, 214, 207)
        c = tuple(round(l + (b - l) * a) for l, b in zip(lite, base))
        return "rgb(%d,%d,%d)" % c, ("#fff" if a > .55 else "#141413")
    cells = ""
    for s in st:
        bg, fg = col(s[3])
        cells += f'<div style="background:{bg};color:{fg}"><b>{esc(s[0])}</b><span>{vn(s[3], 1, True)}</span></div>'
    return (f'<div class="heat">{cells}</div><div class="legend"><span><i style="background:#B8432F"></i>Giảm mạnh</span>'
            f'<span><i style="background:#E4E2D8"></i>Đứng giá</span><span><i style="background:#2F7D4F"></i>Tăng mạnh</span>'
            f'<span style="margin-left:auto">60 mã vốn hóa lớn HOSE</span></div>')

def chart(d):
    pts = d.get("intraday") or []
    if len(pts) < 2: return ""
    W, H, L, R, T, B = 972, 225, 66, 16, 26, 34
    ys = [p[1] for p in pts] + [d["ref"]]
    lo, hi = min(ys), max(ys); pad = (hi - lo) * 0.12 or 1
    lo -= pad; hi += pad
    X = lambda i: L + (W - L - R) * i / (len(pts) - 1)
    Y = lambda v: T + (H - T - B) * (hi - v) / (hi - lo)
    path = " ".join(("M" if i == 0 else "L") + f"{X(i):.1f},{Y(p[1]):.1f}" for i, p in enumerate(pts))
    area = path + f" L{X(len(pts)-1):.1f},{H-B} L{X(0):.1f},{H-B} Z"
    up = pts[-1][1] >= d["ref"]
    c = "#2F7D4F" if up else "#B8432F"
    grid = ""
    for k in range(4):
        v = lo + (hi - lo) * k / 3
        grid += (f'<line x1="{L}" x2="{W-R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="#E6E3D8"/>'
                 f'<text x="{L-8}" y="{Y(v)+7:.1f}" font-size="19" text-anchor="end" fill="#6F6E68">{vn(v, 0)}</text>')
    step = max(1, (len(pts) - 1) // 4)
    idx = list(range(0, len(pts), step))
    if idx[-1] != len(pts) - 1: idx.append(len(pts) - 1)
    xl = "".join(f'<text x="{X(i):.1f}" y="{H-12}" font-size="19" text-anchor="{"end" if i == len(pts)-1 else ("start" if i == 0 else "middle")}" fill="#6F6E68">{esc(pts[i][0])}</text>' for i in idx)
    ry = Y(d["ref"])
    ref = (f'<line x1="{L}" x2="{W-R}" y1="{ry:.1f}" y2="{ry:.1f}" stroke="#141413" stroke-dasharray="6 5" stroke-width="1.5"/>'
           f'<text x="{W-R}" y="{ry-8:.1f}" font-size="19" text-anchor="end" fill="#141413" font-weight="600">Tham chiếu {vn(d["ref"], 2)}</text>')
    hi_i = max(range(len(pts)), key=lambda i: pts[i][1]); lo_i = min(range(len(pts)), key=lambda i: pts[i][1])
    def lab(i, t, dy):
        anchor = "start" if X(i) < W * .75 else "end"
        dx = 8 if anchor == "start" else -8
        return f'<circle cx="{X(i):.1f}" cy="{Y(pts[i][1]):.1f}" r="5" fill="{c}"/><text x="{X(i)+dx:.1f}" y="{Y(pts[i][1])+dy:.1f}" font-size="20" font-weight="700" text-anchor="{anchor}" fill="#141413">{t}</text>'
    marks = lab(hi_i, f"Cao {vn(pts[hi_i][1], 2)}", -10) + lab(lo_i, f"Thấp {vn(pts[lo_i][1], 2)}", -34)
    return (f'<div class="card chart"><svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="Inter,sans-serif">{grid}{xl}'
            f'<path d="{area}" fill="{c}" opacity=".10"/>{ref}<path d="{path}" fill="none" stroke="{c}" stroke-width="3.5" stroke-linejoin="round"/>{marks}</svg></div>')

def flow_pair(title, net, note, lst):
    buy = sorted([(s, v) for s, v in lst if v > 0], key=lambda x: -x[1])[:3]
    sell = sorted([(s, v) for s, v in lst if v < 0], key=lambda x: x[1])[:3]
    head = f'{esc(title)} · <span class="{"pos" if net > 0 else "neg"}">{vn(net, 0, True)} tỷ</span>'
    return (f'<div class="card fl sec"><h3>{head}</h3><div class="h">Mua ròng (tỷ)</div>{bars(buy, "", 1)}'
            f'<div class="h">Bán ròng (tỷ)</div>{bars(sell, "", 1)}</div>')

def mac(d):
    m = d.get("macd")
    if not m: return ""
    items = [("Mua, tích lũy", m["buy"], "pos"), ("Tăng tỷ trọng", m["raise"], "pos"), ("Giảm tỷ trọng", m["reduce"], "neg"), ("Bán toàn bộ", m["sell"], "neg")]
    cards = "".join(f'<div class="card"><div class="n {c}">{n}</div><div class="t">{t}</div></div>' for t, n, c in items)
    return f'<div class="mac">{cards}</div><p class="note">{esc(m.get("note",""))}</p>'

def pct_of(d):
    return d["chg"] / d["ref"] * 100

# ---------- 2 chế độ ----------
def page_giua(d):
    p = pct_of(d)
    up, dn = contributions(d)
    tiles = [
        {"label": "VN-Index", "value": vn(d["now"], 2), "note": f'{vn(d["chg"], 2, True)} ({vn(p, 2, True)}%)', "tone": tone(d["chg"])},
        {"label": "Khối lượng sáng", "value": f'{vn(d["vol_m"], 0)} tr cp', "note": f'{d["vol_pct_avg20"]}% bình quân 20 phiên'},
        {"label": "Khối ngoại ròng", "value": f'{vn(d["foreign_net"], 0, True)} tỷ', "note": d.get("foreign_note", ""), "tone": tone(d["foreign_net"])},
        {"label": "Độ rộng HOSE", "value": f'{d["up"]}/{d["down"]}', "note": f'tăng/giảm · {d["flat"]} đứng giá'},
    ]
    notes = "".join(line(x) for x in d.get("breadth_notes", []))
    extra = line(d["foreign_line"]) if d.get("foreign_line") else ""
    extra += line(d["deriv_line"]) if d.get("deriv_line") else ""
    return f"""<h1>{boldnum(rich(nb(d["headline"])), False).replace("VN-Index", "VN‑Index")}</h1>
<p class="lede">{boldnum(rich(d["lede"]), False)}</p>
<div class="tile4 mini" style="margin-top:8px">{"".join(tile(t) for t in tiles)}</div>
<h2><span class="no">01</span> Diễn biến phiên sáng</h2>{chart(d)}
<h2><span class="no">02</span> Bản đồ nhiệt cổ phiếu</h2>{heat(d)}
<h2><span class="no">03</span> Điểm số đóng góp</h2>
{side_cards(up, dn, "Kéo VN-Index lên (điểm)", "Kéo VN-Index xuống (điểm)") if up or dn else ""}
<h2><span class="no">04</span> Nhóm ngành và dòng tiền</h2>
<div class="card list">{notes}{extra}</div>"""

def page_cuoi(d):
    tiles = []
    for name, close, ref in d["indices"]:
        p = (close - ref) / ref * 100
        tiles.append({"label": name, "value": vn(close, 2), "note": f'{vn(p, 2, True)}%', "tone": tone(close - ref)})
    up, dn = contributions(d)
    movers = "".join(line(x) for x in re.split(r"\s*&nbsp;\|&nbsp;\s*", d.get("movers_line", "")) if x.strip())
    rs = line(d["rs_line"]) if d.get("rs_line") else ""
    fl = ""
    if d.get("foreign_top") is not None:
        fl += flow_pair("Khối ngoại", d["foreign_net"], d.get("foreign_note", ""), d["foreign_top"])
    if d.get("prop_top"):
        fl += flow_pair("Tự doanh", d["prop_net"], d.get("prop_note", ""), d["prop_top"])
    flows = f'<div class="grid g2">{fl}</div>' if fl else ""
    return f"""<h1>{boldnum(rich(nb(d["headline"])), False).replace("VN-Index", "VN‑Index")}</h1>
<p class="lede">{boldnum(rich(d["lede"]), False)}</p>
<div class="tile4 mini" style="margin-top:8px">{"".join(tile(t) for t in tiles)}</div>
<h2><span class="no">01</span> Đóng góp điểm và hiệu suất ngành</h2>
{side_cards(up, dn, "Kéo lên (điểm)", "Kéo xuống (điểm)") if up or dn else ""}<div style="margin-top:10px">{sector_card(d, 4)}</div>
<h2><span class="no">02</span> Dòng tiền</h2>{flows}
<h2><span class="no">03</span> Động lực và tín hiệu</h2>
<div class="card list">{movers}</div><div style="margin-top:10px">{mac(d)}</div>
<h2><span class="no">04</span> Kịch bản phiên tới</h2>
<div class="card list">{news([dict(i, text=nb(i["text"])) for i in d.get("scenarios", [])[:3]])}</div>"""


# ---------- Trang 2 bản cuối ngày: 10 phiên, dòng tiền 5 phiên, cổ phiếu đáng chú ý ----------
GREEN, RED, NAVY, GOLD = "#2F7D4F", "#B8432F", "#1B2B5B", "#E0A526"

def svg_wrap(W, H, inner):
    return f'<div class="card chart"><svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="Inter,sans-serif">{inner}</svg></div>'

def hist_chart(pts):
    """pts: [[dd/mm, close]] — đường VN-Index nhiều phiên, ghi số từng điểm."""
    if len(pts) < 2: return ""
    W, H, L, R, T, B = 972, 250, 66, 30, 36, 34
    ys = [p[1] for p in pts]; lo, hi = min(ys), max(ys); pad = (hi - lo) * .18 or 1; lo -= pad; hi += pad
    X = lambda i: L + (W - L - R) * i / (len(pts) - 1)
    Y = lambda v: T + (H - T - B) * (hi - v) / (hi - lo)
    c = GREEN if pts[-1][1] >= pts[0][1] else RED
    path = " ".join(("M" if i == 0 else "L") + f"{X(i):.1f},{Y(p[1]):.1f}" for i, p in enumerate(pts))
    area = path + f" L{X(len(pts)-1):.1f},{H-B} L{X(0):.1f},{H-B} Z"
    g = ""
    for k in range(4):
        v = lo + (hi - lo) * k / 3
        g += (f'<line x1="{L}" x2="{W-R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="#E6E3D8"/>'
              f'<text x="{L-8}" y="{Y(v)+7:.1f}" font-size="18" text-anchor="end" fill="#6F6E68">{vn(v, 0)}</text>')
    dots = ""
    for i, (dt, v) in enumerate(pts):
        col = GREEN if i == 0 or v >= pts[i-1][1] else RED
        anchor = "start" if i == 0 else ("end" if i == len(pts) - 1 else "middle")
        above = i in (0, len(pts) - 1) or v >= (pts[i-1][1] + pts[i+1][1]) / 2
        ty = Y(v) - 12 if above else Y(v) + 26
        dots += (f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="5" fill="{col}"/>'
                 f'<text x="{X(i):.1f}" y="{ty:.1f}" font-size="18" font-weight="700" text-anchor="{anchor}" fill="#141413" stroke="#fff" stroke-width="5" paint-order="stroke">{vn(v, 2)}</text>'
                 f'<text x="{X(i):.1f}" y="{H-10}" font-size="17" text-anchor="{anchor}" fill="#6F6E68">{esc(dt)}</text>')
    return svg_wrap(W, H, f'{g}<path d="{area}" fill="{c}" opacity=".10"/><path d="{path}" fill="none" stroke="{c}" stroke-width="3.5" stroke-linejoin="round"/>{dots}')

def liq_chart(rows):
    """rows: [[dd/mm, khớp lệnh, thỏa thuận]] tỷ đồng — cột chồng + đường trung bình."""
    if not rows: return ""
    W, H, L, R, T, B = 972, 235, 66, 14, 32, 34
    tot = [a + b for _, a, b in rows]; mx = max(tot) * 1.12
    avg = sum(tot) / len(tot)
    Y = lambda v: T + (H - T - B) * (1 - v / mx)
    n = len(rows); step = (W - L - R) / n; bw = step * .62
    g = ""
    for k in range(4):
        v = mx * k / 3
        g += (f'<line x1="{L}" x2="{W-R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="#E6E3D8"/>'
              f'<text x="{L-8}" y="{Y(v)+6:.1f}" font-size="17" text-anchor="end" fill="#6F6E68">{vn(v / 1000, 0)}k</text>')
    bars_ = ""
    for i, (dt, a, b) in enumerate(rows):
        x = L + step * i + (step - bw) / 2
        bars_ += (f'<rect x="{x:.1f}" y="{Y(a):.1f}" width="{bw:.1f}" height="{Y(0)-Y(a):.1f}" fill="{NAVY}"/>'
                  f'<rect x="{x:.1f}" y="{Y(a+b):.1f}" width="{bw:.1f}" height="{Y(a)-Y(a+b):.1f}" fill="{GOLD}"/>'
                  f'<text x="{x+bw/2:.1f}" y="{Y(a+b)-8:.1f}" font-size="17" font-weight="700" text-anchor="middle" fill="#141413" stroke="#fff" stroke-width="5" paint-order="stroke">{vn(a+b)}</text>'
                  f'<text x="{x+bw/2:.1f}" y="{H-10}" font-size="17" text-anchor="middle" fill="#6F6E68">{esc(dt)}</text>')
    ay = Y(avg)
    ref = f'<line x1="{L}" x2="{W-R}" y1="{ay:.1f}" y2="{ay:.1f}" stroke="#141413" stroke-dasharray="6 5" stroke-width="1.5"/>'
    return svg_wrap(W, H, g + bars_ + ref)

def flow5_chart(title, rows):
    """rows: [[dd/mm, ròng tỷ đồng]] — cột xanh mua ròng / đỏ bán ròng."""
    if not rows: return ""
    W, H, L, R, T, B = 470, 200, 12, 12, 30, 32
    mx = max(abs(v) for _, v in rows) * 1.25 or 1
    zero = T + (H - T - B) / 2; half = (H - T - B) / 2
    n = len(rows); step = (W - L - R) / n; bw = step * .56
    out = f'<line x1="{L}" x2="{W-R}" y1="{zero}" y2="{zero}" stroke="#B8B6AC"/>'
    for i, (dt, v) in enumerate(rows):
        x = L + step * i + (step - bw) / 2; h = abs(v) / mx * half
        y = zero - h if v >= 0 else zero
        col = GREEN if v >= 0 else RED
        ty = y - 7 if v >= 0 else y + h + 19
        out += (f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{h:.1f}" fill="{col}"/>'
                f'<text x="{x+bw/2:.1f}" y="{ty:.1f}" font-size="17" font-weight="700" text-anchor="middle" fill="#141413">{vn(v, 0, True)}</text>'
                f'<text x="{x+bw/2:.1f}" y="{H-9}" font-size="16" text-anchor="middle" fill="#6F6E68">{esc(dt)}</text>')
    tot = sum(v for _, v in rows)
    head = f'<div class="h5">{title} <span class="{"pos" if tot >= 0 else "neg"}">{vn(tot, 0, True)} tỷ / {len(rows)} phiên</span></div>'
    return f'<div class="card fl">{head}<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="Inter,sans-serif">{out}</svg></div>'

def sig(pct, klx, given=None):
    if given: return given
    kl = "KL cao" if klx >= 1.5 else ("KL thấp" if klx < 0.8 else "")
    return ("Giá tăng" if pct > 0 else "Giá giảm") + (f", {kl}" if kl else "")

def notable_table(title, rows, up):
    col = GREEN if up else RED
    body = ""
    for r in rows:
        sym, price, pct, gt, klx = r[:5]
        tin = sig(pct, klx, r[5] if len(r) > 5 else None)
        body += (f'<tr><td class="sy">{esc(sym)}</td><td>{vn(price, 2)}</td><td class="{"pos" if pct >= 0 else "neg"}">{vn(pct, 2, True)}%</td>'
                 f'<td>{vn(gt, 0)}</td><td>{vn(klx, 2)}x</td><td class="sg">{esc(tin)}</td></tr>')
    return (f'<div class="card nt"><div class="nh" style="background:{col}">{title}</div><table>'
            f'<tr><th>Mã</th><th>Giá</th><th>% giá</th><th>GT khớp</th><th>KL/TB20</th><th>Tín hiệu</th></tr>{body}</table></div>')

def page_cuoi2(d):
    parts = []; n = 0
    def sec(title, html):
        nonlocal n
        n += 1; parts.append(f'<h2><span class="no">{n:02d}</span> {title}</h2>{html}')
    h = d.get("hist10") or []
    if len(h) >= 2:
        chg = h[-1][1] - h[0][1]; pct = chg / h[0][1] * 100
        sec(f"VN-Index {len(h)} phiên gần nhất", f'<p class="cap">Từ {esc(h[0][0])} đến {esc(h[-1][0])}: <b class="{"pos" if chg >= 0 else "neg"}">{vn(chg, 2, True)} điểm ({vn(pct, 2, True)}%)</b></p>' + hist_chart(h))
    lq = d.get("liq10") or []
    if lq:
        tot = [a + b for _, a, b in lq]; avg = sum(tot) / len(tot); last = tot[-1]
        sec(f"Thanh khoản {len(lq)} phiên (tỷ đồng)",
            f'<p class="cap">Phiên cuối <b>{vn(last)}</b> tỷ, <b class="{"pos" if last >= avg else "neg"}">{vn((last-avg)/avg*100, 1, True)}%</b> so với trung bình {len(lq)} phiên ({vn(avg)} tỷ). <span class="lg"><i style="background:{NAVY}"></i>Khớp lệnh <i style="background:{GOLD}"></i>Thỏa thuận</span></p>' + liq_chart(lq))
    f5, p5 = d.get("foreign5") or [], d.get("prop5") or []
    if f5 or p5:
        sec("Dòng tiền 5 phiên (tỷ đồng, ròng)", f'<div class="grid g2">{flow5_chart("Khối ngoại", f5)}{flow5_chart("Tự doanh", p5)}</div>')
    nt = d.get("notable") or {}
    if nt.get("up") or nt.get("down"):
        sec("Cổ phiếu đáng chú ý (GT khớp: tỷ đồng)", f'{notable_table("5 mã tăng nổi bật", nt.get("up", [])[:5], True)}<div style="height:10px"></div>{notable_table("5 mã giảm nổi bật", nt.get("down", [])[:5], False)}')
    return "".join(parts)

CSS_P2 = """
.cap{font-size:20px;margin:2px 0 8px;color:#3b3a36} .cap b{font-weight:700}
.lg{float:right;font-size:17px} .lg i{display:inline-block;width:13px;height:13px;margin:0 5px 0 12px;vertical-align:-1px}
.h5{font-size:21px;font-weight:700;padding:2px 4px 4px} .h5 span{font-weight:700;font-size:19px}
.card.fl svg{width:100%;height:auto;display:block}
.nt{padding:0;overflow:hidden;flex-shrink:0} .nt .nh{color:#fff;font-weight:700;font-size:21px;padding:7px 14px}
.nt table{width:100%;border-collapse:collapse;font-size:19px} .nt th{font-size:16px;color:#6F6E68;font-weight:600;text-align:right;padding:5px 8px;background:#F4F2EA}
.nt td{text-align:right;padding:5px 8px;border-top:1px solid #ECE9DF;font-variant-numeric:tabular-nums} .nt th:first-child,.nt td.sy{text-align:left;font-weight:700}
.nt td.sg{font-size:16px;text-align:right;color:#3b3a36} .nt .pos{color:#2F7D4F;font-weight:700} .nt .neg{color:#B8432F;font-weight:700}
"""

def shell(d, body, k, title=None):
    mode = d["mode"]
    return f"""<!doctype html><html lang="vi"><head><meta charset="utf-8"><style>{CSS}</style>
<style>{CSS_M}</style><style>{CSS_P}</style><style>{CSS_P2}</style></head>
<body><div class="page" style="--k:{k}">
<div class="top"><img src="data:image/png;base64,{LOGO}" alt="Weha"><div class="ed"><b class="bs">{title or TITLE[mode]}</b>{esc(d["date_label"])}</div></div>
{body}
<div class="spacer"></div>
<div class="foot"><div class="who"><b>Nguyễn Hoài</b><br>Weha · 0396 336 096</div>
<div class="disc">Số liệu mang tính tham khảo, không phải khuyến nghị mua/bán.<br>Nhà đầu tư tự chịu trách nhiệm với quyết định của mình.</div></div>
</div></body></html>"""

async def render(d, out, page=1):
    from playwright.async_api import async_playwright
    fn = page_giua if d["mode"] == "giua" else (page_cuoi if page == 1 else page_cuoi2)
    ttl = TITLE[d["mode"]] if page == 1 else "DIỄN BIẾN 10 PHIÊN"
    base = os.path.join(out, f"Weha_{NAME[d['mode']]}{'' if page == 1 else '2'}_{d['file_date']}")
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=2.3)
        async def draw(k):
            open(base + ".html", "w", encoding="utf-8").write(shell(d, fn(d), k, ttl))
            await pg.goto("file://" + os.path.abspath(base + ".html")); await pg.wait_for_timeout(250)
            return await pg.evaluate("document.querySelector('.page').scrollHeight")
        k = 1.0
        while True:
            h = await draw(k)
            if h <= 1920 or k <= 0.8: break
            k = round(k - 0.03, 2)
        if h > 1920: print(f"CẢNH BÁO: ảnh vẫn tràn ({h}px) — hãy bớt 1-2 dòng")
        await (await pg.query_selector(".page")).screenshot(path=base + ".png")
        print(f"chiều cao {h}px, hệ số chữ {k}")
        await b.close()
    return base + ".png"

if __name__ == "__main__":
    d = json.load(open(sys.argv[1], encoding="utf-8"))
    out = sys.argv[2] if len(sys.argv) > 2 else "."
    os.makedirs(out, exist_ok=True)
    print(asyncio.run(render(d, out)))
    if d["mode"] == "cuoi" and any(d.get(x) for x in ("hist10", "liq10", "foreign5", "prop5", "notable")):
        print(asyncio.run(render(d, out, 2)))
