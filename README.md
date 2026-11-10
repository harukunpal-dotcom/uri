# URI System Monitor

Ubuntu / Linux 向けの、パソコンの状態をリアルタイムで確認できるデスクトップアプリです。

## 機能

- CPU 使用率
- メモリ使用率と使用量
- ホームディスクの使用率と空き容量
- パソコンの稼働時間
- 1秒ごとの自動更新

## 必要なもの

- Python 3
- Tkinter

## Ubuntuでの起動方法

ターミナルで次のコマンドを実行します。

```bash
sudo apt update
sudo apt install python3-tk
```

このリポジトリをダウンロードして、フォルダ内で次を実行します。

```bash
python3 main.py
```

## 仕組み

追加のPythonライブラリは使いません。Linuxの `/proc` 情報とPython標準ライブラリを使って情報を取得します。

## 注意

このアプリはLinux向けです。CPU・メモリ・ディスクの値はシステム情報を読み取って表示します。設定変更やファイル削除などの操作は行いません。
