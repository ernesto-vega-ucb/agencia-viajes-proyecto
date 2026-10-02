# Agencia de Viajes — Sistema de Reservas de Paquetes Turísticos (Monorepo)

Skeleton inicial de un sistema de reservas para una agencia de viajes, organizado como
**monorepo** con **pnpm workspaces + Turborepo**, backend transaccional en **Java/Spring Boot**,
servicio de **búsqueda NLP + scraping** en **Python/FastAPI**, frontend web en **React + TypeScript +
Tailwind CSS**, app móvil en **React Native + Expo (TypeScript)** y autenticación externa **OIDC/OAuth2 (Keycloak)**.

---

## 1. Árbol de directorios

```
agencia-viajes-proyecto/
├── package.json                     # Workspace raíz (scripts turbo, docker)
├── pnpm-workspace.yaml              # Definición de workspaces
├── turbo.json                       # Pipeline de tareas (dev/build/lint/test)
├── docker-compose.yml               # PostgreSQL + Keycloak + servicios + web
├── .env.example                     # Variables compartidas del entorno
├── .gitignore
├── .nvmrc                           # Node 20
├── keycloak/
│   └── import/
│       └── realm-export.json        # Realm "agencia-viajes" (clients, roles, demo user)
│
├── apps/
│   └── web/                         # Frontend React + TS + Tailwind (Vite)
│       ├── package.json
│       ├── vite.config.ts
│       ├── tsconfig*.json
│       ├── eslint.config.js
│       ├── index.html
│       ├── Dockerfile
│       ├── nginx.conf               # SPA + proxy estático
│       ├── .env.example
│       └── src/
│           ├── main.tsx
│           ├── App.tsx              # Definición de rutas
│           ├── index.css            # Tailwind v4 (@theme)
│           ├── config/env.ts
│           ├── types/domain.ts      # Modelos compartidos (package, booking...)
│           ├── lib/
│           │   ├── api.ts           # bookingApi + searchApi (HTTP + Bearer)
│           │   ├── auth.tsx         # AuthProvider OIDC (oidc-client-ts)
│           │   └── cart.ts          # Carrito en localStorage
│           ├── components/
│           │   └── Layout.tsx       # Header/nav/footer con estado de sesión
│           └── pages/
│               ├── HomePage.tsx
│               ├── SearchPage.tsx   # Buscador NLP
│               ├── PackageDetailPage.tsx
│               ├── CheckoutPage.tsx
│               ├── AccountPage.tsx  # Panel de usuario + sugerencias
│               └── CallbackPage.tsx # Callback OIDC
│   └── mobile/                      # App móvil React Native + Expo SDK 57 (TypeScript)
│       ├── package.json             # @agencia/mobile
│       ├── app.json                 # scheme agenciaviajes, plugins, cleartext en dev
│       ├── App.tsx                  # Navegación (React Navigation) + puerta de auth
│       ├── index.ts
│       ├── expo-env.d.ts            # Tipos de Expo (process.env.EXPO_PUBLIC_*)
│       ├── .env.example             # EXPO_PUBLIC_* (host emulador / IP LAN)
│       └── src/
│           ├── config/env.ts        # URLs de API, OIDC y scheme
│           ├── theme.ts             # Colores y espaciado
│           ├── types/
│           │   ├── domain.ts        # Modelos compartidos con apps/web
│           │   └── navigation.ts    # Tipos de rutas del stack
│           ├── lib/
│           │   ├── api.ts           # bookingApi + searchApi (fetch + Bearer)
│           │   └── auth.tsx         # AuthProvider OIDC (expo-auth-session + PKCE + secure-store)
│           ├── components/
│           │   └── PackageCard.tsx
│           └── screens/
│               ├── LoginScreen.tsx         # Login con Keycloak + redirect URI debug
│               ├── PackagesScreen.tsx      # Listado + buscador NLP con sugerencias
│               ├── PackageDetailScreen.tsx # Fechas/viajeros + crear reserva
│               └── MyBookingsScreen.tsx    # Reservas activas + logout
│
├── services/
│   ├── booking-core/                # Backend transaccional (Spring Boot 3.4 / Java 21)
│   │   ├── pom.xml
│   │   ├── Dockerfile               # Multi-stage (maven -> jre)
│   │   ├── .env.example
│   │   └── src/
│   │       ├── main/resources/
│   │       │   ├── application.yml
│   │       │   └── db/migration/
│   │       │       └── V1__init.sql # Flyway (schema PostgreSQL)
│   │       └── main/java/com/agencia/bookingcore/
│   │           ├── BookingCoreApplication.java
│   │           ├── config/
│   │           │   ├── SecurityConfig.java    # Resource server OAuth2 JWT + CORS
│   │           │   └── DataSeeder.java        # Paquetes demo
│   │           ├── domain/
│   │           │   ├── entity/       # AppUser, TourPackage, Booking, BookingItem
│   │           │   ├── enums/        # BookingStatus
│   │           │   └── repository/   # JPA repositories
│   │           ├── dto/              # Records request/response validados
│   │           ├── service/          # BookingService, TourPackageService, PricingService
│   │           ├── error/            # Excepciones + GlobalExceptionHandler
│   │           └── web/controller/   # BookingController, TourPackageController, Health
│   │
│   └── search-ai/                    # Búsqueda NLP + scraping (FastAPI / Python 3.11+)
│       ├── pyproject.toml
│       ├── Dockerfile
│       ├── .env.example
│       ├── app/
│       │   ├── main.py               # App FastAPI + CORS + create_all
│       │   ├── config.py             # pydantic-settings
│       │   ├── db.py                 # SQLAlchemy engine/session
│       │   ├── models.py             # ScrapedPackage, UserHistory
│       │   ├── schemas.py            # Pydantic models
│       │   ├── api/
│       │   │   ├── search.py         # /search/suggestions, /recommendations, /history
│       │   │   └── scrape.py         # /scrape/run, /scrape/tasks, /scrape/packages
│       │   ├── services/
│       │   │   ├── catalog.py        # Cliente del catálogo (booking-core) + fallback
│       │   │   ├── nlp.py            # Análisis NLP (stopwords ES, TF-IDF, sinónimos)
│       │   │   ├── recommender.py    # Recomendación según historial del usuario
│       │   │   └── scraper.py        # Parser HTML estilo Booking.com (BeautifulSoup)
│       │   ├── tasks/scrape_task.py  # Ejecución asíncrona del scraping
│       │   └── data/mock_booking.html# Fixture local sin red
│       └── tests/test_services.py    # Pruebas unitarias (scraper + NLP)
└── README.md
```

---

## 2. Stack y decisiones técnicas

| Capa | Tecnología | Puerto |
|------|-----------|--------|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS v4, React Router 7, oidc-client-ts | `5173` |
| App móvil | React Native 0.86, Expo SDK 57, TypeScript, React Navigation 7, expo-auth-session (OIDC + PKCE) | Expo (Metro) |
| Backend transaccional | Java 21, Spring Boot 3.4, Spring Data JPA, Flyway, OAuth2 Resource Server | `8081` |
| Búsqueda / NLP / Scraping | Python 3.11+, FastAPI, scikit-learn (TF-IDF), BeautifulSoup | `8082` |
| Base de datos | PostgreSQL 16 | `5432` |
| Autenticación externa | Keycloak 25 (OIDC/OAuth2). Intercambiable por Auth0/Supabase Auth | `8080` |

- **Monorepo:** `pnpm` workspaces + `turbo`. Los paquetes de `apps/*` se gestionan con pnpm;
  los servicios Java/Python se construyen vía Docker (Maven/pip dentro de su imagen).
- **Comunicación** `search-ai → booking-core`: el catálogo de paquetes se consume por HTTP
  (`GET /api/v1/packages`) con caché en memoria y *fallback* local para desarrollo sin red.
- **Autenticación:** los servicios confían en el token JWT emitido por Keycloak (`issuer-uri` /
  `jwks-uri`). El frontend redirige a Keycloak; `booking-core` valida el Bearer token y extrae
  `realm_access.roles` → `ROLE_*` con `@PreAuthorize`.
- **App móvil (Expo):** Authorization Code + PKCE con `expo-auth-session`; la sesión se guarda
  en `expo-secure-store` (iOS Keychain / Android Keystore) y se renueva con el refresh token.
  Por defecto apunta al host del emulador (`10.0.2.2` en Android, `localhost` en iOS) y se
  ajusta con variables `EXPO_PUBLIC_*`.

---

## 3. Guía de inicio rápido

### 3.1 Prerrequisitos

- Docker 24+ con Docker Compose v2
- Node.js 20+ y pnpm 9+ (`npm i -g pnpm`)
- JDK 21 y Maven 3.9+ (solo para desarrollar `booking-core` sin Docker)
- Python 3.11+ (solo para desarrollar `search-ai` sin Docker)

### 3.2 Levantar todo el entorno (recomendado)

```bash
# 1. Copiar variables de entorno raíz
Copy-Item .env.example .env          # o:  cp .env.example .env

# 2. Construir y arrancar PostgreSQL, Keycloak, booking-core, search-ai y web
docker compose up -d --build
```

Una vez arriba:

| Endpoint | URL |
|----------|-----|
| Frontend | http://localhost:5173 |
| Keycloak Admin Console | http://localhost:8080 (`admin` / `admin`) |
| Keycloak Realm | http://localhost:8080/realms/agencia-viajes/.well-known/openid-configuration |
| booking-core OpenAPI/HW | http://localhost:8081/api/v1/health |
| search-ai docs (Swagger) | http://localhost:8082/docs |
| App móvil | `pnpm dev:mobile` en `apps/mobile` (Expo) | Expo Go / dev build |

Usuario demo pre-cargado en Keycloak: **`demo@agencia.test`** / **`Demo123!`** (rol `customer`).

Para ver el comportamiento de roles (`AGENT`/`ADMIN`) puedes crear usuarios en la consola de
Keycloak o asignar roles al usuario demo en `Realm roles → Assigned roles`.

### 3.3 Desarrollo local (hot reload, sin/replicando contenedores)

```bash
# Frontend con Vite (espera servicios en 8080/8081/8082)
cd apps/web
pnpm install
pnpm dev

# Backend core (requiere PostgreSQL arriba; usa la imagen del compose o local)
cd services/booking-core
mvn spring-boot:run

# Servicio de IA (crea venv del proyecto Python 3.11+)
cd services/search-ai
python -m venv .venv && .venv\Scripts\activate   # Windows
# o: source .venv/bin/activate                    # Linux/macOS
pip install -e .
uvicorn app.main:app --reload --port 8082
```

> En Windows usa `Activate.ps1` (`powershell`) desde `.venv\Scripts`.

### 3.4 Flujo de prueba end-to-end

```bash
# 1) Paquetes públicos (sin token)
curl http://localhost:8081/api/v1/packages

# 2) Búsqueda con NLP (usa el catálogo de booking-core)
curl "http://localhost:8082/api/v1/search/suggestions?query=playa%20caribe&user_id=u-001"

# 3) Disparar scraping del fixture (sin red) y consultar resultados
curl -X POST http://localhost:8082/api/v1/scrape/run -H "Content-Type: application/json" -d "{}"
curl http://localhost:8082/api/v1/scrape/packages

# 4) Obtener un access token desde Keycloak (client public, direct access grant)
TOKEN=$(curl -s -X POST "http://localhost:8080/realms/agencia-viajes/protocol/openid-connect/token" \
  -d "client_id=agencia-web" \
  -d "username=demo@agencia.test" -d "password=Demo123!" \
  -d "grant_type=password" | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# 5) Crear una reserva (autenticado)
curl -X POST http://localhost:8081/api/v1/bookings \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d "{\"items\":[{\"packageId\":1,\"startDate\":\"$(date -d '+14 days' +%F)\",\"travelers\":2}]}"

# 6) Ver reservas del usuario
curl http://localhost:8081/api/v1/bookings/me -H "Authorization: Bearer $TOKEN"
```

**Nota sobre `startDate`:** debe coincidir con una de las fechas del paquete
(`GET /api/v1/packages`), que el seeder genera relativas a *hoy*.

### 3.5 App móvil (React Native + Expo)

Con el stack de Docker arriba (3.2), desde la raíz del monorepo:

```bash
cd apps/mobile
npm install          # o: pnpm --filter @agencia/mobile install
npx expo start       # recuerda: pnpm dev:mobile en la raíz también funciona
```

- **Emulador Android:** la app apunta por defecto a `10.0.2.2` (host) para las API (`8081/8082/8080`).
- **Simulador iOS:** por defecto usa `localhost`.
- **Dispositivo físico (Expo Go):** define tu IP LAN en `apps/mobile/.env` (ver `.env.example`),
  p. ej. `EXPO_PUBLIC_API_HOST=192.168.1.50`.
- Usuario demo: `demo@agencia.test` / `Demo123!` (rol `customer`).

> **Redirect URI en Expo Go:** el login OIDC devuelve el control a la app con
> `agenciaviajes://oauth` en dev builds, o con una URL `exp://…` en Expo Go. El realm ya acepta
> `agenciaviajes://oauth` y `exp://*`; si tu Expo Go produce otro valor, añádelo en
> Keycloak → Clients → agencia-web → *Valid redirect URIs* (la pantalla de login muestra el
> valor exacto que usa tu app).

> **Nota sobre el puerto de Metro:** `expo start` usa `8081`, ocupado aquí por `booking-core`,
> por lo que Metro elegirá el siguiente puerto libre (8082/8083…). No afecta a la app: las
> llamadas a `booking-core`/`search-ai` van al `8081`/`8082` del host, no al puerto de Metro.

> **Probar en el navegador (Expo web):** al ejecutar `npx expo start` y pulsar `w`, la app corre
> en el navegador y las llamadas a Keycloak/APIs son *cross-origin*. El realm ya tiene CORS
> abierto para desarrollo (`webOrigins: ["*"]`) y, para que el callback OIDC sea válido, ejecuta
> con puerto fijo `npx expo start --web --port 8083` (aceptados `http://localhost:8083/*` y
> `http://<tu-ip>:8083/*`). En web la sesión se guarda en `localStorage` (SecureStore no existe
> en navegador); en iOS/Android se usa SecureStore.

> **Puerto 8080 ocupado (404 en la IP LAN):** si `http://localhost:8080` responde pero tu IP LAN
> da `404 CORS missing`, otro proceso está tomando `0.0.0.0:8080` (típico: Apache `PEMHTTPD` de
> EDB PostgreSQL PEM). Libera el puerto y reinicia Keycloak: `docker compose restart keycloak`.

---

## 4. Autenticación externa (OIDC con Keycloak)

- El realm `agencia-viajes` se importa automáticamente al arrancar Keycloak
  (`KC_BOOTSTRAP_*` / `--import-realm`) en su **propia base de datos**
  (`agencia_keycloak`; la de la aplicación es `agencia_viajes`, compartida por
  booking-core y search-ai). El realm se exporta con `sslRequired: none` (solo para
  desarrollo local desde dispositivos/emuladores; en producción usa HTTPS y `external`).
- Cliente público **`agencia-web`**: flujo Authorization Code + PKCE tanto en la web
  (`oidc-client-ts`) como en la app móvil (`expo-auth-session`). Redirects permitidos:
  `http://localhost:5173/*`, `agenciaviajes://oauth` y `exp://*`. Incluye *direct access
  grant* para pruebas con `curl`.
- Cliente confidencial **`booking-core`**: solo *service account* para futuras llamadas
  service-to-service (máquina a máquina).
- Roles por defecto: `customer`, `agent`, `admin`. Usuario demo:
  `demo@agencia.test` / `Demo123!` (rol `customer`).
- Usuario administrador local de Keycloak: `admin` / `admin`.

> **Ojo con el claim `sub` (Keycloak 25):** desde KC25 el `sub` de los access tokens
> se añade por un *protocol mapper* del client scope `basic`. Ese scope no se crea al
> importar un realm desde JSON (solo en migraciones de base de datos), por eso el
> cliente `agencia-web` exportado ya incluye el mapper `sub` (`oidc-sub-mapper`).
> Si creas realms nuevos/formato Keycloak 26, asegúrate de incluir `basic` en los
> `defaultClientScopes` o el mapper del `sub`, o tu microservicio no verá `jwt.sub`.

Para cambiar de proveedor (Auth0, Supabase) solo es necesario:

1. Actualizar `VITE_OIDC_*` en `apps/web/.env` y en `.env`:
   `KEYCLOAK_ISSUER_URI` (issuer público) y `KEYCLOAK_JWKS_URI` (URL de las claves).
2. Publicar el cliente con `redirect_uri = http://localhost:5173/callback`.
3. `booking-core` sigue funcionando porque valida JWT por `issuer-uri` + JWKS.

## 5. Endpoints principales

### booking-core (`:8081/api/v1`)

| Método | Ruta | Acceso |
|--------|------|--------|
| GET | `/health` | público |
| GET | `/packages` , `/packages/{id}` | público |
| POST / PUT / DELETE | `/packages[...]` | `ROLE_ADMIN` |
| POST | `/bookings` | autenticado |
| GET | `/bookings/me` , `/bookings/{id}` | autenticado (propietario) |
| POST | `/bookings/{id}/confirm` | `ROLE_AGENT` o `ROLE_ADMIN` |
| POST | `/bookings/{id}/pay` , `/bookings/{id}/cancel` | propietario |

### search-ai (`:8082/api/v1`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/health` | healthcheck |
| GET | `/search/suggestions?query=...&user_id=...` | búsqueda NLP + sugerencias |
| GET | `/recommendations/{user_id}` | recomendación por historial |
| POST | `/history` | registrar evento de usuario |
| POST | `/scrape/run` | lanzar scraping (fuente HTML o fixture) |
| GET | `/scrape/tasks/{task_id}` | estado de la tarea |
| GET | `/scrape/packages` | paquetes scrapeados |

## 6. Comandos útiles del monorepo

```bash
pnpm install           # instalar dependencias de los workspaces (apps/*)
pnpm dev               # turbo run dev (levantar todo lo que tenga script dev)
pnpm dev:web           # solo el frontend web (Vite)
pnpm dev:mobile        # solo la app móvil (Expo/Metro)
pnpm build             # turbo run build
pnpm lint              # turbo run lint
pnpm typecheck         # turbo run typecheck
pnpm docker:up         # docker compose up -d --build
pnpm docker:down       # docker compose down
```

## 7. Roadmap de integraciones sugeridas

- **Pagos reales:** conectar el `POST /bookings/{id}/pay` a un PSP (Stripe/Checkout).
- **Auth service-to-service:** cliente `booking-core` con *client credentials* para que
  `search-ai` registre historial con identidad verificada.
- **Eventos asíncronos:** publicar `BookingCreated`/`BookingPaid` a un broker (Kafka/RabbitMQ)
  para notificaciones, CRM y reporting.
- **Scraping productivo:** añadir Playwright para fuentes JS y un *scheduler* (Celery) para
  periodicidad; evitar scraping real de portales sin permiso de su `robots.txt`.
- **Embeddings:** sustituir TF-IDF por embeddings (sentence-transformers + pgvector) para
  mejorar relevancia de la búsqueda semántica.