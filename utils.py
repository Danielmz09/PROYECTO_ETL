import pandas as pd
import numpy as np
import json
import random

def generar_datos():
    # Ventas
    ventas = pd.DataFrame({
        "id_transaccion": range(1, 1001),
        "id_cliente": np.random.randint(1, 300, 1000),
        "monto": np.random.randint(50, 5000, 1000),
        "fecha": pd.date_range(start="2023-01-01", periods=1000, freq="H"),
        "id_tienda": np.random.randint(1, 10, 1000)
    })
    ventas.to_csv("data/ventas.csv", index=False)

    # Inventario (sucio)
    inventario = pd.DataFrame({
        "producto": ["Producto_" + str(i) for i in range(500)],
        "precio": np.random.choice([None, *np.random.randint(10, 1000, 500)], 500),
        "categoria": np.random.choice(["mx", "México", "mex", None], 500)
    })

    # duplicados
    inventario = pd.concat([inventario, inventario.sample(50)])
    inventario.to_csv("data/inventario.csv", index=False)

    # Perfiles (JSON)
    perfiles = []
    for i in range(300):
        perfiles.append({
            "id_cliente": i,
            "edad": random.randint(18, 60),
            "ingresos": random.randint(5000, 50000)
        })

    with open("data/perfiles.json", "w") as f:
        json.dump(perfiles, f)

    # Logs
    with open("data/logs.txt", "w") as f:
        for i in range(2000):
            f.write(f"ERROR {random.randint(100,500)} tiempo:{random.random()}\n")

    print("Datos generados")