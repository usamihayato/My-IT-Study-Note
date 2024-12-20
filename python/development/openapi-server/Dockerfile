ARG registry=acrprivatepocje001
# ACRのプライベートPythonイメージを使用
FROM ${registry}.azurecr.io/base/python:3.8-slim-bullseye

# 非rootユーザーの作成
RUN useradd -m -u 1000 dmadmin

WORKDIR /usr/src/app

# アプリケーションコードのコピー
COPY --chown=dmadmin:dmadmin src/app/ .
COPY --chown=dmadmin:dmadmin src/lib/ ./lib/

# requirements.txtがある場合のみコピーしてインストール
COPY --chown=dmadmin:dmadmin requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 非rootユーザーに切り替え
USER dmadmin

# 環境変数の設定
ENV PYTHONPATH="/usr/src/app:${PYTHONPATH}"

# uWSGIの起動
CMD ["uwsgi", "--ini", "./uwsgi.ini"]