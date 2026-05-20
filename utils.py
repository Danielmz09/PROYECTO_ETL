import mysql.connector
import pandas as pd


def conectar_mysql():
    """
    Conexión a MySQL (XAMPP)
    """
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",          # Cambiar si configuraste password
        database="etl_proyecto",
        port=3306
    )
    return conn


def cargar_perfiles_json(path):
    """
    Carga perfiles de usuarios desde JSON
    """
    return pd.read_json(path)


def cargar_inventario_csv(path):
    """
    Carga inventario
    """
    return pd.read_csv(path)


def guardar_csv(df, path):
    """
    Guarda dataframe final
    """
    df.to_csv(path, index=False)