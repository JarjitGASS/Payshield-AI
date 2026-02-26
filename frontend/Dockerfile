FROM node:20-alpine AS node-base

WORKDIR /app

COPY package*.json ./

FROM node-base AS dev

RUN npm install

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

FROM node-base AS builder

ARG VITE_API_URL=""
ENV VITE_API_URL=$VITE_API_URL

RUN npm ci

COPY . .

RUN npm run build   # outputs to /app/dist

FROM nginx:1.27-alpine AS production

RUN rm /etc/nginx/conf.d/default.conf

COPY nginx.conf /etc/nginx/conf.d/default.conf

COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -qO- http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
