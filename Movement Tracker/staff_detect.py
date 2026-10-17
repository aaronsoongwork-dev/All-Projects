#!/usr/bin/env python3
"""Staff presence + XY localisation in an overhead fisheye clip (colour-agnostic).
Usage: python staff_detect.py input.mp4 [out_dir]
Outputs: staff_frames.csv (frame,time_s,staff_present,x,y,source), staff_annotated.mp4,
         timeline.png, trajectory.jpg

Pipeline
 1. Moving-object mask: 3-frame differencing (current vs t-K and t+K, both must change)
    AND difference from a median background. Works for any clothing colour.
 2. Blobs (person-sized) -> short tracklets (nearest neighbour, strict jump limit).
 3. Seed = the tracklet with the longest walked path (the sustained walker).
 4. Chain: link tracklets backwards/forwards from the seed when the next one starts
    close in space and time. This follows ONE person through clothing/colour changes
    (e.g. light shirt -> dark coat) because it uses position continuity, not colour.
 5. Gaps between linked tracklets are filled by linear interpolation (flagged 'interp').
"""
import cv2, numpy as np, sys, os, csv

W, H = 480, 360
K = 4
MOTION_T = 22
BG_T = 30
MIN_A, MAX_A = 350, 9000
MAX_JUMP = 25
MAX_GAP = 25
MIN_FRAMES, MIN_PATH = 12, 60
LINK_DIST = 90
LINK_TIME = 8.0

def load(path):
    cap = cv2.VideoCapture(path); fps = cap.get(cv2.CAP_PROP_FPS) or 25
    small = []; size = None
    while True:
        ok, f = cap.read()
        if not ok: break
        if size is None: size = (f.shape[1], f.shape[0])
        small.append(cv2.resize(f, (W, H), interpolation=cv2.INTER_AREA))
    return small, fps, size

def blobs(small):
    g = [cv2.GaussianBlur(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), (5, 5), 0).astype(np.int16) for f in small]
    bg = cv2.GaussianBlur(np.median(np.stack(small[::5]), axis=0).astype(np.uint8), (5, 5), 0)
    close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)); out = []
    for i, f in enumerate(small):
        a, b = g[max(0, i - K)], g[min(len(g) - 1, i + K)]
        mot = (np.abs(g[i] - a) > MOTION_T) & (np.abs(g[i] - b) > MOTION_T)
        fg = cv2.absdiff(cv2.GaussianBlur(f, (5, 5), 0), bg).max(axis=2) > BG_T
        m = (mot & fg).astype(np.uint8) * 255
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, close)
        n, _, st, c = cv2.connectedComponentsWithStats(m)
        out.append([(c[k], st[k, :4], st[k, 4]) for k in range(1, n) if MIN_A <= st[k, 4] <= MAX_A])
    return out

def track(bl):
    tracks = []
    for i, bs in enumerate(bl):
        used = set()
        for t in tracks:
            if i - t['last'] > MAX_GAP: continue
            lx, ly = t['pts'][t['last']][:2]
            best, bd = None, MAX_JUMP * (1 + 0.5 * (i - t['last'] - 1) / max(1, MAX_GAP))
            for j, (c, b, a) in enumerate(bs):
                if j in used: continue
                d = np.hypot(c[0] - lx, c[1] - ly)
                if d < bd: best, bd = j, d
            if best is not None:
                c, b, a = bs[best]; t['pts'][i] = (c[0], c[1], tuple(b)); t['last'] = i; used.add(best)
        for j, (c, b, a) in enumerate(bs):
            if j not in used: tracks.append({'pts': {i: (c[0], c[1], tuple(b))}, 'last': i})
    return tracks

def stats(t):
    fr = sorted(t['pts']); xy = np.array([t['pts'][f][:2] for f in fr])
    path = float(np.hypot(*np.diff(xy, axis=0).T).sum()) if len(fr) > 1 else 0.0
    return fr[0], fr[-1], xy[0], xy[-1], len(fr), path

def chain(tracks, fps):
    cand = [t for t in tracks if stats(t)[4] >= MIN_FRAMES and stats(t)[5] >= MIN_PATH]
    if not cand: return []
    seed = max(cand, key=lambda t: stats(t)[5])
    ch = [seed]; used = {id(seed)}
    for direction in (+1, -1):
        cur = seed
        while True:
            s0, s1, p0, p1, _, _ = stats(cur)
            best, bs = None, 1e9
            for t in cand:
                if id(t) in used: continue
                t0, t1, q0, q1, _, _ = stats(t)
                if direction > 0: gap = (t0 - s1) / fps; d = np.hypot(*(q0 - p1))
                else:             gap = (s0 - t1) / fps; d = np.hypot(*(q1 - p0))
                if gap < -0.3 or gap > LINK_TIME or d > LINK_DIST: continue
                score = d + 20 * max(gap, 0)
                if score < bs: best, bs = t, score
            if best is None: break
            ch.append(best); used.add(id(best)); cur = best
    ch.sort(key=lambda t: stats(t)[0])
    return ch

def main(path, out='out'):
    os.makedirs(out, exist_ok=True)
    small, fps, (FW, FH) = load(path); n = len(small); sx, sy = FW / W, FH / H
    ch = chain(track(blobs(small)), fps)
    pos = {}; src = {}
    for t in ch:
        for f, (x, y, b) in t['pts'].items(): pos[f] = (x, y, b); src[f] = 'tracked'
    fs = sorted(pos)
    for fa, fb in zip(fs[:-1], fs[1:]):
        if fb - fa > 1:
            xa, ya, ba = pos[fa]; xb, yb, bb = pos[fb]
            for f in range(fa + 1, fb):
                u = (f - fa) / (fb - fa)
                bx = tuple(int(ba[k] * (1 - u) + bb[k] * u) for k in range(4))
                pos[f] = (xa * (1 - u) + xb * u, ya * (1 - u) + yb * u, bx); src[f] = 'interp'
    present = np.zeros(n, bool)
    for f in pos: present[f] = True
    with open(os.path.join(out, 'staff_frames.csv'), 'w', newline='') as fh:
        w = csv.writer(fh); w.writerow(['frame', 'time_s', 'staff_present', 'x', 'y', 'source'])
        for i in range(n):
            if i in pos: w.writerow([i, round(i / fps, 2), 1, round(pos[i][0] * sx), round(pos[i][1] * sy), src[i]])
            else: w.writerow([i, round(i / fps, 2), 0, '', '', ''])
    vw = cv2.VideoWriter(os.path.join(out, 'staff_annotated.mp4'), cv2.VideoWriter_fourcc(*'mp4v'), fps, (FW, FH))
    cap = cv2.VideoCapture(path); trail = []
    for i in range(n):
        ok, f = cap.read()
        if not ok: break
        if i in pos:
            x, y, b = pos[i]; X, Y = int(x * sx), int(y * sy)
            if trail and np.hypot(X - trail[-1][0], Y - trail[-1][1]) > 90: trail = []
            trail.append((X, Y)); col = (0, 255, 0) if src[i] == 'tracked' else (0, 200, 255)
            cv2.rectangle(f, (int(b[0] * sx), int(b[1] * sy)), (int((b[0] + b[2]) * sx), int((b[1] + b[3]) * sy)), col, 2)
            cv2.circle(f, (X, Y), 5, (0, 0, 255), -1)
        for a, b2 in zip(trail[-60:-1], trail[-59:]): cv2.line(f, a, b2, (0, 255, 255), 2)
        lab = ('STAFF (tracked)' if src.get(i) == 'tracked' else 'STAFF (est.)') if i in pos else 'no staff'
        cv2.putText(f, f"f{i} t={i/fps:.1f}s {lab}", (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                    (0, 255, 0) if i in pos else (0, 0, 255), 2)
        vw.write(f)
    vw.release()
    segs = []; s = None
    for i, v in enumerate(present):
        if v and s is None: s = i
        if not v and s is not None: segs.append((s, i - 1)); s = None
    if s is not None: segs.append((s, n - 1))
    print("Staff present segments (frames / seconds):")
    for a, b in segs: print(f"  {a}-{b}  ({a/fps:.1f}s - {b/fps:.1f}s)")
    print(f"Linked tracklets: {len(ch)}; estimated (interpolated) frames: {sum(v == 'interp' for v in src.values())}")
    tl = np.full((60, n), 255, np.uint8); tl[:, present] = 60
    for i, v in src.items():
        if v == 'interp': tl[:, i] = 150
    cv2.imwrite(os.path.join(out, 'timeline.png'), cv2.resize(tl, (1200, 60), interpolation=cv2.INTER_NEAREST))
    cap = cv2.VideoCapture(path); ok, vis = cap.read()
    for i, (x, y, b) in pos.items():
        col = tuple(int(c) for c in cv2.applyColorMap(np.uint8([[255 * i // n]]), cv2.COLORMAP_JET)[0, 0])
        cv2.circle(vis, (int(x * sx), int(y * sy)), 3, col, -1)
    cv2.imwrite(os.path.join(out, 'trajectory.jpg'), vis)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'out')