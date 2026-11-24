# 最終段階：ZMK設定一式（2026-11-24受領）

- ファイル一式は ~/workspace/macropad/zmk-config/ にツリー再現済み（build.yml / build.yaml / zephyr/module.yml / config/west.yml・mpad.conf・mpad.keymap / boards/shields/mpad/ の5ファイル）
- ZMK v0.3固定（Zephyr 3.5、board=seeeduino_xiao_ble）。GitHubに置けばActionsでUF2がビルドされる。settings_reset UF2も同時生成
- overlayのピン割り当てはB案接続表と一致をMuse確認済み（KEY1 P0.29 / KEY2 P0.04 / KEY3 P0.05 / KEY4 P0.03 / ENC_SW P1.13 / ENC_A P1.15 / ENC_B P0.28）
- キーマップ：KEY1=Ctrl+C、KEY2=Ctrl+V、KEY3=Ctrl+Z、KEY4=Ctrl+Y（暫定）、ENC短押し=ミュート、回転=音量、押しながら回転=スクロール。SYSコンボ（KEY1+KEY4保持→KEY2=&bootloader、KEY3=BT_CLR、ENC押下=再起動）
- 電池残量レポート有効、30分でディープスリープ、送信出力は既定0dBm（技適の空中線電力が未確認のため+8dBm化は要確認と注意あり）
- 初回書き込みは組立前にXIAO単体で行う（組立後はボタンに触れない）。組立後のブートローダ入りはキーコンボ or パッド17-18ショート×2
- 実機調整値：ENC_SWAP_AB（方向）、ENC_DETENTS=24暫定（CKW12のクリック数）、スクロール量、tapping-term 200ms、combo timeout 80ms

## 天秤の確認事項（§9）
1. 4つ目のキー：暫定Ctrl+Y。候補 Ctrl+Y / Ctrl+X / Win+Shift+S / Ctrl+S ← ユーザー判断
2. ブートローダコンボの操作感（KEY1+KEY4保持→KEY2）
3. CKW12の1回転クリック数（実機確認、暫定24）

## 残作業（設計の外）
- PCBの配線（現状は配置済み・未配線）→ DRC → Gerber出力 → JLCPCB発注
- 筐体STL/DXFは case_out/ に出力済み → JLC3DP発注
- 部品手配（XIAO・CKW12・スイッチ・キーキャップ・電池・ピンヘッダ等）
