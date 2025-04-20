# ベースイメージ（軽量な Node.js）
FROM node:20-alpine

# 作業ディレクトリ作成
WORKDIR /app

# パッケージ関連を先にコピーしてキャッシュ活用
COPY package.json yarn.lock ./

# 依存関係インストール
RUN yarn install --frozen-lockfile

# ソースコードをコピー
COPY . .

# 開発サーバー起動
CMD ["yarn", "dev"]
