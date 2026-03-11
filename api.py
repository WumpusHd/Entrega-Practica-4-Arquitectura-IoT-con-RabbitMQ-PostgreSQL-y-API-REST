import uuid
import json
import pika
import psycopg2
from flask import Flask, request, jsonify

app = Flask(__name__)

# ============================================================
# Conexiones a PostgreSQL y RabbitMQ
# ============================================================

def get_db_connection():
    """Crea y retorna una conexión a PostgreSQL."""
    return psycopg2.connect(
        host='postgres',
        database='iot_db',
        user='user',
        password='password'
    )


def publish_to_rabbitmq(routing_key, message):
    """Publica un mensaje a RabbitMQ con la routing_key indicada."""
    credentials = pika.PlainCredentials('user', 'password')
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbitmq', credentials=credentials))
    channel = connection.channel()

    # Exchange de tipo 'direct' para enrutar por routing_key
    channel.exchange_declare(exchange='orders', exchange_type='direct')

    channel.basic_publish(
        exchange='orders',
        routing_key=routing_key,
        body=json.dumps(message),
        properties=pika.BasicProperties(delivery_mode=2)  # Mensaje persistente
    )
    connection.close()


# ============================================================
# Endpoints del API REST
# ============================================================

@app.route('/orders', methods=['POST'])
def create_order():
    """
    POST Asíncrono: Crea un Task con estado 'pending',
    publica el mensaje a la cola 'post_queue' vía RabbitMQ
    y retorna 202 con el TaskId.
    """
    data = request.json.get('data', '') if request.json else ''
    task_id = str(uuid.uuid4())

    # 1. Registrar el Task en la BD con status 'pending'
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tasks (task_id, operation, status) VALUES (%s, %s, %s)",
        (task_id, 'POST', 'pending')
    )
    conn.commit()
    cur.close()
    conn.close()

    # 2. Publicar mensaje a RabbitMQ (routing_key='post' → cola post_queue)
    publish_to_rabbitmq('post', {'task_id': task_id, 'data': data})

    print(f" [API] POST /orders → TaskId: {task_id}")
    return jsonify({'task_id': task_id}), 202


@app.route('/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    """
    GET Tasks/<<TaskId>>: Permite al Actor consultar
    el estado de una operación asíncrona.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT task_id, operation, status, created_at FROM tasks WHERE task_id = %s",
        (task_id,)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return jsonify({'error': 'Task not found'}), 404

    return jsonify({
        'task_id': str(row[0]),
        'operation': row[1],
        'status': row[2],
        'created_at': str(row[3])
    })


@app.route('/orders', methods=['GET'])
def get_orders():
    """
    GET Orders: Retorna todas las órdenes creadas.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT order_id, data, task_id, created_at FROM orders ORDER BY order_id")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    orders = [{
        'order_id': r[0],
        'data': r[1],
        'task_id': str(r[2]),
        'created_at': str(r[3])
    } for r in rows]

    return jsonify(orders)


@app.route('/orders/<int:order_id>', methods=['PUT'])
def update_order(order_id):
    """
    PUT: Actualiza los datos de una orden existente (síncrono).
    """
    data = request.json.get('data', '') if request.json else ''

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE orders SET data = %s WHERE order_id = %s RETURNING order_id",
        (data, order_id)
    )
    updated = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if not updated:
        return jsonify({'error': 'Order not found'}), 404

    print(f" [API] PUT /orders/{order_id} → Updated")
    return jsonify({'order_id': order_id, 'data': data, 'status': 'updated'})


@app.route('/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    """
    DELETE Asíncrono: Crea un Task con estado 'pending',
    publica el mensaje a la cola 'delete_queue' vía RabbitMQ
    y retorna 202 con el TaskId.
    """
    task_id = str(uuid.uuid4())

    # 1. Registrar el Task en la BD
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tasks (task_id, operation, status) VALUES (%s, %s, %s)",
        (task_id, 'DELETE', 'pending')
    )
    conn.commit()
    cur.close()
    conn.close()

    # 2. Publicar mensaje a RabbitMQ (routing_key='delete' → cola delete_queue)
    publish_to_rabbitmq('delete', {'task_id': task_id, 'order_id': order_id})

    print(f" [API] DELETE /orders/{order_id} → TaskId: {task_id}")
    return jsonify({'task_id': task_id}), 202


# ============================================================
# Iniciar el servidor
# ============================================================

if __name__ == '__main__':
    print(" [API] Starting REST API on port 5000...")
    app.run(host='0.0.0.0', port=5000)
