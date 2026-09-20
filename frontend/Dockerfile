# Build and execute only on AWS.
FROM node:22-bookworm-slim AS build
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --ignore-scripts --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM nginx:1.28-alpine AS runtime
RUN apk add --no-cache ca-certificates
COPY frontend/nginx.conf /etc/nginx/app.conf.template
COPY --chmod=755 frontend/40-runtime-config.sh /docker-entrypoint.d/40-runtime-config.sh
COPY --from=build /web/dist /usr/share/nginx/html
EXPOSE 80
