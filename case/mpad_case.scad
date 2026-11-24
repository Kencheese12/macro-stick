// File: mpad_case.scad
// 縦長BTマクロパッド 筐体・底板・プレート・ヘッダスペーサー（B案・発注前修正版）
//
// 座標系: x=幅（中心0）、y=長手（USB側の外面=0、下端へ+）、z=高さ（底板下面=0）
// 注意: この座標系は KiCad の上面図に対して左右が鏡像になる
// KiCad の相対座標 X → 筐体 x = -X（左右非対称な形状はこの変換で配置）

/* [出力するパーツ] */
part = "assembly"; // [assembly, body, bottom, spacer, plate2d, plate3d]

/* [ID42 合わせ（実測後に変更）] */
id42_plate_top_from_desk = 16.9; // 机面→プレート上面
foot_h = 1.5;
foot_d = 8.0;
foot_x = 5.4;
foot_y_front = 7.0;
foot_y_rear_from_end = 13.5;

/* [XIAO（実測後に変更）] */
usb_protrude = 1.0;
usb_w = 8.94;
usb_h = 3.2;
usb_depth = 7.35;
xiao_w = 17.8;
xiao_l = 21.0;
xiao_t = 1.6;
xiao_gap = 4.0;
pin_cy = 12.8; // U1 ピン配列中心（KiCad Y=110.5）の筐体 y

/* [XIAO 裏面パッド: Seeed XIAO-nRF52840-SMD を --list-pads した値] */
// 4項目とも同じ SMD フットプリントの値を入れる（メイン基板上の DIP 座標は不可）
fp_pad1 = [0.835, -18.12]; // Seeed SMD --list-pads 実測 (Muse, 2026-11-24)
fp_pad7 = [0.835, -2.88];
fp_pad14 = [17.0, -18.12];
fp_bat = [[4.445, -10.8135], [4.445, -12.7185]]; // 19=VBAT, 20=GND
bat_pad = [2.5, 1.1];
relief_margin = 1.5;
relief_d = 1.0;
lead_w = 3.0;

/* [外形] */
L = 111.7;
W = 24.0;
R_out = 3.0;
wall_s = 2.1;
wall_e = 2.0;
skin = 0.8;
usb_wall = 0.8;
rear_skin = 1.0; // 底板後端の差し込み部の外側に残す壁厚

/* [配置] */
pcb_y0 = 2.3;
pcb_w = 19.0;
pcb_l = 101.9;
enc_y = 18.0;
pitch = 19.05;

/* [開口] */
enc_open = 18.6;
slot_w = 16.4;
usb_open_w = 9.4;
usb_open_h = 3.8;
usb_open_r = 1.5;

/* [固定] */
boss_x = 7.0;
boss_from_end = 3.9;
boss_d = 6.2;
insert_hole_d = 3.3;
insert_depth = 4.5;
screw_d = 2.4;
cbore_d = 4.2;
cbore_h = 1.0;
tab_x = 7.0;
tab_w = 4.0;
tab_t = 1.0;
tab_z0 = 0.5;
tab_slot_skin = 0.9;
tab_tip_clr = 0.3;

/* [はめ合い] */
fit_clr = 0.3; // 幅方向（片側）
fit_clr_l = 0.4; // 長手方向（片側）

/* [プレート] */
plate_w = 19.2;
plate_t = 1.5;
sw_hole = 14.0;
plate_r = 0.5;
plate_tail = 9.8; // KEY4 中心 → プレート下端

/* [前側の基板支え] */
front_support = true;
fs_x0 = 4.5;
fs_x1 = 7.5;
fs_depth = 2.0;
enc_s_pad_outer = 3.5; // CKW12 S列パッドの外端 |x|

/* [外観用の推定値] */
keytop_above_plate = 13.0;
wheel_above_top = 5.0;

$fn = 48;

// ---------- 高さ方向 ----------
base_bottom_t = 2.0;
plate_top_nom = 15.4;
extra = id42_plate_top_from_desk - (plate_top_nom + foot_h);
bottom_t = base_bottom_t + max(0, extra);
pcb_t = 1.6;
poron = 0.5;
pcb_bot = bottom_t + 6.8;
pcb_top = pcb_bot + pcb_t;
plate_bot = pcb_top + 3.5;
plate_top = plate_bot + plate_t;
top_z = plate_top + skin;

xiao_top = pcb_bot - xiao_gap;
xiao_bot = xiao_top - xiao_t;
xiao_y0 = pcb_y0;
usb_zc = xiao_top + usb_h / 2;
usb_back = xiao_y0 - usb_protrude + usb_depth;

// ---------- 平面方向 ----------
key_y = [for (i = [1:4]) enc_y + pitch * i];
plate_y0 = key_y[0] - 9.275;
plate_y1 = key_y[3] + plate_tail;
slot_y0 = key_y[0] - 8.275;
slot_y1 = key_y[3] + 8.275;

in_w = W - 2 * wall_s;
boss_y = L - boss_from_end;

bp_w = in_w - 2 * fit_clr;
bp_y0 = wall_e + fit_clr_l;
bp_y1 = L - rear_skin - fit_clr_l;

tab_tip_y = tab_slot_skin + tab_tip_clr;
tab_len = bp_y0 - tab_tip_y;

rail_x0 = 8.8;
rail_x1 = bp_w / 2;
rail_y0 = key_y[0] - 9.0;
rail_y1 = key_y[3] + 9.0;
rail_top = pcb_bot - poron;

stop_y0 = xiao_y0 + xiao_l + 0.2;
lead_y1 = key_y[0] - 5.0;

foot_pos = [[-foot_x, foot_y_front], [foot_x, foot_y_front],
[-foot_x, L - foot_y_rear_from_end], [foot_x, L - foot_y_rear_from_end]];

// ---------- XIAO 裏面パッド → 筐体座標 ----------
fp_given = fp_pad1 != fp_pad7;
fp_cx = (fp_pad1[0] + fp_pad14[0]) / 2;
fp_cy = (fp_pad1[1] + fp_pad7[1]) / 2;
bat_xy = [for (p = fp_bat) [-(p[0] - fp_cx), pin_cy + (p[1] - fp_cy)]];
bat_x0 = min([for (p = bat_xy) p[0]]) - bat_pad[0] / 2;
bat_x1 = max([for (p = bat_xy) p[0]]) + bat_pad[0] / 2;
bat_y0 = min([for (p = bat_xy) p[1]]) - bat_pad[1] / 2;
bat_y1 = max([for (p = bat_xy) p[1]]) + bat_pad[1] / 2;
relief_x0 = min(-lead_w / 2, bat_x0 - relief_margin);
relief_x1 = max(lead_w / 2, bat_x1 + relief_margin);
relief_y0 = bat_y0 - relief_margin;
relief_y1 = bat_y1 + relief_margin;

// ---------- 常に行う検査 ----------
if (extra < 0)
echo(str("[注意] 目標より ", -extra, " mm 高い。ゴム足を薄くしてください"));
echo(str("全長=", L, " 本体高さ(ゴム足込み)=", top_z + foot_h,
" プレート上面(机から)=", plate_top + foot_h,
" キートップ推定(机から)=", plate_top + keytop_above_plate + foot_h,
" プレート=", plate_w, "x", plate_y1 - plate_y0));
assert(plate_y1 < boss_y - boss_d / 2 - 0.3, "プレートが下端ボスに当たる");
assert(pcb_y0 + pcb_l < boss_y - boss_d / 2 - 0.15, "基板が下端ボスに当たる");
assert(enc_y - 7.5 - 1.0 - usb_back >= 0.5, "CKW12 の A/B/C ピンが USB-C に近すぎる");
assert(enc_y - enc_open / 2 > wall_e + 1.0, "CKW12 開口が上端壁に近すぎる");
assert(boss_y + cbore_d / 2 + 0.3 < bp_y1, "座ぐりが底板の後端にかかる");
assert(boss_y + insert_hole_d / 2 < L - wall_e, "インサート穴が端壁の内面から出る");
assert(tab_len > 0.8, "ツメが短すぎる");
assert(fs_x0 - enc_s_pad_outer >= 0.8, "前側の支えが CKW12 S列ピンに近すぎる");
assert(abs(foot_x) + foot_d / 2 < bp_w / 2 - 0.1, "ゴム足が底板の端をまたぐ");
assert(foot_y_front - foot_d / 2 > bp_y0 + 0.1, "前側ゴム足が底板の上端をまたぐ");

// ---------- 底板を出力するときだけ行う検査 ----------
if (part == "bottom" || part == "assembly") {
assert(fp_given, "fp_pad1 / fp_pad7 / fp_pad14 に Seeed SMD フットプリントの --list-pads 値を入れてください");
assert(fp_pad1[0] < fp_pad14[0] && fp_pad1[1] < fp_pad7[1],
"SMD フットプリントの向きが想定と違う（パッド1が左上でない）");
assert(abs(fp_pad7[1] - fp_pad1[1] - 15.24) < 0.1, "パッド1〜7の間隔が 15.24 でない（別のパッドの値?）");
for (p = bat_xy)
assert(abs(p[0]) + bat_pad[0] / 2 < xiao_w / 2
&& p[1] - bat_pad[1] / 2 > xiao_y0
&& p[1] + bat_pad[1] / 2 < xiao_y0 + xiao_l,
"電池パッドが XIAO の外形からはみ出す（DIP の座標を入れていないか確認）");
assert(relief_y1 < stop_y0 - 0.5, "逃げが XIAO 後端ストッパーにかかる");
assert(relief_y0 > bp_y0 + 1.0, "逃げが底板の上端にかかる");
assert(relief_x0 > -bp_w / 2 + 1.0 && relief_x1 < bp_w / 2 - 1.0, "逃げが底板の側端に近すぎる");
echo(str("電池パッド中心(筐体座標)=", bat_xy,
" 逃げ x=", relief_x0, "〜", relief_x1, " y=", relief_y0, "〜", relief_y1));
}

// ---------- 共通 ----------
module rsq(w, l, r) {
offset(r = r) offset(delta = -r) square([w, l]);
}

module rbox(w, l, h, r) {
linear_extrude(h) translate([-w / 2, 0]) rsq(w, l, r);
}

// ---------- 筐体本体 ----------
module body() {
difference() {
union() {
difference() {
rbox(W, L, top_z, R_out);
translate([-in_w / 2, wall_e, -1])
cube([in_w, L - 2 * wall_e, plate_top + 1]);
}
for (sx = [-1, 1])
translate([sx * boss_x, boss_y, bottom_t])
cylinder(d = boss_d, h = top_z - bottom_t);
}
// 底板後端の差し込み部（端壁の下部）
translate([-in_w / 2, L - wall_e - 0.01, -1])
cube([in_w, wall_e - rear_skin + 0.01, bottom_t + 1]);
// インサート下穴
for (sx = [-1, 1])
translate([sx * boss_x, boss_y, bottom_t - 0.01])
cylinder(d = insert_hole_d, h = insert_depth);
// CKW12 開口
translate([-enc_open / 2, enc_y - enc_open / 2, plate_top - 1])
cube([enc_open, enc_open, skin + 2]);
// キー用スロット
translate([0, 0, plate_top - 1])
linear_extrude(skin + 2)
translate([-slot_w / 2, slot_y0]) rsq(slot_w, slot_y1 - slot_y0, 1.0);
// USB 開口
translate([0, -1, usb_zc])
rotate([-90, 0, 0])
linear_extrude(wall_e + 2)
offset(r = usb_open_r) offset(delta = -usb_open_r)
square([usb_open_w, usb_open_h], center = true);
// USB 部の内側薄肉化
translate([-6, usb_wall, usb_zc - 3])
cube([12, wall_e - usb_wall + 0.01, 6]);
// 底板ツメの溝
for (sx = [-1, 1])
translate([sx * tab_x - (tab_w + 0.4) / 2, tab_slot_skin, tab_z0 - 0.2])
cube([tab_w + 0.4, wall_e - tab_slot_skin + 0.01, tab_t + 0.4]);
}
}

// ---------- 底板 ----------
module bottom() {
difference() {
union() {
translate([-bp_w / 2, bp_y0, 0])
cube([bp_w, bp_y1 - bp_y0, bottom_t]);
// 上端ツメ
for (sx = [-1, 1])
translate([sx * tab_x - tab_w / 2, tab_tip_y, tab_z0])
cube([tab_w, tab_len + 0.01, tab_t]);
// 基板受けレール（上に PORON 0.5）
for (sx = [-1, 1])
translate([sx > 0 ? rail_x0 : -rail_x1, rail_y0, bottom_t - 0.01])
cube([rail_x1 - rail_x0, rail_y1 - rail_y0, rail_top - bottom_t + 0.01]);
// XIAO 後端ストッパー（中央は電池リードの通り道）
for (sx = [-1, 1])
translate([sx > 0 ? 2.5 : -7.5, stop_y0, bottom_t - 0.01])
cube([5.0, 1.2, xiao_top - bottom_t + 0.01]);
// 前側の基板支え（上に PORON 0.5）
if (front_support)
for (sx = [-1, 1])
translate([sx > 0 ? fs_x0 : -fs_x1, stop_y0, bottom_t - 0.01])
cube([fs_x1 - fs_x0, fs_depth, rail_top - bottom_t + 0.01]);
}
// ねじ穴＋座ぐり
for (sx = [-1, 1])
translate([sx * boss_x, boss_y, -0.01]) {
cylinder(d = screw_d, h = bottom_t + 0.02);
cylinder(d = cbore_d, h = cbore_h + 0.01);
}
// XIAO 裏面パッド（19/20）の逃げ
translate([relief_x0, relief_y0, bottom_t - relief_d])
cube([relief_x1 - relief_x0, relief_y1 - relief_y0, relief_d + 0.01]);
// 電池リード溝（ストッパー中央の隙間を通る）
translate([-lead_w / 2, relief_y1 - 0.01, bottom_t - relief_d])
cube([lead_w, lead_y1 - relief_y1, relief_d + 0.01]);
}
}

// ---------- ヘッダスペーサー（1.5mm ×2） ----------
module spacer() {
for (i = [0, 1])
translate([i * 5, 0, 0])
difference() {
translate([-1.5, -1.6, 0]) cube([3.0, 2.54 * 6 + 3.2, 1.5]);
for (k = [0:6])
translate([0, k * 2.54, -0.01]) cylinder(d = 1.4, h = 1.52);
}
}

// ---------- プレート ----------
module plate_2d() {
difference() {
translate([-plate_w / 2, plate_y0]) rsq(plate_w, plate_y1 - plate_y0, plate_r);
for (y = key_y)
translate([-sw_hole / 2, y - sw_hole / 2]) rsq(sw_hole, sw_hole, plate_r);
}
}

module plate_3d() {
translate([0, 0, plate_bot]) linear_extrude(plate_t) plate_2d();
}

// ---------- 組立確認 ----------
module assembly() {
color("DimGray", 0.35) body();
color("Gray") bottom();
color("ForestGreen") translate([-pcb_w / 2, pcb_y0, pcb_bot]) cube([pcb_w, pcb_l, pcb_t]);
color("SteelBlue") translate([-xiao_w / 2, xiao_y0, xiao_bot]) cube([xiao_w, xiao_l, xiao_t]);
color("Red")
for (p = bat_xy)
translate([p[0] - bat_pad[0] / 2, p[1] - bat_pad[1] / 2, xiao_bot - 0.1])
cube([bat_pad[0], bat_pad[1], 0.1]);
color("Silver") translate([-usb_w / 2, xiao_y0 - usb_protrude, xiao_top]) cube([usb_w, usb_depth, usb_h]);
color("Orange") translate([-8.5, key_y[0] - 7, bottom_t + 0.3]) cube([17, 50, 4]);
color("LightGray") plate_3d();
color("DarkSlateGray") translate([-9, enc_y - 9, pcb_top]) cube([18, 18, 2.5]);
color("Gainsboro")
translate([0, enc_y, top_z + wheel_above_top - 6])
rotate([0, 90, 0]) cylinder(d = 12, h = 10, center = true);
for (y = key_y)
color("WhiteSmoke")
hull() {
translate([-9.05, y - 9.05, plate_top + 5.0]) cube([18.1, 18.1, 0.1]);
translate([-6.25, y - 6.25, plate_top + keytop_above_plate - 0.1]) cube([12.5, 12.5, 0.1]);
}
for (p = foot_pos)
color("Black") translate([p[0], p[1], -foot_h]) cylinder(d = foot_d, h = foot_h);
}

// ---------- 出力 ----------
if (part == "assembly") assembly();
else if (part == "body") body();
else if (part == "bottom") bottom();
else if (part == "spacer") spacer();
else if (part == "plate2d") plate_2d();
else if (part == "plate3d") plate_3d();
