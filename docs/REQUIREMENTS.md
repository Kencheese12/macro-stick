# マクロパッド 要件メモ

決定日: 2026-11-24（はまけん承認）

## 概要
- 用途: PC作業用マクロパッド
- 形態: Keychron Nape Pro のような細長い縦型ストリップ。部品は全て縦一列配置
- ゼロから新規設計（既存 focuspad はベースにしない）

## 構成（上から順）
1. CKW12（遊舎工房 水平ロータリーエンコーダ、プッシュスイッチ付きホイールモジュール）×1 — 一番上
2. Gateron 静音赤軸（MX互換）×4 — 縦一列
   - 取り付け: ホットスワップソケット想定（仮置き）

## 電源・接続
- 電池駆動、Bluetooth無線（USBハブは付けない。前回の試作にはあった）
- MCU: Seeed XIAO nRF52840（BLE＋充電回路内蔵、ZMKファーム想定）
- 充電は USB-C（XIAO のポート）想定

## 製造
- 基板: JLCPCB。部品はできるだけ LCSC で揃えて JLCPCB の実装サービスで載せる（XIAO nRF52840 と CKW12 は手はんだ想定）
- ケース: 天秤に設計してもらい、印刷は JLC3DP、素材は PA12-S

## 進め方
- 基本設計: GMO天秤AI Biz（Claude Opus系）
- 検証: Muse が出力を取り込み、KiCad 10.0.8（~/workspace/kicad10/kicad10-cli.sh）で ERC/DRC・整合性チェック・3Dレンダリング確認

## 参考
- 前回の試作の残骸: 天秤AIのチャット「USBハブ付き〜」内にあり（回収予定）
  - 注意: 前回分には RP2040 チップ直付け等の記述があるかもしれないが、今回は採用しない（MCU は XIAO nRF52840 で確定）。はまけん指示「気にせず」
- CKW12 設計者向けガイド: https://github.com/yushakobo/build-documents/blob/master/Accessory_parts/CKW12/for_developers/readme.md
- CKW12 商品ページ: https://shop.yushakobo.jp/products/ckw12
