# 軽量なPython 3.11イメージを使用
FROM python:3.11-slim

# コンテナ内の作業ディレクトリを設定
WORKDIR /app

# 必要なパッケージリストを先にコピーしてインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Botのコードをコンテナにコピー
COPY . .

# Botの実行
CMD ["python", "main.py"]
