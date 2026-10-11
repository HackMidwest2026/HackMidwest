# CityCare API + agents. Build from the repo root so the shared /data folder is in context:
#   docker build -f api/Dockerfile -t citycare-api .
FROM node:22-alpine AS deps
# Prisma's query engine uses the OpenSSL 3 libraries already in node:alpine (libssl3),
# so no apk install is needed (that would fail when Alpine's mirror is unreachable).
WORKDIR /app/api
COPY api/package.json api/package-lock.json ./
COPY api/prisma ./prisma
# postinstall runs `prisma generate`, building the database client from prisma/schema.prisma.
RUN npm ci --omit=dev

FROM node:22-alpine
ENV NODE_ENV=production \
    PORT=8080 \
    DATA_DIR=/app/data \
    STATE_DIR=/app/var
WORKDIR /app/api
COPY --from=deps /app/api/node_modules ./node_modules
COPY api/package.json ./
COPY api/prisma ./prisma
COPY api/src ./src
COPY data /app/data
RUN mkdir -p /app/var && chown -R node:node /app/var
USER node
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=5 \
  CMD wget -qO- http://127.0.0.1:8080/api/health >/dev/null || exit 1
CMD ["node", "src/server.js"]
