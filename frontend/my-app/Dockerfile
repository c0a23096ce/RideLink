FROM node:18-alpine
WORKDIR /app

# 必要なファイルを先にコピー
COPY package.json yarn.lock ./

# 依存関係をインストール（ここが重要！）
RUN yarn install --frozen-lockfile --network-timeout 1000000

# ソースコードをコピー
COPY . .

# Next.jsアプリを起動
CMD ["yarn", "dev"]
