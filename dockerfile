# python:3.11のイメージをベースにする
FROM python:3.11-buster

# pythonの出力表示をDockerに合わせる
ENV PYTHONUNBUFFERED=1

# 作業ディレクトリを指定
WORKDIR /src

# pipを使ってpoetryをインストール
RUN pip install poetry

# pyproject.tomlとpoetry.lockをコピー
COPY pyproject.toml* poetry.lock* ./

# 作業ディレクトリを再度指定
WORKDIR /src

# poetryでライブラリをインストール
# 仮想環境をプロジェクト内に作成失敗する場合はFalseに変更
RUN poetry config virtualenvs.in-project true 
RUN if [ -f pyproject.toml ]; then poetry install --no-root; fi

# vicornのサーバーを立ち上げる
ENTRYPOINT [ "poetry", "run", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--reload" ]