# C-Cultivator 🚀 (42 Tokyo向け ゲリラ自動採点Discord Bot)

C-Cultivator（シー・カルティベーター）は、42の学生コミュニティ（Discord）向けに開発された、**「ピア・ラーニング」と「ゲーム性」を極限まで高める自動採点Bot**です。

毎日ランダムな時間に「ゲリラ課題」が投下され、制限時間10分以内にC言語の課題を解き、`Norminette` のチェックをくぐり抜けた者だけが、他のクリア者のコードを閲覧できる「秘密の感想戦チャンネル」に招待されます。

## ✨ 主な機能 (Features)

* **⏰ ゲリラ投下システム (BeReal-style Notifications)**
  * 毎日特定の時間帯（10:00〜21:00など）のどこかで、突然課題が投下されます。
* **⚖️ 自動採点＆Normチェック (Auto Grading)**
  * 提出された `.c` ファイルは `Wandbox API` を通じて即座にコンパイル・実行・テストケース検証が行われます。
  * 42公式のコーディング規約チェッカー `Norminette` もコンテナ内で裏側で走り、厳密に判定します。
* **🔐 クリア者限定「感想戦」 (Secret Peer-Learning Channel)**
  * テストとNormをノーミスで突破したユーザーは、自動生成された鍵付きチャンネルに招待されます。
  * 一般ユーザーからは一切見えない空間で、「どんなコード書いた？」「そこポインタでいけるのか！」といった熱い議論（ピア・ラーニング）が交わせます。
* **🏆 スピードランキング (Speed Ranking)**
  * 課題ごとに、クリアタイムが早かったユーザーのランキングを表示し、競争心を煽ります。

## 🛠 技術スタック (Tech Stack)

* **Language:** Python 3.11+
* **Library:** `discord.py`
* **Database:** SQLite3
* **Infrastructure:** Docker / Docker Compose
* **External APIs/Tools:** Wandbox API, `norminette` (Python package)

## 🚀 セットアップと起動方法 (Installation & Usage)

Dockerがインストールされている環境であれば、すぐに起動できます。

### 1. リポジトリのクローン
```bash
git clone [https://github.com/あなたのユーザー名/C-Cultivator.git](https://github.com/あなたのユーザー名/C-Cultivator.git)
cd C-Cultivator
