# macro-stick

縦型Bluetoothマクロパッドの設計データ一式。CKW12ホイールエンコーダ×1＋MXスイッチ×4の1列レイアウト、MCUは Seeed XIAO nRF52840 をエンコーダの下（基板裏面）に配置するB案。全長111.7mm。

## 中身

- `kicad/` — KiCad 10 基板データ
  - `mpad_b.kicad_pcb` — B案の基板（部品配置済み。配線はFreeroutingで実施）
  - `mpad_a.kicad_pcb` — A案（参考）
  - `lib/` — 自作フットプリント（mpad.pretty）とSeeed XIAOフットプリント
  - `gen_mpad_b.py` / `gen_mpad.py` — 基板生成スクリプト（KiCad同梱Pythonで実行）
- `case/mpad_case.scad` — 筐体・底板・プレート・スペーサーのOpenSCADデータ（part変数で切替、JLC3DP PA12-S想定）
- `zmk-config/` — ZMK v0.3用ファームウェア設定（このフォルダを独立リポジトリにするとGitHub ActionsでUF2がビルドされる）
- `docs/` — 要件と設計メモ

## キー割り当て

| 位置 | 割り当て |
|---|---|
| KEY1 | Ctrl+C |
| KEY2 | Ctrl+V |
| KEY3 | Ctrl+Z |
| KEY4 | Print Screen |
| エンコーダ回転 | 音量 |
| エンコーダ短押し | ミュート |
| エンコーダ押しながら回転 | スクロール |

設計：GMO天秤AI（基本設計）＋ Muse（KiCad/OpenSCAD検証）
