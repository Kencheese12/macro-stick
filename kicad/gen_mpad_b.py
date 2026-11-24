# File: gen_mpad_b.py
"""縦長BTマクロパッド B案：部品配置済み・未配線の基板を生成する（段階4 改訂）

B案: XIAO を CKW12 の真下・メイン基板の裏面に、ピンヘッダで吊り下げる（部品面を上向き）

実行環境: KiCad 10.0.x 同梱 Python（SWIG版 pcbnew）
互換対応（Linux AppImage で報告のあった3点）:
  (1) BOARD() を優先し、失敗時のみ CreateEmptyBoard() を使う
  (2) 基板厚の設定に失敗しても続行する
  (3) Footprint.Remove() を使わない（CKW12 の MP 削除はテキスト加工で行う）
"""

import math
import os
import re
import sys

import pcbnew

# ------------------------------------------------------------ パス
HERE = os.path.dirname(os.path.abspath(__file__))
LIB_MPAD = os.path.join(HERE, "lib", "mpad.pretty")
LIB_SEEED = os.path.join(HERE, "lib", "Seeed_XIAO.pretty")
OUT_DIR = os.path.join(HERE, "out")
OUT_PCB = os.path.join(OUT_DIR, "mpad_b.kicad_pcb")

FP_XIAO = "XIAO_nRF52840_DIP_Back"
FP_ENC_SRC = "RotaryEncoder_EC12_CKW12"
FP_ENC = "RotaryEncoder_CKW12_noMP"
FP_SW = "SW_MX_HS_Kailh_1U_Back"
SEEED_DIP = "XIAO-nRF52840-DIP"

# ------------------------------------------------------------ 寸法（KiCad座標, mm, Yは下向き）
ORIGIN_X = 100.0
ORIGIN_Y = 100.0
BOARD_W = 19.0
BOARD_L = 101.9
CORNER_R = 1.0
CX = ORIGIN_X + BOARD_W / 2.0
CASE_OFFSET = ORIGIN_Y - 2.3          # KiCad Y = 筐体 y + 97.7


def case_y(y):
    return y + CASE_OFFSET


XIAO_POS = (CX, case_y(12.8))
XIAO_L = 21.0
XIAO_ROW = 15.24
XIAO_SPAN = 2.54 * 6
USB_PROTRUDE = 1.0
USB_DEPTH = 7.35
USB_W = 8.94

ENC_POS = (CX, case_y(18.0))
KEY_Y = tuple(case_y(18.0 + 19.05 * i) for i in range(1, 5))
MP_X = 5.6

ANT_KO_INTO_XIAO = 4.0
ANT_KO_GAP = 2.0
EDGE_MIN = 0.3

# ------------------------------------------------------------ ネット
NETS = ("GND", "ENC_A", "ENC_B", "ENC_SW", "KEY1", "KEY2", "KEY3", "KEY4")

XIAO_NET = {
    "2": "KEY4",     # D1  P0.03
    "3": "ENC_B",    # D2  P0.28
    "4": "KEY1",     # D3  P0.29
    "5": "KEY2",     # D4  P0.04
    "6": "KEY3",     # D5  P0.05
    "9": "ENC_SW",   # D8  P1.13
    "11": "ENC_A",   # D10 P1.15
    "13": "GND",
}
XIAO_SPARE = {"1", "7", "8", "10", "12", "14"}

ENC_NET = {"A": "ENC_A", "B": "ENC_B", "C": "GND", "S1": "ENC_SW", "S2": "GND"}


# ------------------------------------------------------------ 共通
def mm(v):
    return pcbnew.FromMM(v)


def P(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


def to_mm(v):
    return round(pcbnew.ToMM(v), 3)


def load_fp(lib, name):
    fp = pcbnew.FootprintLoad(lib, name)
    if fp is None:
        sys.exit(f"[ERROR] フットプリントが見つかりません: {os.path.join(lib, name)}.kicad_mod")
    return fp


def new_board():
    try:
        return pcbnew.BOARD()
    except Exception:
        return pcbnew.CreateEmptyBoard()


def lset(*layers):
    ls = pcbnew.LSET()
    for layer in layers:
        try:
            ls.AddLayer(layer)
        except AttributeError:
            ls.addLayer(layer)
    return ls


def pad_rel(fp, num):
    for p in fp.Pads():
        if p.GetNumber() == num:
            a, o = p.GetPosition(), fp.GetPosition()
            return (to_mm(a.x - o.x), to_mm(a.y - o.y))
    return None


def assign_nets(fp, mapping, nets):
    for pad in fp.Pads():
        name = mapping.get(pad.GetNumber())
        if name:
            pad.SetNet(nets[name])


def exclude_from_jlc(fp):
    try:
        fp.SetAttributes(fp.GetAttributes()
                         | pcbnew.FP_EXCLUDE_FROM_POS_FILES
                         | pcbnew.FP_EXCLUDE_FROM_BOM)
    except AttributeError:
        print(f"[WARN] {fp.GetReference()} の除外属性を設定できません（手動で設定）")


def flip_to_back(fp):
    pos = fp.GetPosition()
    try:
        fp.Flip(pos, pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    except (AttributeError, TypeError, NotImplementedError):
        fp.Flip(pos, True)


def place_back(fp, pos, check_pad, want_x_neg, want_y_neg=None):
    fp.SetOrientationDegrees(0)
    fp.SetPosition(P(*pos))
    flip_to_back(fp)

    def ok():
        dx, dy = pad_rel(fp, check_pad)
        cx = want_x_neg is None or (dx < 0) == want_x_neg
        cy = want_y_neg is None or (dy < 0) == want_y_neg
        return cx and cy, (dx, dy)

    good, rel = ok()
    if not good:
        fp.SetOrientationDegrees(fp.GetOrientationDegrees() + 180.0)
        good, rel = ok()
    tag = "OK" if good else "WARN"
    print(f"[{tag}] {fp.GetReference()} 裏面 パッド{check_pad} 相対位置={rel}")


# ------------------------------------------------------------ CKW12: MP 除去（テキスト加工）
PAD_RE = re.compile(r"\(pad\s")
AT_RE = re.compile(r"\(at\s+(-?[\d.]+)\s+(-?[\d.]+)")
NAME_RE = re.compile(r'\((footprint|module)\s+("(?:[^"\\]|\\.)*"|[^\s()]+)')


def block_end(text, start):
    depth = 0
    in_str = False
    i = start
    while i < len(text):
        c = text[i]
        if in_str:
            if c == "\\":
                i += 2
                continue
            if c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    sys.exit("[ERROR] CKW12 フットプリントの括弧が閉じていません")


def make_enc_nomp():
    src = os.path.join(LIB_MPAD, FP_ENC_SRC + ".kicad_mod")
    dst = os.path.join(LIB_MPAD, FP_ENC + ".kicad_mod")
    if not os.path.exists(src):
        sys.exit(f"[ERROR] 公式 CKW12 フットプリントがありません: {src}")
    with open(src, encoding="utf-8") as f:
        text = f.read()

    out, pos, removed = [], 0, 0
    while True:
        m = PAD_RE.search(text, pos)
        if not m:
            out.append(text[pos:])
            break
        s = m.start()
        e = block_end(text, s)
        at = AT_RE.search(text[s:e])
        is_mp = False
        if at:
            x, y = float(at.group(1)), float(at.group(2))
            is_mp = abs(abs(x) - MP_X) < 0.05 and abs(y) < 0.05
        if is_mp:
            out.append(text[pos:s].rstrip(" \t"))
            removed += 1
        else:
            out.append(text[pos:e])
        pos = e

    new = NAME_RE.sub(lambda g: f'({g.group(1)} "{FP_ENC}"', "".join(out), count=1)
    with open(dst, "w", encoding="utf-8") as f:
        f.write(new)
    tag = "OK" if removed == 2 else "WARN"
    print(f"[{tag}] CKW12 の MP を {removed} 個除去 → {FP_ENC}.kicad_mod")


# ------------------------------------------------------------ 外形・ゾーン
def add_edge(board):
    x0, y0 = ORIGIN_X, ORIGIN_Y
    x1, y1 = x0 + BOARD_W, y0 + BOARD_L
    r = CORNER_R
    k = r * (1.0 - 1.0 / math.sqrt(2.0))
    lines = (((x0 + r, y0), (x1 - r, y0)),
             ((x1, y0 + r), (x1, y1 - r)),
             ((x1 - r, y1), (x0 + r, y1)),
             ((x0, y1 - r), (x0, y0 + r)))
    arcs = (((x0, y0 + r), (x0 + k, y0 + k), (x0 + r, y0)),
            ((x1 - r, y0), (x1 - k, y0 + k), (x1, y0 + r)),
            ((x1, y1 - r), (x1 - k, y1 - k), (x1 - r, y1)),
            ((x0 + r, y1), (x0 + k, y1 - k), (x0, y1 - r)))
    for a, b in lines:
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(P(*a))
        s.SetEnd(P(*b))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(mm(0.1))
        board.Add(s)
    for a, m, b in arcs:
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_ARC)
        s.SetArcGeometry(P(*a), P(*m), P(*b))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(mm(0.1))
        board.Add(s)


def rect_outline(zone, x0, y0, x1, y1):
    o = zone.Outline()
    o.NewOutline()
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        o.Append(mm(x), mm(y))


def add_zones(board, gnd):
    try:
        z = pcbnew.ZONE(board)
        z.SetLayer(pcbnew.B_Cu)
        z.SetNet(gnd)
        rect_outline(z, ORIGIN_X, ORIGIN_Y, ORIGIN_X + BOARD_W, ORIGIN_Y + BOARD_L)
        board.Add(z)
        print("[OK] B.Cu GND ゾーン（未充填）")
    except Exception as e:
        print(f"[WARN] GND ゾーンを作れません（手動で作成）: {e}")

    end = XIAO_POS[1] + XIAO_L / 2.0
    ky0, ky1 = end - ANT_KO_INTO_XIAO, end + ANT_KO_GAP
    try:
        k = pcbnew.ZONE(board)
        k.SetIsRuleArea(True)
        k.SetLayerSet(lset(pcbnew.F_Cu, pcbnew.B_Cu))
        rect_outline(k, ORIGIN_X, ky0, ORIGIN_X + BOARD_W, ky1)
        k.SetDoNotAllowTracks(False)
        k.SetDoNotAllowVias(True)
        for name in ("SetDoNotAllowZoneFills", "SetDoNotAllowCopperPour"):
            if hasattr(k, name):
                getattr(k, name)(True)
                break
        for name in ("SetDoNotAllowPads", "SetDoNotAllowFootprints"):
            if hasattr(k, name):
                getattr(k, name)(False)
        if hasattr(k, "SetZoneName"):
            k.SetZoneName("KO1_ANTENNA")
        board.Add(k)
        print(f"[OK] KO1 y={ky0:.2f}〜{ky1:.2f}（ベタ・ビア禁止、配線可）")
    except Exception as e:
        print(f"[WARN] KO1 を作れません（手動で作成）: {e}")


# ------------------------------------------------------------ 検査
def bb_gap(a, b):
    dx = max(a.GetLeft() - b.GetRight(), b.GetLeft() - a.GetRight(), 0)
    dy = max(a.GetTop() - b.GetBottom(), b.GetTop() - a.GetBottom(), 0)
    return to_mm(int(math.hypot(dx, dy)))


def check_seeed_dip():
    path = os.path.join(LIB_SEEED, SEEED_DIP + ".kicad_mod")
    if not os.path.exists(path):
        print("[INFO] Seeed の DIP フットプリントがないため、列間隔の照合を省略")
        return
    fp = pcbnew.FootprintLoad(LIB_SEEED, SEEED_DIP)
    nums = {str(i) for i in range(1, 15)}
    pts = [p.GetFPRelativePosition() for p in fp.Pads() if p.GetNumber() in nums]
    if len(pts) != 14:
        print(f"[WARN] Seeed DIP のパッド1〜14が {len(pts)} 個しかありません")
        return
    xs = [to_mm(v.x) for v in pts]
    ys = [to_mm(v.y) for v in pts]
    spans = sorted((max(xs) - min(xs), max(ys) - min(ys)))
    print(f"[INFO] Seeed DIP: 配列の幅={spans}（期待値 {XIAO_ROW} / {XIAO_SPAN}）")
    if abs(spans[0] - min(XIAO_ROW, XIAO_SPAN)) > 0.05 or abs(spans[1] - max(XIAO_ROW, XIAO_SPAN)) > 0.05:
        print("[WARN] 列間隔またはピッチが想定と違います。XIAO_nRF52840_DIP_Back を修正してください")


def check_edges(board):
    x0, y0 = mm(ORIGIN_X + EDGE_MIN), mm(ORIGIN_Y + EDGE_MIN)
    x1, y1 = mm(ORIGIN_X + BOARD_W - EDGE_MIN), mm(ORIGIN_Y + BOARD_L - EDGE_MIN)
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                continue
            bb = pad.GetBoundingBox()
            if bb.GetLeft() < x0 or bb.GetRight() > x1 or bb.GetTop() < y0 or bb.GetBottom() > y1:
                print(f"[WARN] {fp.GetReference()} パッド{pad.GetNumber()} が基板端から {EDGE_MIN}mm 以内")


def check_unassigned(board):
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        for pad in fp.Pads():
            if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                continue
            if ref == "U1" and pad.GetNumber() in XIAO_SPARE:
                continue
            if pad.GetNetCode() == 0:
                print(f"[WARN] {ref} パッド{pad.GetNumber()} にネットがありません")


def check_enc(enc, xiao):
    usb_back = XIAO_POS[1] - XIAO_L / 2.0 - USB_PROTRUDE + USB_DEPTH
    tops = [to_mm(p.GetBoundingBox().GetTop()) for p in enc.Pads()
            if abs(to_mm(p.GetPosition().x) - CX) < USB_W / 2.0 + 1.0]
    gap = min(tops) - usb_back
    print(f"[{'OK' if gap >= 0.5 else 'WARN'}] CKW12 中央ピンと USB-C 奥端の Y 方向距離 = {gap:.2f}mm")
    g = min(bb_gap(a.GetBoundingBox(), b.GetBoundingBox()) for a in enc.Pads() for b in xiao.Pads())
    print(f"[{'OK' if g >= 0.5 else 'WARN'}] CKW12 と XIAO のパッド間最小距離 = {g:.2f}mm")


# ------------------------------------------------------------ メイン
def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    make_enc_nomp()
    check_seeed_dip()

    board = new_board()
    board.SetCopperLayerCount(2)
    try:
        board.GetDesignSettings().SetBoardThickness(mm(1.6))
    except Exception as e:
        print(f"[WARN] 基板厚を設定できません（基板設定で 1.6mm を手動設定）: {e}")
    try:
        ds = board.GetDesignSettings()
        ds.SetAuxOrigin(P(ORIGIN_X, ORIGIN_Y))
        ds.SetGridOrigin(P(ORIGIN_X, ORIGIN_Y))
    except Exception:
        print("[WARN] 原点を設定できません（基板左上に手動で設定）")

    nets = {}
    for name in NETS:
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni)
        nets[name] = ni

    add_edge(board)

    xiao = load_fp(LIB_MPAD, FP_XIAO)
    board.Add(xiao)
    xiao.SetReference("U1")
    xiao.SetValue("XIAO_nRF52840")
    place_back(xiao, XIAO_POS, "1", want_x_neg=True, want_y_neg=True)
    p14 = pad_rel(xiao, "14")
    print(f"[{'OK' if p14[0] > 0 and p14[1] < 0 else 'WARN'}] U1 パッド14 相対位置={p14}（右上が正）")
    assign_nets(xiao, XIAO_NET, nets)
    exclude_from_jlc(xiao)

    enc = load_fp(LIB_MPAD, FP_ENC)
    board.Add(enc)
    enc.SetReference("ENC1")
    enc.SetValue("CKW12")
    enc.SetOrientationDegrees(0)
    enc.SetPosition(P(*ENC_POS))
    assign_nets(enc, ENC_NET, nets)
    exclude_from_jlc(enc)

    for i, y in enumerate(KEY_Y, start=1):
        sw = load_fp(LIB_MPAD, FP_SW)
        board.Add(sw)
        sw.SetReference(f"SW{i}")
        sw.SetValue("CPG151101S11")
        place_back(sw, (CX, y), "1", want_x_neg=True, want_y_neg=True)
        assign_nets(sw, {"1": f"KEY{i}", "2": "GND"}, nets)

    add_zones(board, nets["GND"])
    check_edges(board)
    check_unassigned(board)
    check_enc(enc, xiao)

    pcbnew.SaveBoard(OUT_PCB, board)
    print(f"[DONE] {OUT_PCB}")


if __name__ == "__main__":
    main()