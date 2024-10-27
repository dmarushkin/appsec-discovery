FROM node:16 as build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm install

COPY . .
RUN npm run build

FROM node:16

WORKDIR /app
COPY --from=build /app/build /app/build
RUN npm install -g serve
CMD ["serve", "-s", "build"]