# Build stage
FROM node:18-alpine AS builder
WORKDIR /app

# Adiciona utilitários para compilação caso existam dependências nativas
RUN apk add --no-cache libc6-compat

# Instala dependências (separado para cache da camada)
COPY package.json package-lock.json* ./
RUN npm ci

# Copia o código-fonte
COPY . .

# Argumentos de build para o Next.js
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

ARG NEXT_PUBLIC_TOKEN
ENV NEXT_PUBLIC_TOKEN=${NEXT_PUBLIC_TOKEN}

# Desabilita telemetria
ENV NEXT_TELEMETRY_DISABLED=1

# Compila o projeto (Standalone mode ativado automaticamente via next.config.mjs ou TS)
RUN npm run build

# Production stage
FROM node:18-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copia apenas os artefatos necessários
COPY --from=builder /app/public ./public
# Se usar a opção 'output: standalone' no next.config.ts, o nextjs cria um arquivo server.js
# Se não usar, executamos via npm start. Como o padrao nao usa standalone, copiaremos tudo:
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["npm", "start"]
