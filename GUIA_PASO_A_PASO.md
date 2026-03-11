## Cómo ejecutar PASO A PASO (como en clase, terminal por terminal)

### Paso 1: Levantar la infraestructura
En la primera terminal:
```bash
docker-compose up -d --build
```
Esto levanta: RabbitMQ, PostgreSQL, y todos los contenedores en modo espera.

Verifica que estén corriendo:
```bash
docker-compose ps
```

### Paso 2: Abrir la interfaz de RabbitMQ
Abre el navegador en: http://localhost:15672
- Usuario: `user`
- Contraseña: `password`
Aquí podrás ver las colas `post_queue` y `delete_queue` en tiempo real.

### Paso 3: Iniciar el API REST (Terminal 1)
```bash
docker exec -it api_rest python api.py
```
Deberías ver: `[API] Starting REST API on port 5000...`

### Paso 4: Iniciar el Consumer POST (Terminal 2)
Abre una NUEVA terminal y ejecuta:
```bash
docker exec -it consumer_post python consumer_post.py
```
Deberías ver: `[*] Consumer POST esperando mensajes...`

### Paso 5: Iniciar el Worker DELETE (Terminal 3)
Abre OTRA terminal y ejecuta:
```bash
docker exec -it consumer_delete python consumer_delete.py
```
Deberías ver: `[*] Worker DELETE esperando mensajes...`

### Paso 6: Ejecutar el Productor (Terminal 4)
Abre OTRA terminal y ejecuta:
```bash
docker exec -it producer python producer.py
```
¡Aquí verás toda la demostración! Y en las otras terminales verás los mensajes siendo procesados.

### Paso 7: Probar manualmente con curl (Terminal 5 - como el Actor)
```bash
# Crear una orden
curl -X POST http://localhost:5000/orders -H "Content-Type: application/json" -d "{\"data\": \"Sensor IoT temperatura: 28.5C\"}"

# Copiar el task_id de la respuesta y consultar su estado
curl http://localhost:5000/tasks/PEGAR-TASK-ID-AQUI

# Ver todas las órdenes
curl http://localhost:5000/orders

# Eliminar una orden
curl -X DELETE http://localhost:5000/orders/1

# Verificar con DBeaver: conectarse a localhost:5432, db=iot_db, user/password
```

### Paso 8: Detener todo
```bash
docker-compose down --rmi all -v
```

---

## Resumen visual de terminales

```
Terminal 1 → docker exec -it api_rest python api.py           ← API REST
Terminal 2 → docker exec -it consumer_post python consumer_post.py  ← Consumer POST (cola)
Terminal 3 → docker exec -it consumer_delete python consumer_delete.py  ← Worker DELETE (cola)
Terminal 4 → docker exec -it producer python producer.py      ← Productor eventos
Terminal 5 → curl ... (pruebas manuales como Actor)           ← Actor
```
