# Stage 1: Build React frontend
FROM node:20-slim AS frontend
WORKDIR /web
COPY web/package.json web/package-lock.json* ./
RUN npm install
COPY web/ .
RUN npm run build

# Stage 2: Python backend
FROM python:3.12-slim
WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY . .
COPY --from=frontend /web/dist /app/web/dist
RUN pip install --no-cache-dir -e .

EXPOSE 8000
CMD ["sentinelops"]
