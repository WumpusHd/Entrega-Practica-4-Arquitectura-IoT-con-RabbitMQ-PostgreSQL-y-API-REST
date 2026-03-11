import json
import time
import pika
import psycopg2


def get_db_connection():
    """Crea y retorna una conexión a PostgreSQL."""
    return psycopg2.connect(
        host='postgres',
        database='iot_db',
        user='user',
        password='password'
    )


def callback(ch, method, properties, body):
    """
    Callback que se ejecuta cuando llega un mensaje a la cola post_queue.
    1. Marca el Task como 'processing'
    2. Simula trabajo (sleep)
    3. Crea la orden en la BD
    4. Marca el Task como 'completed'
    """
    message = json.loads(body.decode())
    task_id = message['task_id']
    data = message['data']

    print(f" [Consumer POST] Recibido task: {task_id}")

    conn = get_db_connection()
    cur = conn.cursor()

    # Actualizar task a 'processing'
    cur.execute("UPDATE tasks SET status = %s WHERE task_id = %s", ('processing', task_id))
    conn.commit()

    # Simular tiempo de procesamiento (como si fuera una operación pesada)
    time.sleep(2)

    # Crear la orden en la tabla orders
    cur.execute(
        "INSERT INTO orders (data, task_id) VALUES (%s, %s)",
        (data, task_id)
    )

    # Actualizar task a 'completed' (Update TaskId en el diagrama)
    cur.execute("UPDATE tasks SET status = %s WHERE task_id = %s", ('completed', task_id))
    conn.commit()

    cur.close()
    conn.close()

    print(f" [Consumer POST] Task {task_id} completado - Orden creada")

    # Confirmar que el mensaje fue procesado (ACK manual)
    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    credentials = pika.PlainCredentials('user', 'password')
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbitmq', credentials=credentials))
    channel = connection.channel()

    # Declarar exchange y cola
    channel.exchange_declare(exchange='orders', exchange_type='direct')
    channel.queue_declare(queue='post_queue', durable=True)
    channel.queue_bind(exchange='orders', queue='post_queue', routing_key='post')

    # Prefetch = 1: No enviar más de un mensaje al worker hasta que termine el actual
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='post_queue', on_message_callback=callback)

    print(' [*] Consumer POST esperando mensajes... Presiona CTRL+C para salir')
    channel.start_consuming()


if __name__ == '__main__':
    main()
