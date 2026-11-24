// File: mpad_case.scad
// 縦長BTマクロパッド 筐体・底板・プレート・ヘッダスペーサー（B案）
// 座標系: x=幅（中心0）、y=長手（上端外面=0、下端へ+）、z=高さ（底板下面=0）
// ※ y を「下へ+」としているため、OpenSCAD の上面ビューでは上下が反転して見える

/* [出力するパーツ] */
part = "assembly"; // [assembly, body, bottom, spacer, plate2d, plate3d]

/* [ID42 合わせ（実測後に変更）] */
id42_plate_top_from_desk = 16.9;  // 机面→プレート上面
foot_h = 1.5;
foot_d = 8.0;

/* [XIAO（実測後に変更）] */
usb_protrude = 1.0;
usb_w = 8.94;
usb_h = 3.2;
usb_depth = 7.35;
xiao_w = 17.8;
xiao_l = 21.0;
xiao_t = 1.6;
xiao_gap = 4.0;
relief_y0 = 11.0;     // 底板の逃げ（XIAO 裏面パッド19/20の位置で調整）
relief_y1 = 21.0;
relief_w = 11.0;
relief_d = 1.0;

/* [外形] */
L = 111.7;
W = 24.0;
R_out = 3.0;
wall_s = 2.1;
wall_e = 2.0;
skin = 0.8;
usb_wall = 0.8;

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
boss_from_end = 3.6;
boss_d = 6.2;
insert_hole_d = 3.3;
insert_depth = 4.5;
screw_d = 2.4;
cbore_d = 4.2;
cbore_h = 1.2;
tab_x = 7.0;
tab_w = 4.0;
tab_t = 1.0;
tab_len = 1.2;
tab_z0 = 0.5;

/* [プレート] */
plate_w = 19.4;
plate_t = 1.5;
sw_hole = 14.0;
plate_r = 0.5;

/* [外観用の推定値] */
keytop_above_plate = 13.0;
wheel_above_top = 5.0;

$fn = 48;

// ---------- 導出値 ----------
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

key_y = [for (i = [1:4]) enc_y + pitch * i];
plate_y0 = key_y[0] - 9.275;
plate_y1 = key_y[3] + 10.175;
slot_y0 = key_y[0] - 8.275;
slot_y1 = key_y[3] + 8.275;

in_w = W - 2 * wall_s;
boss_y = L - boss_from_end;

bp_w = in_w - 0.3;
bp_y0 = wall_e + 0.15;
bp_y1 = L - wall_e - 0.15;

rail_x0 = 8.9;
rail_x1 = 9.7;
rail_y0 = key_y[0] - 9.0;
rail_y1 = key_y[3] + 9.0;
rail_top = pcb_bot - poron;

stop_y0 = xiao_y0 + xiao_l + 0.2;
lead_y1 = key_y[0] - 5.0;

foot_pos = [[-6, 6.5], [6, 6.5], [-6, L - 13.5], [6, L - 13.5]];

// ---------- 検査 ----------
if (extra < 0)
    echo(str("[注意] 目標より ", -extra, " mm 高い。ゴム足を薄くしてください"));
echo(str("全長=", L, " 本体高さ(ゴム足込み)=", top_z + foot_h,
         " プレート上面(机から)=", plate_top + foot_h,
         " キートップ推定(机から)=", plate_top + keytop_above_plate + foot_h));
assert(plate_y1 < boss_y - boss_d / 2 - 0.3, "プレートが下端ボスに当たる");
assert(pcb_y0 + pcb_l < boss_y - boss_d / 2 - 0.3, "基板が下端ボスに当たる");
assert(enc_y - 7.5 - 1.0 - usb_back >= 0.5, "CKW12 の A/B/C ピンが USB-C に近すぎる");
assert(enc_y - enc_open / 2 > wall_e + 1.0, "CKW12 開口が上端壁に近すぎる");

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
            translate([sx * tab_x - (tab_w + 0.4) / 2, wall_e - tab_len - 0.1, tab_z0 - 0.2])
                cube([tab_w + 0.4, tab_len + 0.2, tab_t + 0.4]);
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
                translate([sx * tab_x - tab_w / 2, bp_y0 - tab_len, tab_z0])
                    cube([tab_w, tab_len + 0.01, tab_t]);
            // 基板受けレール（上に PORON 0.5）
            for (sx = [-1, 1])
                translate([sx > 0 ? rail_x0 : -rail_x1, rail_y0, bottom_t - 0.01])
                    cube([rail_x1 - rail_x0, rail_y1 - rail_y0, rail_top - bottom_t + 0.01]);
            // XIAO 後端ストッパー（中央は電池リードの通り道）
            for (sx = [-1, 1])
                translate([sx > 0 ? 2.5 : -7.5, stop_y0, bottom_t - 0.01])
                    cube([5.0, 1.2, xiao_top - bottom_t + 0.01]);
        }
        // ねじ穴＋座ぐり
        for (sx = [-1, 1])
            translate([sx * boss_x, boss_y, -0.01]) {
                cylinder(d = screw_d, h = bottom_t + 0.02);
                cylinder(d = cbore_d, h = cbore_h);
            }
        // ゴム足くぼみ
        for (p = foot_pos)
            translate([p[0], p[1], -0.01])
                cylinder(d = foot_d + 0.2, h = 0.5);
        // XIAO 裏面パッドの逃げ
        translate([-relief_w / 2, relief_y0, bottom_t - relief_d])
            cube([relief_w, relief_y1 - relief_y0, relief_d + 0.01]);
        // 電池リード溝
        translate([-2, relief_y1 - 0.01, bottom_t - relief_d])
            cube([4, lead_y1 - relief_y1, relief_d + 0.01]);
    }
}

// ---------- ヘッダスペーサー（1.5mm ×2） ----------
module spacer() {
    for (i = [0, 1])
        translate([i * 5, 0, 0])
            difference() {
                translate([-1.3, -1.27, 0]) cube([2.6, 17.78, 1.5]);
                for (k = [0:6])
                    translate([0, k * 2.54, -0.01]) cylinder(d = 1.2, h = 1.52);
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
}

// ---------- 出力 ----------
if (part == "assembly") assembly();
else if (part == "body") body();
else if (part == "bottom") bottom();
else if (part == "spacer") spacer();
else if (part == "plate2d") plate_2d();
else if (part == "plate3d") plate_3d();