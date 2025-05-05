FROM node:20-bullseye AS builder
WORKDIR /app
COPY package.json package-lock.json* yarn.lock* ./
RUN if [ -f yarn.lock ]; then yarn install --frozen-lockfile; else npm ci; fi
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install --user --no-cache-dir -r requirements.txt
COPY . .
RUN if [ -f "webpack.config.js" ]; then npm run build; fi

FROM python:3.10-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
ENV PATH=/root/.local/bin:$PATH
COPY --from=builder /app .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt
RUN useradd -m appuser
USER appuser
LABEL maintainer="inhouse-dev-team"
LABEL app.version="1.0"
LABEL app.description="Custom In-House Node + Python Hybrid"
LABEL app.source="https://github.com/YourOrg/YourRepo"
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s CMD curl -f http://localhost:8000/health || exit 1
EXPOSE 8000
CMD ["python", "app.py"]
