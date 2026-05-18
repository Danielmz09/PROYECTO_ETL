import pandas as pd
import numpy as np
import json
from sklearn.preprocessing import MinMaxScaler
from sklearn.decomposition import PCA

# EXTRACCIÓN
def extraer():
    ventas = pd.read_csv("data/ventas.csv")
    inventario = pd.read_csv("data/inventario.csv")

    with open("data/perfiles.json") as f:
        perfiles = pd.DataFrame(json.load(f))

    return ventas, inventario, perfiles


# TRANSFORMACIÓN
def transformar(ventas, inventario, perfiles):

    # LIMPIEZA
    inventario = inventario.drop_duplicates()
    inventario["precio"] = inventario["precio"].fillna(inventario["precio"].mean())

    # LIMPIEZA TEXTO
    inventario["categoria"] = inventario["categoria"].replace({
        "mx": "México",
        "mex": "México"
    })

    # NORMALIZACIÓN FECHAS
    ventas["fecha"] = pd.to_datetime(ventas["fecha"])

    # JOIN
    df = ventas.merge(perfiles, on="id_cliente", how="left")

    # REGLAS DE NEGOCIO
    df["segmento"] = np.where(
        (df["monto"] > 1000) & (df["edad"] < 30),
        "Premium Joven",
        "Regular"
    )

    # ESCALADO
    scaler = MinMaxScaler()
    df[["monto", "ingresos"]] = scaler.fit_transform(df[["monto", "ingresos"]])

    # PCA
    pca = PCA(n_components=2)
    df[["pca1", "pca2"]] = pca.fit_transform(df[["monto", "ingresos"]])

    return df


# CARGA
def cargar(df):
    df.to_csv("output/data_master_clean.csv", index=False)
    print("Archivo final generado")

if __name__ == "__main__":

    # EXTRAER
    ventas, inventario, perfiles = extraer()

    # TRANSFORMAR
    df_final = transformar(ventas, inventario, perfiles)

    # CARGAR
    cargar(df_final)