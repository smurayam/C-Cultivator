### README.md


# C-Cultivator

C-Cultivatorは、42の学生コミュニティにおけるピア・ラーニングの促進を目的とした、学習支援用のDiscord Botです。
指定された時間枠内でランダムにC言語の課題を出題し、提出されたコードの自動採点およびNorminetteによる静的解析を行います。すべての要件を満たしたユーザーのみを専用のコードレビューチャンネルへ招待する仕組みを提供します。

## 機能一覧 (Features)

* **ランダム出題システム**
  * 毎日指定した時間枠（例: 10:00〜21:00）の中で、ランダムな時刻に課題を通知します。
  * 課題の出題から一定時間（デフォルト: 10分間）を制限時間として設けています。
* **自動コンパイル・実行による採点**
  * `Wandbox API` を利用し、提出されたC言語のソースコード(`.c`)をコンテナ外部で安全にコンパイルおよび実行します。
  * 内部で保持しているテストケースと照合し、実行結果の正当性を自動で判定します。
* **Norminette 静的解析**
  * 42公式のコーディング規約チェッカーである `Norminette` をバックグラウンドで実行し、フォーマット違反の有無を検査します。
* **クリア者限定チャンネルの動的生成**
  * 実行テストとNorminetteの双方をクリアしたユーザーに対し、Discordの権限（Permissions）を動的に付与します。
  * 一般権限からは不可視となる専用チャンネルへ該当ユーザーを誘導し、参加者間でのコードの共有およびピア・ラーニングを促します。
* **ランキング機能**
  * 課題ごとに、出題から提出までのタイムを計測し、クリア者のスピードランキングを表示します。

## 技術スタック (Tech Stack)

* **言語:** Python 3.11+
* **ライブラリ:** `discord.py`
* **データベース:** SQLite3
* **インフラ:** Docker / Docker Compose
* **外部ツール/API:** Wandbox API, `norminette` (Python package)

## 導入手順 (Installation & Setup)

DockerおよびDocker Composeがインストールされている環境を前提とします。

### 1. リポジトリのクローン
```bash
git clone [https://github.com/YourUsername/C-Cultivator.git](https://github.com/YourUsername/C-Cultivator.git)
cd C-Cultivator

```

### 2. 環境変数の設定

プロジェクトのルートディレクトリに `.env` ファイルを作成し、Discord Developer Portalで取得したBotトークンを記述します。

```env
DISCORD_BOT_TOKEN=your_discord_bot_token_here

```

### 3. 通知先チャンネルの設定

`main.py` 内の定数 `ANNOUNCE_CHANNEL_ID` を、課題出題の通知を行いたいDiscordチャンネルのIDに変更してください。

```python
# main.py
ANNOUNCE_CHANNEL_ID = 123456789012345678

```

### 4. ビルドおよび起動

以下のコマンドを実行し、コンテナをビルド・起動します。初回起動時にSQLiteデータベースとテーブル群が自動で構築されます。

```bash
sudo docker compose up -d --build

```

## コマンド仕様 (Commands)

* `/start` : 現在アクティブな課題への挑戦を開始し、BotからDMで課題の詳細を受信します。
* `/submit [file.c]` : 解答となるC言語ファイルを添付して提出し、自動採点処理を実行します。
* `/ranking` : 現在のセッションにおけるクリアタイムのランキング一覧を出力します。
* `/test_alert` : **[管理者権限必須]** 通知システムを手動でトリガーし、新規セッションおよび専用チャンネルを生成します。
* `/ping` : Botの稼働状況およびレイテンシ（ms）を確認します。

## ディレクトリ構成 (Directory Structure)

```text
C-Cultivator/
├── docker-compose.yml   # コンテナオーケストレーション設定
├── Dockerfile           # 実行環境および依存パッケージの定義
├── requirements.txt     # Pythonパッケージリスト
├── main.py              # Botのメインロジックおよびコマンドルーティング
├── judge.py             # コンパイル・実行・Norminette判定ロジック
└── data/                # SQLiteデータベースファイル保存先 (Volume)

```

## ライセンス (License)

This project is licensed under the MIT License.

```
