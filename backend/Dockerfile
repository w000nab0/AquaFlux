# Pythonの公式イメージをベースとして使うよ
# ここでPythonのバージョンを指定します。今回は3.11を使ってみましょう。
FROM python:3.11-slim-bullseye

# 作業ディレクトリを /app に設定するよ
# アプリのファイルは、この /app の中に置いていくことになります。
WORKDIR /app

# requirements.txt を /app にコピーするよ
# アプリが動くために必要なライブラリのリストです。
COPY requirements.txt .

# requirements.txt に書かれているライブラリをインストールするよ
# --no-cache-dir は、キャッシュを使わないでインストールすることで、イメージのサイズを小さくするおまじないです。
RUN pip install --no-cache-dir -r requirements.txt

# 現在のディレクトリのすべてのファイルを、Dockerイメージの /app にコピーするよ
# backendディレクトリの中身を全てコピーするイメージですね。
COPY . .

# Djangoアプリケーションを起動するコマンドを設定するよ
# これは仮のコマンドなので、後で変更するかもしれません。
# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]