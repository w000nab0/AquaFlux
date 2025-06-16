# AquaFlux/frontend/Dockerfile
FROM python:3.11-slim-bookworm

# 作業ディレクトリを設定
WORKDIR /app

# NiceGUIの依存関係をコピーしてインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# NiceGUIアプリケーションのコードをコピー
COPY . .

# NiceGUIがリッスンするポート
EXPOSE 8001

# アプリケーションの実行コマンド
CMD ["python", "main.py"]