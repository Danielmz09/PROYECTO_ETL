import pandas as pd
import os
from sqlalchemy import create_engine
from utils import cargar_perfiles_json


def ejecutar_etl():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # conexión MySQL
    engine = create_engine(
        "mysql+pymysql://root:@localhost/etl_proyecto"
    )

    # SQL
    ventas_df = pd.read_sql(
        "SELECT * FROM ventas_historicas",
        engine
    )

    # rutas
    ruta_perfiles = os.path.join(
        BASE_DIR, "data", "perfiles.json"
    )

    ruta_inventario = os.path.join(
        BASE_DIR, "data", "inventario.csv"
    )

    ruta_api = os.path.join(
        BASE_DIR, "data", "api_pedidos.json"
    )

    ruta_web = os.path.join(
        BASE_DIR, "data", "productos_web.csv"
    )

    # cargar archivos
    perfiles = cargar_perfiles_json(ruta_perfiles)
    inventario = pd.read_csv(ruta_inventario)
    api_df = pd.read_json(ruta_api)
    web_df = pd.read_csv(ruta_web)

    # LIMPIAR NOMBRES COLUMNAS

    # inventario: producto_id -> id_producto
    inventario.rename(
        columns={"producto_id": "id_producto"},
        inplace=True
    )

    # api: Customer_ID -> id_cliente
    api_df.rename(
       columns={"Customer_ID": "id_cliente"},
      inplace=True
    )


    # CORREGIR TIPOS DE DATOS

    df = ventas_df.merge(
        perfiles,
        on="id_cliente",
        how="left"
    )

    # convertir a entero
    df["id_producto"] = df["id_producto"].astype(int)
    inventario["id_producto"] = inventario["id_producto"].astype(int)
    web_df["id_producto"] = web_df["id_producto"].str.replace("PROD_", "", regex=False)
    web_df["id_producto"] = web_df["id_producto"].astype(int)
    api_df["id_cliente"] = api_df["id_cliente"].astype(int)

    return df