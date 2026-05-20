import pandas as pd
import numpy as np
import json
import os
import random
from datetime import datetime, timedelta


def generar_datos():
    os.makedirs("data", exist_ok=True)
    os.makedirs("output", exist_ok=True)

    # VENTAS
    ventas = pd.DataFrame({
        "id_transaccion": range(1, 5001),
        "id_cliente": np.random.randint(1, 1001, 5000),
        "monto": np.random.randint(100, 5000, 5000),
        "fecha": [
            (datetime.now() - timedelta(days=random.randint(1, 365))).strftime("%d/%m/%Y")
            for _ in range(5000)
        ],
        "id_tienda": np.random.randint(1, 11, 5000)
    })

    # duplicados intencionales
    ventas = pd.concat([ventas, ventas.iloc[:100]])

    ventas.to_csv("data/ventas.csv", index=False)

    # INVENTARIO SUCIO
    inventario = pd.DataFrame({
        "producto_id": range(1, 1001),
        "stock": np.random.randint(1, 500, 1000),
        "precio": np.random.randint(10, 2000, 1000)
    })

    # 10% nulos
    inventario.loc[:100, "stock"] = np.nan

    # duplicados
    inventario = pd.concat([inventario, inventario.iloc[:50]])

    inventario.to_csv("data/inventario.csv", index=False)

    # PERFILES (JSON / NoSQL)
    perfiles = []

    for i in range(1, 1001):
        perfiles.append({
            "id_cliente": i,
            "edad": random.randint(18, 65),
            "ingresos": random.randint(5000, 50000),
            "puntos_lealtad": random.randint(0, 3000),
            "pais": random.choice(["MX", "mex", "México", "USA"])
        })

    with open("data/perfiles.json", "w", encoding="utf-8") as f:
        json.dump(perfiles, f, indent=4)

    # LOGS TXT
    with open("data/logs.txt", "w") as f:
        for _ in range(2000):
            estado = random.choice(["OK", "ERROR", "TIMEOUT"])
            tiempo = random.randint(20, 800)
            f.write(f"estado={estado}, tiempo={tiempo}ms\n")

    print("Datos generados correctamente.")