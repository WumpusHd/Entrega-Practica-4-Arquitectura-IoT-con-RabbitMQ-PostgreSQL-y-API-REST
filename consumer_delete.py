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
    Callback que se ejecuta cuando llega un mensaje a la cola delete_queue.
    1. Marca el Task como 'processing'
    2. Simula trabajo (sleep)
    3. Elimina la orden de la BD
    4. Marca el Task como 'completed'
    """
    message = json.loads(body.decode())
    task_id = message['task_id']
    order_id = message['order_id']

    print(f" [Worker DELETE] Recibido task: {task_id} - Eliminar orden #{order_id}")

    conn = get_db_connection()
    cur = conn.cursor()

    # Actualizar task a 'processing'
    cur.execute("UPDATE tasks SET status = %s WHERE task_id = %s", ('processing', task_id))
    conn.commit()

    # Simular tiempo de procesamiento
    time.sleep(2)

    # Eliminar la orden de la tabla orders
    cur.execute("DELETE FROM orders WHERE order_id = %s RETURNING order_id", (order_id,))
    deleted = cur.fetchone()

    if deleted:
        # Actualizar task a 'completed' (Update TaskId en el diagrama)
        cur.execute("UPDATE tasks SET status = %s WHERE task_id = %s", ('completed', task_id))
        print(f" [Worker DELETE] Task {task_id} completado - Orden #{order_id} eliminada")
    else:
        # La orden no existía
        cur.execute("UPDATE tasks SET status = %s WHERE task_id = %s", ('failed', task_id))
        print(f" [Worker DELETE] Task {task_id} falló - Orden #{order_id} no encontrada")

    conn.commit()
    cur.close()
    conn.close()

    # Confirmar que el mensaje fue procesado (ACK manual)
    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    credentials = pika.PlainCredentials('user', 'password')
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbitmq', credentials=credentials))
    channel = connection.channel()

    # Declarar exchange y cola
    channel.exchange_declare(exchange='orders', exchange_type='direct')
    channel.queue_declare(queue='delete_queue', durable=True)
    channel.queue_bind(exchange='orders', queue='delete_queue', routing_key='delete')

    # Prefetch = 1
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='delete_queue', on_message_callback=callback)

    print(' [*] Worker DELETE esperando mensajes... Presiona CTRL+C para salir')
    channel.start_consuming()


if __name__ == '__main__':
    main()
