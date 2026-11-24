# File: gen_mpad.py
"""縦長BTマクロパッド：部品配置済み・未配線の基板を生成する（段階4）

実行環境: KiCad 10.0.x に同梱の Python（SWIG版 pcbnew）
  - KiCad 10 では import 時に非推奨警告が出るが動作する
  - SWIG版 pcbnew は KiCad 11 で削除予定（生成済みの .kicad_pcb は 11 でも開ける）

使い方:
  python gen_mpad.py --list-pads   Seeed XIAO フットプリントのパッド一覧を表示
  python gen_mpad.py               基板を生成（out/mpad.kicad_pcb）
"""

import argparse
import math
import os
import sys

import pcbnew

# ------------------------------------------------------------ パス
HERE = os.path.dirname(os.path.abspath(__file__))
LIB_MPAD = os.path.join(HERE, "lib", "mpad.pretty")
LIB_SEEED = os.path.join(HERE, "lib", "Seeed_XIAO.pretty")
SEEED_FP = "XIAO-nRF52840-SMD"
XIAO_FP_OUT = "XIAO_nRF52840_SMD_BackAccess"
OUT_DIR = os.path.join(HERE, "out")
OUT_PCB = os.path.join(OUT_DIR, "mpad.kicad_pcb")

# ------------------------------------------------------------ XIAO 裏面パッド
XIAO_PAD_BAT_NEG = "20"   # 検証で修正: Seeed公式シンボルでは 20=GND（電池マイナス側）
XIAO_PAD_BAT_POS = "19"   # 検証で修正: Seeed公式シンボルでは 19=VBAT（電池プラス）
XIAO_PAD_RST = None       # --list-pads で RST の番号を確認して文字列で設定。None なら RST 穴と TP を省略
BACK_HOLE_DRILL = 1.0
BACK_HOLE_PAD = 1.7

# ------------------------------------------------------------ 寸法（KiCad座標, mm, Yは下向き）
ORIGIN_X = 100.0
ORIGIN_Y = 100.0
BOARD_W = 19.0
BOARD_L = 118.7
CORNER_R = 1.0
CX = ORIGIN_X + BOARD_W / 2.0

XIAO_POS = (CX, 110.50)   # XIAO本体の中心（端面パッド配列の中心で合わせる）
XIAO_LEN = 21.0
ENC_POS = (CX, 132.525)
KEY_Y = (151.575, 170.625, 189.675, 208.725)
J1_POS = (CX, 142.90)
TP1_POS = (CX - 1.27, 104.00)
TP2_POS = (CX + 1.27, 104.00)

ANT_KO_INTO_XIAO = 4.0    # XIAO末端から内側へ（ベタ・ビア禁止）
ANT_KO_GAP = 2.0          # XIAO末端から外側へ
EDGE_MIN = 0.3            # 銅と基板端の距離の警告しきい値（JLCの正式ルールはDRCで確認）

# ------------------------------------------------------------ ネット
NETS = ("GND", "BAT+", "RST", "ENC_A", "ENC_B", "ENC_SW",
        "KEY1", "KEY2", "KEY3", "KEY4")

XIAO_NET = {
    "1": "ENC_A",    # D0 P0.02
    "2": "ENC_B",    # D1 P0.03
    "3": "ENC_SW",   # D2 P0.28
    "4": "KEY1",     # D3 P0.29
    "5": "KEY2",     # D4 P0.04
    "6": "KEY3",     # D5 P0.05
    "9": "KEY4",     # D8 P1.13
    "13": "GND",
}
XIAO_SPARE = {"7", "8", "10", "11", "12", "14"}   # D6, D7, D9, D10, 3V3, 5V

ENC_NET = {"A": "ENC_A", "B": "ENC_B", "C": "GND",
           "S1": "ENC_SW", "S2": "GND", "MP": "GND"}


# ------------------------------------------------------------ 共通ヘルパー
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


def pad_size(pad):
    try:
        s = pad.GetSize(pcbnew.F_Cu)
    except (TypeError, NotImplementedError):
        s = pad.GetSize()
    return to_mm(s.x), to_mm(s.y)


def set_shape_size(pad, shape, w, h):
    size = P(w, h)
    try:
        pad.SetShape(pcbnew.F_Cu, shape)
        pad.SetSize(pcbnew.F_Cu, size)
    except (TypeError, NotImplementedError):
        pad.SetShape(shape)
        pad.SetSize(size)


def pth_mask():
    try:
        return pcbnew.PAD.PTHMask()
    except AttributeError:
        return pcbnew.PAD_PTHMask()


def lset(*layers):
    ls = pcbnew.LSET()
    for layer in layers:
        try:
            ls.AddLayer(layer)
        except AttributeError:
            ls.addLayer(layer)
    return ls


def pads_by_number(fp, num):
    return [p for p in fp.Pads() if p.GetNumber() == num]


def pad_rel(fp, num, center=None):
    pads = pads_by_number(fp, num)
    if not pads:
        return None
    a = pads[0].GetPosition()
    o = center if center is not None else fp.GetPosition()
    return (to_mm(a.x - o.x), to_mm(a.y - o.y))


def array_center(fp, nums):
    xs, ys = [], []
    for p in fp.Pads():
        if p.GetNumber() in nums:
            a = p.GetPosition()
            xs.append(a.x)
            ys.append(a.y)
    return pcbnew.VECTOR2I((min(xs) + max(xs)) // 2, (min(ys) + max(ys)) // 2)


def exclude_from_jlc(fp):
    try:
        fp.SetAttributes(fp.GetAttributes()
                         | pcbnew.FP_EXCLUDE_FROM_POS_FILES
                         | pcbnew.FP_EXCLUDE_FROM_BOM)
    except AttributeError:
        print(f"[WARN] {fp.GetReference()} の除外属性を設定できませんでした（手動で設定）")


def assign_nets(fp, mapping, nets):
    for pad in fp.Pads():
        name = mapping.get(pad.GetNumber())
        if name:
            pad.SetNet(nets[name])


# ------------------------------------------------------------ XIAO
def list_pads(fp):
    print(f"{'pad':>5} {'x':>8} {'y':>8} {'w':>6} {'h':>6}  attr")
    for pad in sorted(fp.Pads(), key=lambda p: (len(p.GetNumber()), p.GetNumber())):
        pos = pad.GetFPRelativePosition()
        w, h = pad_size(pad)
        attr = "SMD" if pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD else "THT/NPTH"
        print(f"{pad.GetNumber():>5} {to_mm(pos.x):8.3f} {to_mm(pos.y):8.3f} {w:6.2f} {h:6.2f}  {attr}")


def build_xiao_backaccess():
    # 検証で修正: KiCad 10.0.8 (Linux AppImage) の SWIG pcbnew では Footprint.Remove() を
    # 繰り返すとバインディングが壊れるため、裏面加工済みフットプリント
    # （lib/mpad.pretty/XIAO_nRF52840_SMD_BackAccess.kicad_mod、Seeed公式ファイルを
    # テキスト編集で加工：未使用裏面パッド削除、19=VBAT/20=GND を貫通穴化）を読み込む方式に変更。
    fp = load_fp(LIB_MPAD, XIAO_FP_OUT)
    back = {XIAO_PAD_BAT_NEG: "GND", XIAO_PAD_BAT_POS: "BAT+"}
    if XIAO_PAD_RST:
        back[XIAO_PAD_RST] = "RST"
    return fp, back


def place_xiao(fp):
    edge_nums = {str(i) for i in range(1, 15)}
    for deg in (0.0, 90.0, 180.0, 270.0):
        fp.SetOrientationDegrees(deg)
        c = array_center(fp, edge_nums)
        p1 = pad_rel(fp, "1", c)
        p14 = pad_rel(fp, "14", c)
        if p1 is None or p14 is None:
            sys.exit("[ERROR] XIAO のパッド1/14が見つかりません")
        if p1[0] < 0 < p14[0] and p1[1] < 0 and p14[1] < 0 and abs(p1[1] - p14[1]) < 0.5:
            target = P(*XIAO_POS)
            fp.Move(pcbnew.VECTOR2I(target.x - c.x, target.y - c.y))
            print(f"[OK] U1 回転 {deg:.0f}°（パッド1={p1} パッド14={p14}、配列中心基準）")
            return
    sys.exit("[ERROR] パッド1が左上・パッド14が右上になる回転がありません（--list-pads で番号を確認）")


def report_xiao_body(fp):
    ys = []
    for item in fp.GraphicalItems():
        if item.GetLayer() in (pcbnew.F_Fab, pcbnew.F_SilkS, pcbnew.F_CrtYd):
            bb = item.GetBoundingBox()
            ys += [bb.GetTop(), bb.GetBottom()]
    if not ys:
        print("[INFO] XIAO の外形図形が見つかりません。上端位置は目視で確認してください")
        return
    top, bottom = to_mm(min(ys)), to_mm(max(ys))
    print(f"[INFO] XIAO 図形の範囲 y={top}〜{bottom}（基板上端 y={ORIGIN_Y}）")
    if abs(top - ORIGIN_Y) > 0.5:
        print("[WARN] XIAO の上端が基板上端と0.5mm以上ずれています。XIAO_POS の Y を調整してください")


# ------------------------------------------------------------ 裏面配置
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
        cond_x = want_x_neg is None or (dx < 0) == want_x_neg
        cond_y = want_y_neg is None or (dy < 0) == want_y_neg
        return cond_x and cond_y, (dx, dy)

    good, rel = ok()
    if not good:
        fp.SetOrientationDegrees(fp.GetOrientationDegrees() + 180.0)
        good, rel = ok()
    tag = "OK" if good else "WARN"
    print(f"[{tag}] {fp.GetReference()} 裏面 パッド{check_pad} 相対位置={rel}")


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
        print(f"[WARN] GND ゾーンを作れませんでした（手動で作成）: {e}")

    xiao_end = XIAO_POS[1] + XIAO_LEN / 2.0
    ky0 = xiao_end - ANT_KO_INTO_XIAO
    ky1 = xiao_end + ANT_KO_GAP
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
        print(f"[OK] KO1 アンテナ禁止域 y={ky0:.2f}〜{ky1:.2f}（ベタ・ビア禁止、配線可）")
    except Exception as e:
        print(f"[WARN] KO1 を作れませんでした（手動で作成）: {e}")


# ------------------------------------------------------------ 検査
def check_edges(board):
    x0, y0 = mm(ORIGIN_X + EDGE_MIN), mm(ORIGIN_Y + EDGE_MIN)
    x1, y1 = mm(ORIGIN_X + BOARD_W - EDGE_MIN), mm(ORIGIN_Y + BOARD_L - EDGE_MIN)
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                continue
            bb = pad.GetBoundingBox()
            if bb.GetLeft() < x0 or bb.GetRight() > x1 or bb.GetTop() < y0 or bb.GetBottom() > y1:
                print(f"[WARN] {fp.GetReference()} パッド{pad.GetNumber()} が基板端から {EDGE_MIN}mm 以内です")


def check_unassigned(board):
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        for pad in fp.Pads():
            if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                continue
            if ref == "U1" and pad.GetNumber() in XIAO_SPARE:
                continue
            if pad.GetNetCode() == 0:
                print(f"[WARN] {ref} パッド{pad.GetNumber()} にネットが割り当てられていません")


# ------------------------------------------------------------ メイン
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list-pads", action="store_true")
    args = ap.parse_args()

    if args.list_pads:
        list_pads(load_fp(LIB_SEEED, SEEED_FP))
        return

    os.makedirs(OUT_DIR, exist_ok=True)

    xiao, back = build_xiao_backaccess()
    try:
        pcbnew.FootprintSave(LIB_MPAD, xiao)
        xiao = load_fp(LIB_MPAD, XIAO_FP_OUT)
        print(f"[OK] {XIAO_FP_OUT}.kicad_mod を保存")
    except Exception as e:
        print(f"[WARN] XIAO フットプリントを保存できませんでした（基板には配置します）: {e}")

    board = pcbnew.BOARD()  # 検証で修正: KiCad 10.0.8 の SWIG では CreateEmptyBoard が未型付けオブジェクトを返すため
    board.SetCopperLayerCount(2)
    ds = board.GetDesignSettings()
    try:
        ds.SetBoardThickness(mm(1.6))
    except AttributeError:
        print("[WARN] 基板厚を設定できませんでした（KiCad 10.0.8 SWIG の型付け制限。基板設定で手動指定）")
    try:
        ds.SetAuxOrigin(P(ORIGIN_X, ORIGIN_Y))
        ds.SetGridOrigin(P(ORIGIN_X, ORIGIN_Y))
    except AttributeError:
        print("[WARN] 原点を設定できませんでした（基板左上に手動で設定）")

    nets = {}
    for name in NETS:
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni)
        nets[name] = ni

    add_edge(board)

    # U1: XIAO
    board.Add(xiao)
    xiao.SetReference("U1")
    xiao.SetValue("XIAO_nRF52840")
    place_xiao(xiao)
    assign_nets(xiao, {**XIAO_NET, **back}, nets)
    exclude_from_jlc(xiao)
    report_xiao_body(xiao)

    # ENC1: CKW12
    enc = load_fp(LIB_MPAD, "RotaryEncoder_EC12_CKW12")
    board.Add(enc)
    enc.SetReference("ENC1")
    enc.SetValue("CKW12")
    enc.SetOrientationDegrees(0)
    enc.SetPosition(P(*ENC_POS))
    assign_nets(enc, ENC_NET, nets)
    exclude_from_jlc(enc)

    # SW1-4: MX + Kailh ソケット（裏面）
    for i, y in enumerate(KEY_Y, start=1):
        sw = load_fp(LIB_MPAD, "SW_MX_HS_Kailh_1U_Back")
        board.Add(sw)
        sw.SetReference(f"SW{i}")
        sw.SetValue("CPG151101S11")
        place_back(sw, (CX, y), "1", want_x_neg=True, want_y_neg=True)
        assign_nets(sw, {"1": f"KEY{i}", "2": "GND"}, nets)

    # J1: 電池パッド（裏面）
    j1 = load_fp(LIB_MPAD, "BattPad_2P_TH_P3.5")
    board.Add(j1)
    j1.SetReference("J1")
    j1.SetValue("LiPo")
    place_back(j1, J1_POS, "1", want_x_neg=True)
    assign_nets(j1, {"1": "BAT+", "2": "GND"}, nets)

    # TP1/TP2: リセット用テストパッド（裏面）
    if XIAO_PAD_RST:
        for ref, pos, net in (("TP1", TP1_POS, "RST"), ("TP2", TP2_POS, "GND")):
            tp = load_fp(LIB_MPAD, "TestPad_SMD_D1.5")
            board.Add(tp)
            tp.SetReference(ref)
            tp.SetValue(net)
            place_back(tp, pos, "1", want_x_neg=None)
            assign_nets(tp, {"1": net}, nets)
    else:
        print("[INFO] XIAO_PAD_RST 未設定のため、RST 穴と TP1/TP2 を省略しました")

    add_zones(board, nets["GND"])
    check_edges(board)
    check_unassigned(board)

    pcbnew.SaveBoard(OUT_PCB, board)
    print(f"[DONE] {OUT_PCB}")


if __name__ == "__main__":
    main()