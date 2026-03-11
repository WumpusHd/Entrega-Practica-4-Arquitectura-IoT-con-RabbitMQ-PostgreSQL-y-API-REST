-- Tabla de Tasks: almacena el estado de cada operación asíncrona
CREATE TABLE IF NOT EXISTS tasks (
    task_id UUID PRIMARY KEY,
    operation VARCHAR(20) NOT NULL,      
    status VARCHAR(50) NOT NULL DEFAULT 'pending', 
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Orders: almacena las órdenes creadas
CREATE TABLE IF NOT EXISTS orders (
    order_id SERIAL PRIMARY KEY,
    data TEXT,
    task_id UUID REFERENCES tasks(task_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
