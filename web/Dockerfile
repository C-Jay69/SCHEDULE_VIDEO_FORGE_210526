FROM node:20-alpine AS base

WORKDIR /app
# Build context is the repo root (matches api/Dockerfile + worker/Dockerfile).
COPY web/package.json web/package-lock.json* ./
# Use npm ci when a lockfile is present for reproducible builds; fall back to
# npm install otherwise.
RUN npm ci --no-audit --no-fund || npm install --no-audit --no-fund

FROM base AS builder
COPY web/ .
# NEXT_PUBLIC_* values are inlined into the client bundle at BUILD time, so they
# must be provided here (via docker build --build-arg or compose build.args) —
# runtime env vars are ignored by the browser bundle and would cause a
# server/client hydration mismatch. Empty by default => same-origin /api/*
# (proxied by Caddy).
ARG NEXT_PUBLIC_API_URL=
ARG NEXT_PUBLIC_APP_URL=
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_APP_URL=$NEXT_PUBLIC_APP_URL
# API_URL drives the server-side /api/* rewrite in next.config.js, which is
# also compiled into the build — bake it for the target backend.
ARG API_URL=http://api:8000
ENV API_URL=$API_URL
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
