# -*- coding: utf-8 -*-
import html, math, sys
E = html.escape
COL = dict(data='#1f3a68', ctrl='#c55a11', haz='#c00000', fwd='#2e7d32', idx='#7030a0', const='#444')
WID = dict(data=1.6, ctrl=1.2, haz=1.3, fwd=1.4, idx=1.4, const=1.0)
DASH = dict(haz='7 3', fwd='7 3')
FILL = dict(blk=('#eaf2fb', '#c5daf1', '#2f5597'), rf=('#eaf2fb', '#bcd4ef', '#2f5597'), ctrl=('#fff1e3', '#f8cfa6', '#c55a11'),
            haz=('#fdecec', '#f4c2c2', '#c00000'), fwd=('#eaf6ea', '#c3e3c4', '#2e7d32'), bru=('#fff1e3', '#f8cfa6', '#c55a11'),
            mux=('#fffbe6', '#ffe699', '#9c7a00'), alu=('#eef7e8', '#cfe6bd', '#4e7a2a'), adder=('#eef7e8', '#cfe6bd', '#4e7a2a'),
            reg=('#f1ecf8', '#d6c8ec', '#5b3f8c'), preg=('#f3f0fa', '#dcd3ef', '#5b3f8c'))

def segs(w):
    p = w['pts']
    return [(p[i], p[i + 1]) for i in range(len(p) - 1)]

def is_h(s): return abs(s[0][1] - s[1][1]) < 0.01
def is_v(s): return abs(s[0][0] - s[1][0]) < 0.01
def rng(a, b): return (min(a, b), max(a, b))

def label_box(t, size, x, y, anchor):
    wdt = 0
    for ch in t:
        wdt += size * (1.0 if ord(ch) > 0x2e80 else 0.56)
    if anchor == 'middle': x0 = x - wdt / 2
    elif anchor == 'end': x0 = x - wdt
    else: x0 = x
    return (x0, y - size * 0.8, x0 + wdt, y + size * 0.25)

def box_ov(a, b, m=0):
    return a[0] < b[2] + m and b[0] < a[2] + m and a[1] < b[3] + m and b[1] < a[3] + m

def comp_rect(c):
    return (c['x'], c['y'], c['x'] + c['w'], c['y'] + c['h'])

def run(comps, wires, texts, G):
    errs, warns = [], []
    # ---------- 1. component overlap
    for i in range(len(comps)):
        for j in range(i + 1, len(comps)):
            if box_ov(comp_rect(comps[i]), comp_rect(comps[j]), 6):
                errs.append('BOX OVERLAP/too close: %s <-> %s' % (comps[i]['id'], comps[j]['id']))
    # ---------- 2. segment through component
    for w in wires:
        for s in segs(w):
            (x1, y1), (x2, y2) = s
            for c in comps:
                l, t, r, b = comp_rect(c)
                if c['kind'] == 'mux': t += 7; b -= 7   # slanted edges
                if c['kind'] in ('alu', 'adder'): t += c['h']*0.13; b -= c['h']*0.13
                if is_h(s):
                    a, bb = rng(x1, x2)
                    if t + 1 < y1 < b - 1 and a < r - 1 and bb > l + 1:
                        errs.append('WIRE THROUGH BOX: %s seg %s crosses %s' % (w['net'], s, c['id']))
                else:
                    a, bb = rng(y1, y2)
                    if l + 1 < x1 < r - 1 and a < b - 1 and bb > t + 1:
                        errs.append('WIRE THROUGH BOX: %s seg %s crosses %s' % (w['net'], s, c['id']))
    # ---------- 3/4/5/6 wire-wire
    allsegs = [(w['net'], s, w) for w in wires for s in segs(w)]
    hops = []
    ncross = 0
    for i in range(len(allsegs)):
        for j in range(i + 1, len(allsegs)):
            n1, s1, w1 = allsegs[i]; n2, s2, w2 = allsegs[j]
            same = n1 == n2
            if is_h(s1) and is_h(s2) or is_v(s1) and is_v(s2):
                k = 1 if is_h(s1) else 0      # coordinate that's constant
                o = 0 if is_h(s1) else 1
                d = abs(s1[0][k] - s2[0][k])
                a1, b1 = rng(s1[0][o], s1[1][o]); a2, b2 = rng(s2[0][o], s2[1][o])
                ov = min(b1, b2) - max(a1, a2)
                if not same and d < 0.5 and ov > -0.5:
                    errs.append('COLLINEAR TOUCH/OVERLAP: %s %s  <->  %s %s' % (n1, s1, n2, s2))
                elif not same and d < 8 and ov > 4:
                    warns.append('near-parallel (%.0fpx, len %.0f): %s %s <-> %s %s' % (d, ov, n1, s1, n2, s2))
                continue
            h, v = (s1, s2) if is_h(s1) else (s2, s1)
            hn, vn = (n1, n2) if is_h(s1) else (n2, n1)
            y = h[0][1]; x = v[0][0]
            hx1, hx2 = rng(h[0][0], h[1][0]); vy1, vy2 = rng(v[0][1], v[1][1])
            if hx1 - 0.01 <= x <= hx2 + 0.01 and vy1 - 0.01 <= y <= vy2 + 0.01:
                interior_h = hx1 + 0.01 < x < hx2 - 0.01
                interior_v = vy1 + 0.01 < y < vy2 - 0.01
                if same:
                    if interior_h and interior_v:
                        warns.append('same-net crossing: %s at (%s,%s)' % (hn, x, y))
                    continue
                if interior_h and interior_v:
                    ncross += 1
                    hops.append((h, x))
                    if min(x - hx1, hx2 - x) < 9 or min(y - vy1, vy2 - y) < 9:
                        warns.append('crossing near a corner/end (%s x %s) at (%s,%s)' % (hn, vn, x, y))
                else:
                    errs.append('T-TOUCH between different nets: %s / %s at (%s,%s)' % (hn, vn, x, y))
    # ---------- 7. labels
    lbls = []
    for w in wires:
        if w['label']:
            lbls.append((w['net'], label_box(w['label'], 10, w['lp'][0], w['lp'][1], w['anchor']), w['label']))
    for t in texts:
        if t.get('chk', True) and t['y'] < 1080:
            lbls.append(('#text', label_box(t['s'], t['size'], t['x'], t['y'], t['anchor']), t['s']))
    for i in range(len(lbls)):
        for j in range(i + 1, len(lbls)):
            if box_ov(lbls[i][1], lbls[j][1], 1):
                errs.append('LABEL OVERLAP: "%s" <-> "%s"' % (lbls[i][2], lbls[j][2]))
        for c in comps:
            if c['kind'] == 'preg' or True:
                if box_ov(lbls[i][1], comp_rect(c), 0):
                    errs.append('LABEL ON BOX: "%s" on %s' % (lbls[i][2], c['id']))
        for n, s, w in allsegs:
            if n == lbls[i][0]: continue
            (x1, y1), (x2, y2) = s
            bx = lbls[i][1]
            sb = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
            if box_ov(bx, sb, 0):
                errs.append('LABEL ON LINE: "%s" over %s %s' % (lbls[i][2], n, s))
    print('components:', len(comps), ' wires:', len(wires), ' crossings(hops):', ncross)
    for e in errs: print('ERR ', e)
    for w_ in warns: print('warn', w_)
    G['_hops'] = hops
    write_svg(comps, wires, texts, G, hops)

# ------------------------------------------------------------------ SVG
def path_with_hops(w, hops, r=5):
    pts = w['pts']
    d = 'M%.1f,%.1f' % pts[0]
    for s in segs(w):
        (x1, y1), (x2, y2) = s
        if is_h(s) and w['kind'] != 'const':
            xs = sorted([hx for (hs, hx) in hops if hs is s or (hs[0] == s[0] and hs[1] == s[1])], reverse=(x2 < x1))
            dirn = 1 if x2 > x1 else -1
            for hx in xs:
                d += ' L%.1f,%.1f A%d,%d 0 0 %d %.1f,%.1f' % (hx - r * dirn, y1, r, r, 1 if dirn > 0 else 0, hx + r * dirn, y1)
        d += ' L%.1f,%.1f' % (x2, y2)
    return d

def shape(c):
    x, y, w, h = c['x'], c['y'], c['w'], c['h']
    k = c['kind']
    f1, f2, st = FILL.get(c['style'], FILL['blk'])
    grad = 'g_' + c['style']
    common = 'fill="url(#%s)" stroke="%s" stroke-width="1.4" filter="url(#sh)"' % (grad, st)
    o = []
    if k == 'mux':
        o.append('<polygon points="%g,%g %g,%g %g,%g %g,%g" %s/>' % (x, y, x + w, y + 10, x + w, y + h - 10, x, y + h, common))
    elif k in ('alu', 'adder'):
        pts = [(x, y), (x + w, y + h * .25), (x + w, y + h * .75), (x, y + h), (x, y + h * .58), (x + w * .28, y + h * .5), (x, y + h * .42)]
        o.append('<polygon points="%s" %s/>' % (' '.join('%g,%g' % p for p in pts), common))
    else:
        rx = 3 if k != 'preg' else 2
        o.append('<rect x="%g" y="%g" width="%g" height="%g" rx="%d" %s/>' % (x, y, w, h, rx, common))
    return o

def write_svg(comps, wires, texts, G, hops):
    W, H = G['W'], G['H']
    o = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" font-family="Segoe UI, Microsoft YaHei, PingFang SC, Noto Sans CJK SC, Arial, sans-serif">' % (W, H, W, H)]
    o.append('<defs>')
    o.append('<pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse"><path d="M20,0 L0,0 0,20" fill="none" stroke="#e9eef5" stroke-width="0.8"/></pattern>')
    o.append('<filter id="sh" x="-10%" y="-10%" width="130%" height="130%"><feDropShadow dx="2.5" dy="2.5" stdDeviation="1.6" flood-color="#000" flood-opacity="0.22"/></filter>')
    for key, (f1, f2, st) in FILL.items():
        vert = 'x2="1" y2="0"' if key == 'preg' else 'x2="0" y2="1"'
        o.append('<linearGradient id="g_%s" x1="0" y1="0" %s><stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s"/></linearGradient>' % (key, vert, f1, f2))
    for k, c in COL.items():
        o.append('<marker id="ar_%s" viewBox="0 0 10 10" refX="9.5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse" markerUnits="userSpaceOnUse"><path d="M0,1 L10,5 L0,9 z" fill="%s"/></marker>' % (k, c))
    o.append('</defs>')
    o.append('<rect width="%d" height="%d" fill="#ffffff"/><rect width="%d" height="%d" fill="url(#grid)"/>' % (W, H, W, H))
    # title
    o.append('<text x="30" y="36" font-size="24" font-weight="bold" fill="#1f3864">RV32I 五级流水线 CPU 微架构框图</text>')
    o.append('<text x="430" y="36" font-size="13" fill="#555">IF / ID / EX / MEM / WB · 全前递 (EX/MEM, MEM/WB → EX) · load-use 停顿 1 拍 · 分支/跳转在 EX 解析 (预测不跳转, 冲刷 2 条) · 寄存器堆写优先旁路</text>')
    # stage zones
    for name, x0, x1, col in G['ST']:
        o.append('<rect x="%d" y="62" width="%d" height="1010" fill="%s" fill-opacity="0.28" stroke="%s" stroke-opacity="0.9" stroke-dasharray="4 3"/>' % (x0, x1 - x0, col, '#9fb3c8'))
        o.append('<rect x="%d" y="62" width="%d" height="24" fill="%s"/>' % (x0, x1 - x0, col))
        o.append('<text x="%d" y="79" font-size="14" font-weight="bold" fill="#1f3864" text-anchor="middle">%s</text>' % ((x0 + x1) / 2, E(name)))
    # components
    for c in comps:
        o += shape(c)
        x, y, w, h = c['x'], c['y'], c['w'], c['h']
        if c['kind'] == 'preg':
            o.append('<text x="%g" y="%g" font-size="13" font-weight="bold" fill="#5b3f8c" text-anchor="middle">%s</text>' % (x + w / 2, y + h + 18, E(c['title'])))
            for f, fy in G['PFIELDS'][c['title']]:
                o.append('<text x="%g" y="%g" font-size="9.5" fill="#3b2a5c" text-anchor="middle">%s</text>' % (x + w / 2, fy + 3.5, E(f)))
                o.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#b6a7d6" stroke-width="0.6"/>' % (x + 3, fy + 8, x + w - 3, fy + 8))
            # clock
            o.append('<polyline points="%g,%g %g,%g %g,%g" fill="none" stroke="#5b3f8c" stroke-width="1.2"/>' % (x + w / 2 - 7, y + h, x + w / 2, y + h - 9, x + w / 2 + 7, y + h))
            continue
        if c['kind'] == 'mux':
            o.append('<text x="%g" y="%g" font-size="11" font-weight="bold" fill="#7a5f00" text-anchor="middle">%s</text>' % (x + w / 2 + 2, y + h / 2 + 4, 'MUX' if h >= 100 else ''))
        elif c['kind'] in ('alu', 'adder'):
            o.append('<text x="%g" y="%g" font-size="%d" font-weight="bold" fill="#35541c" text-anchor="middle">%s</text>' % (x + w * .64, y + h / 2 + 5, c['tsize'] if c['kind'] == 'alu' else 13, E(c['title'])))
        elif c['kind'] != 'reg':
            ty = y + h / 2 + (0 if c['sub'] else 4); cx = x + w / 2
            if c['id'] in ('ctrl', 'rf', 'dmem', 'imem'): ty = y + 22 if c['id'] != 'imem' else y + 60
            if c['id'] in ('dmem',): ty = y + 60
            if c['id'] in ('haz',): ty = y + 30; cx = x + 120
            if c['id'] in ('fwd',): ty = y + 34
            if c['id'] == 'aludec': ty = y + 24; cx = x + 88
            if c['id'] == 'bru': ty = y + 27
            o.append('<text x="%g" y="%g" font-size="%d" font-weight="bold" fill="#1f3864" text-anchor="middle">%s</text>' % (cx if c['id'] != 'ctrl' else x + 62, ty, c['tsize'], E(c['title'])))
            if c['sub']:
                o.append('<text x="%g" y="%g" font-size="10" fill="#444" text-anchor="middle">%s</text>' % (cx if c['id'] != 'ctrl' else x + 62, ty + 14, E(c['sub'])))
        if c['kind'] == 'reg':
            o.append('<polyline points="%g,%g %g,%g %g,%g" fill="none" stroke="#5b3f8c" stroke-width="1.2"/>' % (x + w / 2 - 7, y + h, x + w / 2, y + h - 9, x + w / 2 + 7, y + h))
            o.append('<text x="%g" y="%g" font-size="13" font-weight="bold" fill="#3b2a5c" text-anchor="middle">%s</text>' % (x + w / 2, y + 26, E(c['title'])))
            o.append('<text x="%g" y="%g" font-size="9.5" fill="#444" text-anchor="middle">%s</text>' % (x + w / 2, y + 40, E(c['sub'])))
        # port labels
        for side, pos, lab in c['ports']:
            if not lab: continue
            fs = 9.5
            col = '#333'
            if side == 'L': o.append('<text x="%g" y="%g" font-size="%g" fill="%s">%s</text>' % (x + (4 if c['kind'] != 'mux' else 3), pos + 3.5, fs, col, E(lab)))
            if side == 'R': o.append('<text x="%g" y="%g" font-size="%g" fill="%s" text-anchor="end">%s</text>' % (x + w - 4, pos + 3.5, fs, col, E(lab)))
            if side == 'T': o.append('<text x="%g" y="%g" font-size="%g" fill="%s" text-anchor="middle">%s</text>' % (pos, y + 12, fs, col, E(lab)))
            if side == 'B': o.append('<text x="%g" y="%g" font-size="%g" fill="%s" text-anchor="middle">%s</text>' % (pos, y + h - 4, fs, col, E(lab)))
    # extra component inner texts
    for t in G.get('INNER', []):
        o.append('<text x="%g" y="%g" font-size="%g" fill="%s" text-anchor="%s">%s</text>' % (t[0], t[1], t[2], t[4], t[5], E(t[3])))
    # wires
    for w in wires:
        k = w['kind']
        d = path_with_hops(w, hops)
        dash = ' stroke-dasharray="%s"' % DASH[k] if k in DASH else ''
        mk = ' marker-end="url(#ar_%s)"' % k if w['arrow'] and k != 'const' else ''
        o.append('<path d="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linejoin="round"%s%s/>' % (d, COL[k], WID[k], dash, mk))
    # junction dots
    for i, w in enumerate(wires):
        p0 = w['pts'][0]
        for j in range(i):
            v = wires[j]
            if v['net'] != w['net'] or v['pts'][0] == p0: continue
            hit = False
            for s in segs(v):
                (x1, y1), (x2, y2) = s
                if min(x1, x2) - .01 <= p0[0] <= max(x1, x2) + .01 and min(y1, y2) - .01 <= p0[1] <= max(y1, y2) + .01:
                    hit = True
            if hit:
                o.append('<circle cx="%g" cy="%g" r="3.3" fill="%s"/>' % (p0[0], p0[1], COL[w['kind']]))
                break
    # wire labels
    for w in wires:
        if not w['label']: continue
        c = COL[w['kind']]
        o.append('<text x="%g" y="%g" font-size="10" fill="%s" text-anchor="%s" stroke="#fff" stroke-width="3" paint-order="stroke" stroke-opacity="0.9">%s</text>' % (w['lp'][0], w['lp'][1], c, w['anchor'], E(w['label'])))
    for t in texts:
        o.append('<text x="%g" y="%g" font-size="%g" fill="%s" text-anchor="%s" font-weight="%s"%s%s>%s</text>' % (
            t['x'], t['y'], t['size'], t['color'], t['anchor'], t['weight'], ' font-style="italic"' if t['italic'] else '',
            ' font-family="%s"' % t['family'] if t['family'] else '', E(t['s'])))
    for extra in G.get('EXTRA', []):
        o.append(extra)
    o.append('</svg>')
    open(G.get('OUT', 'riscv-5stage-pipeline.svg'), 'w').write('\n'.join(o))
