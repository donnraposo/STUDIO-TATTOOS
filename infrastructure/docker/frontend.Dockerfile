FROM node:22-alpine AS base

WORKDIR /app

FROM base AS development

COPY frontend/package.json ./
RUN npm install

COPY frontend/ ./

EXPOSE 5173
CMD ["npm", "run", "dev"]

FROM base AS build

COPY frontend/package.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

FROM nginx:1.27-alpine AS production

COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
