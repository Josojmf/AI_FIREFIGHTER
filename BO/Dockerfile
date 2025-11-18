# Build stage
FROM node:18-alpine AS build

WORKDIR /app

RUN apk add --no-cache curl

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 3001

HEALTHCHECK --interval=30s --timeout=5s --retries=5 \
  CMD curl -f http://localhost:3001 || exit 1

CMD ["nginx", "-g", "daemon off;"]
