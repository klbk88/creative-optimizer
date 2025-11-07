# 🚀 Быстрый старт UTM Tracking

Гайд по запуску проекта локально и на сервере.

---

## 📋 Что нужно установить

### Локальный запуск

```bash
# Проверь что установлено:
docker --version          # Docker 20.10+
docker-compose --version  # Docker Compose 1.29+
git --version            # Git 2.0+
```

**Не установлено?**

**macOS:**
```bash
brew install docker docker-compose git
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install docker.io docker-compose git
```

**Windows:**
- Скачать Docker Desktop: https://www.docker.com/products/docker-desktop

---

## 🏠 Локальный запуск (тест за 5 минут)

### Шаг 1: Склонировать репозиторий

```bash
git clone https://github.com/klbk88/utm-tracking.git
cd utm-tracking
```

---

### Шаг 2: Создать .env файл

```bash
cp .env.test .env
```

Или создай вручную файл `.env`:

```bash
# Database
DATABASE_URL=postgresql://utm_user:utm_password@postgres:5432/utm_tracking

# Redis
REDIS_URL=redis://redis:6379/0

# JWT
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production-min-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# Telegram Bot (опционально, можно оставить пустым)
TELEGRAM_BOT_TOKEN=
ADMIN_BOT_TOKEN=
ADMIN_IDS=

# OpenAI (опционально, для анализа креативов)
OPENAI_API_KEY=
```

---

### Шаг 3: Запустить Docker Compose

```bash
docker-compose up
```

**Что запустится:**
- FastAPI (port 8000) - API сервер
- PostgreSQL (port 5432) - База данных
- Redis (port 6379) - Кеш
- Prometheus (port 9090) - Метрики
- Grafana (port 3000) - Дашборды

**Первый запуск займет ~2-3 минуты** (скачивает Docker образы).

**Увидишь в логах:**
```
api_1         | INFO:     Uvicorn running on http://0.0.0.0:8000
postgres_1    | PostgreSQL init process complete; ready for start up.
redis_1       | Ready to accept connections
```

---

### Шаг 4: Открыть Swagger UI

Открой браузер: **http://localhost:8000/docs**

Увидишь интерактивную документацию API со всеми endpoints.

---

### Шаг 5: Создать тестового юзера

**Через Swagger UI:**

1. Найди endpoint `POST /api/v1/auth/register`
2. Нажми "Try it out"
3. Введи:

```json
{
  "email": "test@test.com",
  "password": "test123",
  "full_name": "Test User"
}
```

4. Нажми "Execute"

**Получишь ответ:**
```json
{
  "user_id": "uuid-123",
  "email": "test@test.com",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Скопируй `access_token`** - он понадобится!

---

### Шаг 6: Авторизоваться в Swagger

1. Нажми кнопку **"Authorize"** (замок) в правом верхнем углу Swagger
2. Введи: `Bearer YOUR_TOKEN_HERE` (замени на свой токен)
3. Нажми "Authorize"

Теперь все запросы будут авторизованы!

---

### Шаг 7: Протестировать Early Signals

**Создать креатив:**

`POST /api/v1/creative/creatives`

```json
{
  "name": "Test Video 1",
  "creative_type": "ugc",
  "product_category": "lootbox",
  "production_cost": 15000,
  "hook_type": "wait",
  "emotion": "excitement",
  "pacing": "fast",
  "test_phase": "micro_test"
}
```

**Запомни `creative_id` из ответа.**

---

**Анализ 24h:**

`POST /api/v1/creative/analyze-early-signals`

```json
{
  "creative_id": "ВАШ_UUID_СЮДА",
  "impressions": 500,
  "clicks": 20,
  "landing_views": 18,
  "landing_bounces": 6,
  "avg_time_on_page": 6.5,
  "conversions": 2
}
```

**Получишь:**
```json
{
  "signal": "strong_positive",
  "confidence": 0.75,
  "recommendation": "scale",
  "predicted_final_cvr": 0.12,
  "reasoning": "Score: 3 (3 positive, 0 negative). ✅ CTR 4.00% ...",
  "next_action": "🚀 Увеличить бюджет до $100-200. Predicted CVR: 12.0%"
}
```

**✅ Работает! API готов к использованию.**

---

### Шаг 8: Grafana (опционально)

Открой: **http://localhost:3000**

**Логин:** admin
**Пароль:** admin

**Импортировать дашборд:**
1. Идем в Dashboards → Import
2. Upload JSON file: `monitoring/grafana-dashboard.json`
3. Profit! Видишь метрики (пока пустые, нужны реальные данные)

---

## ⚠️ Частые проблемы

### Порт 8000 занят

```bash
# Найти что занимает порт
lsof -i :8000

# Убить процесс
kill -9 PID
```

Или в `docker-compose.yml` поменяй порт:
```yaml
ports:
  - "8001:8000"  # Теперь API на :8001
```

---

### PostgreSQL не стартует

```bash
# Удалить старые данные
rm -rf postgres_data/

# Рестарт
docker-compose down
docker-compose up
```

---

### Миграции не применились

```bash
# Войти в контейнер API
docker-compose exec api bash

# Применить миграции вручную
alembic upgrade head
```

---

## 🛑 Остановить все

```bash
# Остановить (данные сохранятся)
docker-compose down

# Остановить + удалить данные
docker-compose down -v
```

---

## ☁️ Серверный деплой (продакшн)

### Что нужно:

1. **VPS сервер** (любой):
   - Hetzner: €4.5/мес (CPX11)
   - DigitalOcean: $6/мес (Basic Droplet)
   - Vultr: $5/мес

2. **Домен** (опционально, можно по IP):
   - Namecheap: $1/год (.xyz)
   - Cloudflare: бесплатно (если домен есть)

---

### Быстрый деплой на VPS

**1. SSH на сервер:**

```bash
ssh root@YOUR_SERVER_IP
```

---

**2. Установить Docker:**

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Установить docker-compose
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

---

**3. Клонировать репозиторий:**

```bash
cd /opt
git clone https://github.com/klbk88/utm-tracking.git
cd utm-tracking
```

---

**4. Создать .env для продакшена:**

```bash
nano .env
```

**Важно поменять:**

```bash
# Безопасный JWT secret (32+ символов)
JWT_SECRET_KEY=your-real-super-secret-key-min-32-chars-random-string

# Безопасный пароль PostgreSQL
DATABASE_URL=postgresql://utm_user:СЛОЖНЫЙ_ПАРОЛЬ_СЮДА@postgres:5432/utm_tracking

# Выключить debug
DEBUG=false

# Твой домен (или IP)
API_HOST=your-domain.com
```

---

**5. Запустить:**

```bash
docker-compose up -d
```

Флаг `-d` = detached mode (в фоне).

---

**6. Проверить что работает:**

```bash
# Логи API
docker-compose logs -f api

# Статус контейнеров
docker-compose ps
```

Должно быть:
```
NAME                STATUS
utm-api-1          Up 30 seconds
utm-postgres-1     Up 30 seconds
utm-redis-1        Up 30 seconds
```

---

**7. Открыть порты в файрволе:**

```bash
# UFW (Ubuntu)
ufw allow 22    # SSH
ufw allow 80    # HTTP
ufw allow 443   # HTTPS
ufw allow 8000  # API (временно для теста)
ufw enable
```

---

**8. Проверить API:**

```bash
curl http://YOUR_SERVER_IP:8000/health

# Должно вернуть:
{"status": "ok"}
```

**✅ API работает на сервере!**

---

### Настройка Nginx + SSL (опционально, но рекомендуется)

**Зачем:**
- HTTPS (безопасно)
- Красивый URL (api.your-domain.com вместо IP:8000)
- TikTok webhook требует HTTPS

---

**1. Установить Nginx:**

```bash
apt install nginx certbot python3-certbot-nginx -y
```

---

**2. Создать конфиг Nginx:**

```bash
nano /etc/nginx/sites-available/utm-tracking
```

**Вставить:**

```nginx
server {
    listen 80;
    server_name your-domain.com;  # Твой домен или IP

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Grafana
    location /grafana/ {
        proxy_pass http://localhost:3000/;
    }

    # Prometheus
    location /prometheus/ {
        proxy_pass http://localhost:9090/;
    }
}
```

---

**3. Активировать конфиг:**

```bash
ln -s /etc/nginx/sites-available/utm-tracking /etc/nginx/sites-enabled/
nginx -t  # Проверить конфиг
systemctl restart nginx
```

---

**4. Получить SSL (если есть домен):**

```bash
certbot --nginx -d your-domain.com
```

Certbot автоматически настроит HTTPS!

---

**5. Проверить:**

```bash
curl https://your-domain.com/health

# Должно вернуть:
{"status": "ok"}
```

**✅ API доступен через HTTPS!**

---

## 🔄 Обновление на сервере

Когда есть новые изменения в репозитории:

```bash
cd /opt/utm-tracking

# Забрать изменения
git pull

# Рестарт контейнеров
docker-compose down
docker-compose up -d --build

# Проверить логи
docker-compose logs -f api
```

---

## 📊 Мониторинг на сервере

### Grafana

Открыть: `http://YOUR_IP:3000` (или `https://your-domain.com/grafana`)

**Логин:** admin
**Пароль:** admin (поменяй!)

---

### Prometheus

Открыть: `http://YOUR_IP:9090` (или `https://your-domain.com/prometheus`)

Можешь делать запросы:
```
utm_clicks_total
utm_conversions_total
creative_cvr{cluster_id="0"}
```

---

## 🎯 Итого

### Локальный тест (5 минут)
```bash
git clone https://github.com/klbk88/utm-tracking.git
cd utm-tracking
cp .env.test .env
docker-compose up
# Открыть http://localhost:8000/docs
```

### Серверный деплой (30 минут)
```bash
# На сервере:
cd /opt
git clone https://github.com/klbk88/utm-tracking.git
cd utm-tracking
nano .env  # Настроить
docker-compose up -d
ufw allow 8000
# Открыть http://SERVER_IP:8000/docs
```

### С Nginx + SSL (1 час)
```bash
# + к серверному деплою:
apt install nginx certbot -y
nano /etc/nginx/sites-available/utm-tracking
certbot --nginx -d your-domain.com
# Открыть https://your-domain.com/docs
```

---

## 📚 Дальше что?

**После запуска API:**

1. **Подключить TikTok:** Читай `UTM_MARKOV_WORKFLOW.md`
2. **Запустить микро-тесты:** Читай `EARLY_SIGNALS_WORKFLOW.md`
3. **Настроить Grafana:** Импортировать `monitoring/grafana-dashboard.json`
4. **Обучить модель:** `POST /api/v1/creative/train-markov-chain`

---

## 🆘 Помощь

**Проблемы с запуском?**

1. Проверь логи:
```bash
docker-compose logs api
docker-compose logs postgres
```

2. Рестарт:
```bash
docker-compose down
docker-compose up --build
```

3. Полная очистка:
```bash
docker-compose down -v
rm -rf postgres_data redis_data
docker-compose up
```

---

**Готово! API работает.** 🚀

Следующий шаг: Подключить TikTok и запустить первый микро-тест за $10.
