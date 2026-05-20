import pandas as pd
import numpy as np
import json
from sklearn.preprocessing import MinMaxScaler
from sklearn.decomposition import PCA


# EXTRACCIÓN
def extraer():
    ventas = pd.read_csv("data/ventas.csv")
    inventario = pd.read_csv("data/inventario.csv")

    with open("data/perfiles.json", "r", encoding="utf-8") as f:
        perfiles = pd.DataFrame(json.load(f))

    with open("data/logs.txt", "r") as f:
        logs = f.readlines()

    return ventas, inventario, perfiles, logs


# TRANSFORMACIÓN
def transformar(ventas, inventario, perfiles):
    # LIMPIEZA
    ventas = ventas.drop_duplicates()
    inventario = inventario.fillna(0)

    # NORMALIZAR FECHAS
    ventas["fecha"] = pd.to_datetime(
        ventas["fecha"],
        format="%d/%m/%Y"
    )

    # LIMPIEZA DE STRINGS
    perfiles["pais"] = perfiles["pais"].replace({
        "mex": "México",
        "MX": "México"
    })

    # MERGE (LEFT JOIN)
    df = ventas.merge(
        perfiles,
        on="id_cliente",
        how="left"
    )

    # REGLAS DE NEGOCIO
    df["segmento_cliente"] = np.where(
        (df["monto"] > 1000) & (df["edad"] < 30),
        "Premium Joven",
        "Regular"
    )

    # MIN MAX SCALER
    scaler = MinMaxScaler()

    columnas_numericas = [
        "monto",
        "edad",
        "ingresos",
        "puntos_lealtad"
    ]

    df[columnas_numericas] = scaler.fit_transform(
        df[columnas_numericas]
    )

    # PCA
    pca = PCA(n_components=3)

    componentes = pca.fit_transform(
        df[columnas_numericas]
    )

    df["pca1"] = componentes[:, 0]
    df["pca2"] = componentes[:, 1]
    df["pca3"] = componentes[:, 2]

    return df


# CARGA
def cargar(df):
    df.to_csv(
        "output/data_master_clean.csv",
        index=False
    )

    print("Archivo final generado: output/data_master_clean.csv")