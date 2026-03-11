import time
import random
import requests

API_URL = 'http://api:5000'


def main():
    """
    Productor de eventos sintéticos.
    Simula un cliente que envía POST al API REST para crear órdenes.
    Corresponde al componente "productor eventos sintéticos" del diagrama.
    """
    print(" [Productor] Iniciando productor de eventos sintéticos...")
    print(" [Productor] Esperando a que el API esté listo...")

    # Esperar a que el API esté disponible
    for attempt in range(30):
        try:
            requests.get(f"{API_URL}/orders", timeout=2)
            print(" [Productor] API conectado!")
            break
        except Exception:
            time.sleep(2)
    else:
        print(" [Productor] ERROR: No se pudo conectar al API")
        return

    # -------------------------------------------------------
    # Paso 1: Enviar varios POST para crear órdenes
    # -------------------------------------------------------
    print("\n" + "=" * 50)
    print(" FASE 1: Creando órdenes (POST asíncrono)")
    print("=" * 50)

    task_ids = []

    for i in range(5):
        sensor_data = f"Sensor IoT #{i + 1} - Temperatura: {random.uniform(20, 35):.1f}°C"

        response = requests.post(
            f"{API_URL}/orders",
            json={'data': sensor_data}
        )

        if response.status_code == 202:
            task_id = response.json()['task_id']
            task_ids.append(task_id)
            print(f" [→] Enviado: {sensor_data}")
            print(f"     TaskId: {task_id} (HTTP 202 Accepted)")
        else:
            print(f" [!] Error enviando orden: {response.status_code}")

        time.sleep(1)

    # -------------------------------------------------------
    # Paso 2: Consultar el estado de los tasks (GET Tasks/TaskId)
    # -------------------------------------------------------
    print("\n" + "=" * 50)
    print(" FASE 2: Consultando estado de tasks")
    print("=" * 50)

    time.sleep(5)  # Esperar a que los consumers procesen

    for task_id in task_ids:
        response = requests.get(f"{API_URL}/tasks/{task_id}")
        if response.status_code == 200:
            task = response.json()
            print(f" [?] Task {task['task_id'][:8]}... → Status: {task['status']}")

    # -------------------------------------------------------
    # Paso 3: Consultar todas las órdenes (GET Orders)
    # -------------------------------------------------------
    print("\n" + "=" * 50)
    print(" FASE 3: Consultando órdenes creadas (GET /orders)")
    print("=" * 50)

    response = requests.get(f"{API_URL}/orders")
    if response.status_code == 200:
        orders = response.json()
        print(f" [i] Total de órdenes: {len(orders)}")
        for order in orders:
            print(f"     Orden #{order['order_id']}: {order['data']}")

    # -------------------------------------------------------
    # Paso 4: Eliminar una orden (DELETE asíncrono)
    # -------------------------------------------------------
    print("\n" + "=" * 50)
    print(" FASE 4: Eliminando una orden (DELETE asíncrono)")
    print("=" * 50)

    if response.status_code == 200 and len(orders) > 0:
        order_to_delete = orders[0]['order_id']
        response = requests.delete(f"{API_URL}/orders/{order_to_delete}")

        if response.status_code == 202:
            delete_task_id = response.json()['task_id']
            print(f" [x] Solicitada eliminación de orden #{order_to_delete}")
            print(f"     TaskId: {delete_task_id} (HTTP 202 Accepted)")

            # Esperar y verificar
            time.sleep(5)
            response = requests.get(f"{API_URL}/tasks/{delete_task_id}")
            if response.status_code == 200:
                task = response.json()
                print(f" [?] Task de eliminación → Status: {task['status']}")

    # -------------------------------------------------------
    # Paso 5: Verificar órdenes restantes
    # -------------------------------------------------------
    print("\n" + "=" * 50)
    print(" FASE 5: Verificando órdenes restantes")
    print("=" * 50)

    response = requests.get(f"{API_URL}/orders")
    if response.status_code == 200:
        orders = response.json()
        print(f" [i] Total de órdenes restantes: {len(orders)}")
        for order in orders:
            print(f"     Orden #{order['order_id']}: {order['data']}")

    print("\n [Productor] Demostración completada!")


if __name__ == '__main__':
    main()
