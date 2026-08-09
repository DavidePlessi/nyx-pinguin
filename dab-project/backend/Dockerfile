# ==========================================
# STAGE 1: Build Vue Frontend
# ==========================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

# Copia package.json e package-lock.json
COPY frontend/package*.json ./
RUN npm ci

# Copia il resto del codice e builda
COPY frontend/ ./
RUN npm run build

# ==========================================
# STAGE 2: Build Python Backend
# ==========================================
FROM python:3.11-slim
WORKDIR /app

# Non scrivere pyc e non bufferizzare output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Installa le dipendenze Python
COPY backend/requirements.txt /app/backend/
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copia il codice Python
COPY backend/ /app/backend/

# Copia la cartella dist del frontend dallo stage precedente 
# e la posiziona dove FastAPI se l'aspetta (nella cartella padre del backend)
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Esponi porta 8000
EXPOSE 8000

# Avvia FastAPI
WORKDIR /app/backend
CMD ["uvicorn", "main_api:app", "--host", "0.0.0.0", "--port", "8000"]
