# Práctica 4 - Arquitectura IoT con RabbitMQ, PostgreSQL y API REST

## Arquitectura

```
Productor ──POST──→ API REST ──(3)──→ RabbitMQ ──→ Consumer POST    ──→ DB (crear orden)
                       │                    └──→ Worker DELETE    ──→ DB (eliminar orden)
                       │                                                    │
                       ←──── 202 + TaskId ──────────────────── Update TaskId ┘
                       │
Actor ─── GET Task/TaskId ──→ API REST ──(2)──→ DB (consultar estado)
       └─ GET Orders ───────→ API REST ──(2)──→ DB (listar órdenes)
```

## Componentes

| Servicio           | Puerto | Descripción                                        |
|--------------------|--------|----------------------------------------------------|
| **RabbitMQ**       | 5672 / 15672 | Message broker + interfaz web de administración |
| **PostgreSQL**     | 5432   | BD con tablas `tasks` y `orders`                  |
| **API REST**       | 5000   | Flask API - Recibe peticiones, publica a RabbitMQ |
| **Consumer POST**  | -      | Cola que consume mensajes y crea órdenes          |
| **Worker DELETE**  | -      | Cola que consume mensajes y elimina órdenes       |
| **Producer**       | -      | Genera eventos sintéticos (POST al API)           |

## Endpoints del API

| Método   | Ruta                 | Tipo       | Descripción                        |
|----------|----------------------|------------|------------------------------------|
| `POST`   | `/orders`            | Asíncrono  | Crear orden → retorna 202 + TaskId |
| `GET`    | `/tasks/<TaskId>`    | Síncrono   | Consultar estado de un task        |
| `GET`    | `/orders`            | Síncrono   | Listar todas las órdenes           |
| `PUT`    | `/orders/<order_id>` | Síncrono   | Actualizar datos de una orden      |
| `DELETE` | `/orders/<order_id>` | Asíncrono  | Eliminar orden → retorna 202 + TaskId |

## Cómo ejecutar

### 1. Levantar todos los servicios
```bash
docker-compose up -d --build
```

### 2. Ver los logs de todos los contenedores
```bash
docker-compose logs -f
```

### 3. Ver logs de un servicio específico
```bash
docker-compose logs -f producer         # Ver output del productor
docker-compose logs -f consumer_post    # Ver output del consumer POST
docker-compose logs -f consumer_delete  # Ver output del worker DELETE
docker-compose logs -f api              # Ver output del API
```

### 4. Acceder a las interfaces web
- **RabbitMQ Management**: http://localhost:15672 (user/password)
- **API REST**: http://localhost:5000

### 5. Probar manualmente con curl (como el Actor del diagrama)
```bash
# Crear una orden (POST asíncrono)
curl -X POST http://localhost:5000/orders -H "Content-Type: application/json" -d "{\"data\": \"Sensor temperatura: 25.5C\"}"

# Consultar estado de un task
curl http://localhost:5000/tasks/{TASK_ID}

# Listar todas las órdenes
curl http://localhost:5000/orders

# Actualizar una orden (PUT)
curl -X PUT http://localhost:5000/orders/1 -H "Content-Type: application/json" -d "{\"data\": \"Dato actualizado\"}"

# Eliminar una orden (DELETE asíncrono)
curl -X DELETE http://localhost:5000/orders/1
```

### 6. Conectarse a PostgreSQL con DBeaver
- **Host**: localhost
- **Puerto**: 5432
- **Base de datos**: iot_db
- **Usuario**: user
- **Contraseña**: password

### 7. Detener y limpiar
```bash
docker-compose down --rmi all -v
```

---

## Ejercicios anteriores de clase (send/receive y emit/receive logs)

```bash
# Levantar servicios
docker-compose up -d --build

# Ejecutar ejercicios anteriores con el python-client
docker exec -it practice4-python-client-1 python receive_logs.py
docker exec -it practice4-python-client-1 python emit_logs.py
```