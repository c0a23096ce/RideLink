# python:3.11のイメージをベースにする
FROM python:3.11-buster

# pythonの出力表示をDockerに合わせる
ENV PYTHONUNBUFFERED=1

# 作業ディレクトリを指定
WORKDIR /app

# pipを使ってpoetryをインストール
RUN pip install poetry

# pyproject.tomlとpoetry.lockをコピー
COPY pyproject.toml* poetry.lock* ./

# poetryでライブラリをインストール
RUN if [ -f pyproject.toml ]; then poetry install --no-root || cat /src/poetry.lock; fi

# vicornのサーバーを立ち上げる
ENTRYPOINT ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--reload"]