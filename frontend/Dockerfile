# Frontend Dockerfile - Build & Serve
FROM node:20-alpine AS builder

WORKDIR /app

# Dependencias
COPY package.json package-lock.json* ./
RUN npm install

# Código fuente
COPY . .

# Build de producción
RUN npm run build

# Servir con nginx
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
