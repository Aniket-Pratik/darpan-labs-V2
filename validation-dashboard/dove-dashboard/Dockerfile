# Dove Validation Dashboard — static Vite app served by `serve`
FROM node:20-alpine AS base

# --- Dependencies stage ---
FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci

# --- Build stage ---
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# --- Production stage ---
FROM base AS runner
WORKDIR /app
ENV NODE_ENV=production

# Install only `serve` in the runtime image — no source, no dev deps
RUN npm install --global serve@14.2.6

COPY --from=builder /app/dist ./dist

EXPOSE 3000

# Railway injects $PORT dynamically; serve it with SPA fallback (-s).
# Shell form required for ${PORT:-3000} expansion — do not convert to exec form.
CMD ["sh", "-c", "serve dist -s -l tcp://0.0.0.0:${PORT:-3000}"]
