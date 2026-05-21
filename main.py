"""
main.py - Proyecto ETL completo en un solo archivo

Incluye:
1. Extraccion desde archivos locales: CSV, JSON y TXT.
2. Extraccion desde MySQL si esta disponible; si falla, usa data/ventas.csv.
3. API REST: obtiene entre 50 y 100 registros desde JSONPlaceholder.
4. Web Scraping: obtiene entre 50 y 100 registros desde Books to Scrape.
5. Limpieza, transformacion, integracion y guardado del archivo final.

Ejecucion:
    python main.py

Carpetas esperadas:
    data/ventas.csv
    data/inventario.csv
    data/perfiles.json
    data/logs.txt

Salida:
    output/data_master_clean.csv
    data/api_rest_registros.csv
    data/web_scraping_registros.csv
"""

from __future__ import annotations

import csv
import json
import os
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import pandas as pd


# ==========================================================
# CONFIGURACION GENERAL
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

VENTAS_CSV = DATA_DIR / "ventas.csv"
INVENTARIO_CSV = DATA_DIR / "inventario.csv"
PERFILES_JSON = DATA_DIR / "perfiles.json"
LOGS_TXT = DATA_DIR / "logs.txt"

API_REST_CSV = DATA_DIR / "api_rest_registros.csv"
WEB_SCRAPING_CSV = DATA_DIR / "web_scraping_registros.csv"
ARCHIVO_FINAL = OUTPUT_DIR / "data_master_clean.csv"

MIN_REGISTROS_EXTERNOS = 50
MAX_REGISTROS_EXTERNOS = 100


# ==========================================================
# UTILIDADES
# ==========================================================

def crear_carpetas() -> None:
    """Crea las carpetas necesarias si no existen."""
    DATA_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)


def leer_json_url(url: str, timeout: int = 15) -> Any:
    """Lee JSON desde una URL usando solo librerias estandar de Python."""
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 ETL-Academico/1.0",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        contenido = response.read().decode("utf-8")
        return json.loads(contenido)


def leer_html_url(url: str, timeout: int = 15) -> str:
    """Lee HTML desde una URL usando solo librerias estandar de Python."""
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 ETL-Academico/1.0"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="ignore")


def limpiar_texto(valor: Any) -> str:
    """Normaliza espacios y convierte a texto seguro."""
    if pd.isna(valor):
        return ""
    return re.sub(r"\s+", " ", str(valor)).strip()


def limpiar_precio(valor: Any) -> float:
    """Convierte un precio tipo '£51.77' a numero decimal."""
    texto = limpiar_texto(valor)
    texto = texto.replace("£", "").replace("$", "").replace(",", "")
    texto = re.sub(r"[^0-9.]", "", texto)
    return float(texto) if texto else 0.0


def guardar_csv(df: pd.DataFrame, ruta: Path) -> None:
    """Guarda un DataFrame en CSV."""
    ruta.parent.mkdir(exist_ok=True)
    df.to_csv(ruta, index=False, encoding="utf-8-sig")


# ==========================================================
# EXTRACCION LOCAL: CSV, JSON, TXT Y MYSQL OPCIONAL
# ==========================================================

def cargar_ventas_desde_mysql() -> pd.DataFrame | None:
    """
    Intenta cargar ventas desde MySQL.
    Si no existe la conexion, regresa None y el ETL usa ventas.csv.
    """
    try:
        from sqlalchemy import create_engine

        engine = create_engine("mysql+pymysql://root:@localhost/etl_proyecto")
        query = "SELECT * FROM ventas_historicas"
        df = pd.read_sql(query, engine)
        if df.empty:
            return None
        print("Ventas cargadas desde MySQL.")
        return df
    except Exception as error:
        print(f"No se pudo conectar a MySQL. Se usara ventas.csv. Detalle: {error}")
        return None


def cargar_ventas() -> pd.DataFrame:
    """Carga ventas desde MySQL si esta disponible; si no, desde CSV."""
    ventas_mysql = cargar_ventas_desde_mysql()
    if ventas_mysql is not None:
        return ventas_mysql

    if not VENTAS_CSV.exists():
        raise FileNotFoundError(f"No se encontro el archivo: {VENTAS_CSV}")

    return pd.read_csv(VENTAS_CSV)


def cargar_inventario() -> pd.DataFrame:
    """Carga inventario desde CSV."""
    if not INVENTARIO_CSV.exists():
        raise FileNotFoundError(f"No se encontro el archivo: {INVENTARIO_CSV}")
    return pd.read_csv(INVENTARIO_CSV)


def cargar_perfiles() -> pd.DataFrame:
    """Carga perfiles desde JSON."""
    if not PERFILES_JSON.exists():
        raise FileNotFoundError(f"No se encontro el archivo: {PERFILES_JSON}")
    return pd.read_json(PERFILES_JSON)


def cargar_logs() -> pd.DataFrame:
    """
    Carga logs desde TXT con formato:
    estado=ERROR, tiempo=517ms
    """
    if not LOGS_TXT.exists():
        return pd.DataFrame(columns=["estado_log", "tiempo_ms"])

    registros = []
    patron = re.compile(r"estado=(?P<estado>\w+),\s*tiempo=(?P<tiempo>\d+)ms", re.I)

    with open(LOGS_TXT, "r", encoding="utf-8", errors="ignore") as archivo:
        for linea in archivo:
            match = patron.search(linea)
            if match:
                registros.append(
                    {
                        "estado_log": match.group("estado").upper(),
                        "tiempo_ms": int(match.group("tiempo")),
                    }
                )

    return pd.DataFrame(registros)


# ==========================================================
# API REST: ENTRE 50 Y 100 REGISTROS
# ==========================================================

def extraer_api_rest(limite: int = MAX_REGISTROS_EXTERNOS) -> pd.DataFrame:
    """
    Extrae registros de una API REST publica.

    Fuente: JSONPlaceholder /posts
    Cantidad: entre 50 y 100 registros.

    Nota academica:
    Al ser una fuente externa, se limita el volumen para evitar problemas
    por limites de tasa, tiempo de respuesta o disponibilidad del servicio.
    """
    limite = max(MIN_REGISTROS_EXTERNOS, min(limite, MAX_REGISTROS_EXTERNOS))
    url = "https://jsonplaceholder.typicode.com/posts"

    try:
        datos = leer_json_url(url)
        df = pd.DataFrame(datos).head(limite)
        df.rename(
            columns={
                "userId": "id_cliente_api",
                "id": "id_registro_api",
                "title": "titulo_api",
                "body": "descripcion_api",
            },
            inplace=True,
        )
        df["fuente_api"] = "JSONPlaceholder"
        print(f"API REST cargada correctamente: {len(df)} registros.")
    except Exception as error:
        print(f"No se pudo consumir la API REST. Se generaran datos demo. Detalle: {error}")
        df = pd.DataFrame(
            [
                {
                    "id_cliente_api": (i % 1000) + 1,
                    "id_registro_api": i,
                    "titulo_api": f"Pedido API demo {i}",
                    "descripcion_api": "Registro demo generado por falta de conexion externa",
                    "fuente_api": "Demo local",
                }
                for i in range(1, limite + 1)
            ]
        )

    guardar_csv(df, API_REST_CSV)
    return df


# ==========================================================
# WEB SCRAPING: ENTRE 50 Y 100 REGISTROS
# ==========================================================

@dataclass
class ProductoScraping:
    titulo: str = ""
    precio: str = ""
    disponibilidad: str = ""
    rating: str = ""


class BooksToScrapeParser(HTMLParser):
    """Parser simple para extraer libros de books.toscrape.com."""

    def __init__(self) -> None:
        super().__init__()
        self.productos: list[ProductoScraping] = []
        self.en_producto = False
        self.producto_actual: ProductoScraping | None = None
        self.capturar_precio = False
        self.capturar_disponibilidad = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        clases = attrs_dict.get("class", "") or ""

        if tag == "article" and "product_pod" in clases:
            self.en_producto = True
            self.producto_actual = ProductoScraping()

        if self.en_producto and tag == "p" and "star-rating" in clases:
            partes = clases.split()
            ratings = [p for p in partes if p != "star-rating"]
            if self.producto_actual and ratings:
                self.producto_actual.rating = ratings[0]

        if self.en_producto and tag == "a":
            titulo = attrs_dict.get("title")
            if titulo and self.producto_actual and not self.producto_actual.titulo:
                self.producto_actual.titulo = titulo

        if self.en_producto and tag == "p" and "price_color" in clases:
            self.capturar_precio = True

        if self.en_producto and tag == "p" and "availability" in clases:
            self.capturar_disponibilidad = True

    def handle_data(self, data: str) -> None:
        if not self.en_producto or not self.producto_actual:
            return

        texto = limpiar_texto(data)
        if not texto:
            return

        if self.capturar_precio:
            self.producto_actual.precio += texto

        if self.capturar_disponibilidad:
            self.producto_actual.disponibilidad += " " + texto

    def handle_endtag(self, tag: str) -> None:
        if self.capturar_precio and tag == "p":
            self.capturar_precio = False

        if self.capturar_disponibilidad and tag == "p":
            self.capturar_disponibilidad = False

        if self.en_producto and tag == "article":
            if self.producto_actual:
                self.productos.append(self.producto_actual)
            self.en_producto = False
            self.producto_actual = None


def extraer_web_scraping(limite: int = 60) -> pd.DataFrame:
    """
    Extrae productos mediante Web Scraping.

    Fuente: books.toscrape.com
    Cantidad: entre 50 y 100 registros.

    Nota academica:
    Se limita a pocas paginas para evitar sobrecargar el sitio y respetar
    que las fuentes externas pueden tener restricciones o limites de tasa.
    """
    limite = max(MIN_REGISTROS_EXTERNOS, min(limite, MAX_REGISTROS_EXTERNOS))
    productos: list[dict[str, Any]] = []

    try:
        pagina = 1
        while len(productos) < limite:
            url = f"https://books.toscrape.com/catalogue/page-{pagina}.html"
            html = leer_html_url(url)
            parser = BooksToScrapeParser()
            parser.feed(html)

            if not parser.productos:
                break

            for item in parser.productos:
                productos.append(
                    {
                        "id_producto": len(productos) + 1,
                        "producto_web": limpiar_texto(item.titulo),
                        "precio_web": limpiar_precio(item.precio),
                        "disponibilidad_web": limpiar_texto(item.disponibilidad),
                        "rating_web": limpiar_texto(item.rating),
                        "fuente_web": "Books to Scrape",
                    }
                )
                if len(productos) >= limite:
                    break

            pagina += 1
            time.sleep(0.3)

        df = pd.DataFrame(productos).head(limite)
        print(f"Web Scraping cargado correctamente: {len(df)} registros.")
    except Exception as error:
        print(f"No se pudo hacer Web Scraping. Se generaran datos demo. Detalle: {error}")
        df = pd.DataFrame(
            [
                {
                    "id_producto": i,
                    "producto_web": f"Producto web demo {i}",
                    "precio_web": round(100 + (i * 3.75), 2),
                    "disponibilidad_web": "In stock",
                    "rating_web": ["One", "Two", "Three", "Four", "Five"][i % 5],
                    "fuente_web": "Demo local",
                }
                for i in range(1, limite + 1)
            ]
        )

    guardar_csv(df, WEB_SCRAPING_CSV)
    return df


# ==========================================================
# TRANSFORMACION
# ==========================================================

def preparar_ventas(ventas: pd.DataFrame, inventario: pd.DataFrame) -> pd.DataFrame:
    """Limpia ventas y agrega id_producto si no existe."""
    ventas = ventas.copy()
    ventas.columns = [c.strip().lower() for c in ventas.columns]

    if "id_transaccion" not in ventas.columns:
        ventas.insert(0, "id_transaccion", range(1, len(ventas) + 1))

    if "id_producto" not in ventas.columns:
        total_productos = max(len(inventario), 1)
        ventas["id_producto"] = ((ventas["id_transaccion"].astype(int) - 1) % total_productos) + 1

    ventas["id_cliente"] = pd.to_numeric(ventas["id_cliente"], errors="coerce").fillna(0).astype(int)
    ventas["id_producto"] = pd.to_numeric(ventas["id_producto"], errors="coerce").fillna(0).astype(int)
    ventas["monto"] = pd.to_numeric(ventas["monto"], errors="coerce").fillna(0)
    ventas["fecha"] = pd.to_datetime(ventas["fecha"], errors="coerce", dayfirst=True)
    ventas["fecha"] = ventas["fecha"].dt.strftime("%Y-%m-%d")

    return ventas


def preparar_inventario(inventario: pd.DataFrame) -> pd.DataFrame:
    """Limpia inventario y normaliza nombres de columnas."""
    inventario = inventario.copy()
    inventario.columns = [c.strip().lower() for c in inventario.columns]

    if "producto_id" in inventario.columns and "id_producto" not in inventario.columns:
        inventario.rename(columns={"producto_id": "id_producto"}, inplace=True)

    inventario["id_producto"] = pd.to_numeric(inventario["id_producto"], errors="coerce").fillna(0).astype(int)
    inventario["stock"] = pd.to_numeric(inventario.get("stock", 0), errors="coerce").fillna(0).astype(int)
    inventario["precio"] = pd.to_numeric(inventario.get("precio", 0), errors="coerce").fillna(0)

    # Evita duplicar ventas cuando un producto aparece mas de una vez en inventario.
    inventario = (
        inventario.sort_values("id_producto")
        .groupby("id_producto", as_index=False)
        .agg(stock=("stock", "sum"), precio=("precio", "mean"))
    )

    return inventario


def preparar_perfiles(perfiles: pd.DataFrame) -> pd.DataFrame:
    """Limpia perfiles de clientes."""
    perfiles = perfiles.copy()
    perfiles.columns = [c.strip().lower() for c in perfiles.columns]

    perfiles["id_cliente"] = pd.to_numeric(perfiles["id_cliente"], errors="coerce").fillna(0).astype(int)
    perfiles["edad"] = pd.to_numeric(perfiles.get("edad", 0), errors="coerce").fillna(0).astype(int)
    perfiles["ingresos"] = pd.to_numeric(perfiles.get("ingresos", 0), errors="coerce").fillna(0)
    perfiles["puntos_lealtad"] = pd.to_numeric(perfiles.get("puntos_lealtad", 0), errors="coerce").fillna(0).astype(int)
    perfiles["pais"] = perfiles.get("pais", "Sin dato").astype(str).str.strip()
    perfiles["pais"] = perfiles["pais"].replace({"mex": "México", "MX": "México", "Mexico": "México"})

    # Evita duplicar ventas cuando un cliente aparece mas de una vez en perfiles.
    perfiles = (
        perfiles.sort_values("id_cliente")
        .groupby("id_cliente", as_index=False)
        .agg(
            edad=("edad", "first"),
            ingresos=("ingresos", "first"),
            puntos_lealtad=("puntos_lealtad", "max"),
            pais=("pais", "first"),
        )
    )

    return perfiles


def preparar_api(api_df: pd.DataFrame) -> pd.DataFrame:
    """Agrupa la API REST por cliente para integrarla al dataset maestro."""
    api_df = api_df.copy()
    api_df["id_cliente"] = pd.to_numeric(api_df["id_cliente_api"], errors="coerce").fillna(0).astype(int)

    resumen = (
        api_df.groupby("id_cliente", as_index=False)
        .agg(
            registros_api=("id_registro_api", "count"),
            ultimo_registro_api=("id_registro_api", "max"),
            fuente_api=("fuente_api", "first"),
        )
    )
    return resumen


def preparar_logs(logs_df: pd.DataFrame) -> pd.DataFrame:
    """Genera indicadores generales de logs."""
    if logs_df.empty:
        return pd.DataFrame(
            [{"logs_total": 0, "logs_error": 0, "logs_timeout": 0, "tiempo_promedio_ms": 0.0}]
        )

    return pd.DataFrame(
        [
            {
                "logs_total": len(logs_df),
                "logs_error": int((logs_df["estado_log"] == "ERROR").sum()),
                "logs_timeout": int((logs_df["estado_log"] == "TIMEOUT").sum()),
                "tiempo_promedio_ms": round(float(logs_df["tiempo_ms"].mean()), 2),
            }
        ]
    )


def transformar_datos(
    ventas: pd.DataFrame,
    inventario: pd.DataFrame,
    perfiles: pd.DataFrame,
    api_df: pd.DataFrame,
    web_df: pd.DataFrame,
    logs_df: pd.DataFrame,
) -> pd.DataFrame:
    """Integra todas las fuentes y crea columnas utiles para analisis."""
    inventario = preparar_inventario(inventario)
    ventas = preparar_ventas(ventas, inventario)
    perfiles = preparar_perfiles(perfiles)
    api_resumen = preparar_api(api_df)
    logs_resumen = preparar_logs(logs_df)

    web_df = web_df.copy()
    web_df["id_producto"] = pd.to_numeric(web_df["id_producto"], errors="coerce").fillna(0).astype(int)
    web_df = web_df.drop_duplicates(subset=["id_producto"], keep="first")

    df = ventas.merge(perfiles, on="id_cliente", how="left")
    df = df.merge(inventario, on="id_producto", how="left")
    df = df.merge(api_resumen, on="id_cliente", how="left")
    df = df.merge(web_df, on="id_producto", how="left")

    # Agregar resumen de logs como columnas constantes para el reporte final
    for columna, valor in logs_resumen.iloc[0].items():
        df[columna] = valor

    # Limpieza de valores faltantes
    df["edad"] = df["edad"].fillna(0).astype(int)
    df["ingresos"] = df["ingresos"].fillna(0)
    df["puntos_lealtad"] = df["puntos_lealtad"].fillna(0).astype(int)
    df["pais"] = df["pais"].fillna("Sin dato")
    df["stock"] = df["stock"].fillna(0).astype(int)
    df["precio"] = df["precio"].fillna(0)
    df["registros_api"] = df["registros_api"].fillna(0).astype(int)
    df["ultimo_registro_api"] = df["ultimo_registro_api"].fillna(0).astype(int)
    df["fuente_api"] = df["fuente_api"].fillna("Sin API")
    df["producto_web"] = df["producto_web"].fillna("Sin producto web")
    df["precio_web"] = df["precio_web"].fillna(0)
    df["disponibilidad_web"] = df["disponibilidad_web"].fillna("Sin dato")
    df["rating_web"] = df["rating_web"].fillna("Sin rating")
    df["fuente_web"] = df["fuente_web"].fillna("Sin web scraping")

    # Variables derivadas
    df["cliente_premium"] = df["puntos_lealtad"].apply(lambda x: "Sí" if x >= 1000 else "No")
    df["categoria_monto"] = pd.cut(
        df["monto"],
        bins=[-1, 500, 2000, 5000, float("inf")],
        labels=["Bajo", "Medio", "Alto", "Muy alto"],
    ).astype(str)
    df["estado_stock"] = df["stock"].apply(lambda x: "Sin stock" if x <= 0 else "Disponible")
    df["utilidad_estimada"] = (df["monto"] - df["precio"]).round(2)
    df["origen_integrado"] = "CSV + JSON + TXT + API REST + Web Scraping"

    # Orden sugerido de columnas principales
    columnas_principales = [
        "id_transaccion",
        "id_cliente",
        "id_producto",
        "monto",
        "fecha",
        "id_tienda",
        "edad",
        "ingresos",
        "puntos_lealtad",
        "pais",
        "cliente_premium",
        "categoria_monto",
        "stock",
        "precio",
        "estado_stock",
        "utilidad_estimada",
        "registros_api",
        "ultimo_registro_api",
        "fuente_api",
        "producto_web",
        "precio_web",
        "disponibilidad_web",
        "rating_web",
        "fuente_web",
        "logs_total",
        "logs_error",
        "logs_timeout",
        "tiempo_promedio_ms",
        "origen_integrado",
    ]

    columnas_existentes = [c for c in columnas_principales if c in df.columns]
    columnas_extra = [c for c in df.columns if c not in columnas_existentes]
    df = df[columnas_existentes + columnas_extra]

    return df


# ==========================================================
# CARGA / EJECUCION ETL
# ==========================================================

def ejecutar_etl() -> pd.DataFrame:
    """Ejecuta el pipeline ETL completo."""
    crear_carpetas()

    print("=" * 70)
    print("INICIANDO PROCESO ETL")
    print("=" * 70)

    ventas = cargar_ventas()
    inventario = cargar_inventario()
    perfiles = cargar_perfiles()
    logs = cargar_logs()

    api_df = extraer_api_rest(limite=100)
    web_df = extraer_web_scraping(limite=60)

    df_final = transformar_datos(
        ventas=ventas,
        inventario=inventario,
        perfiles=perfiles,
        api_df=api_df,
        web_df=web_df,
        logs_df=logs,
    )

    guardar_csv(df_final, ARCHIVO_FINAL)
    return df_final


def mostrar_resumen(df: pd.DataFrame) -> None:
    """Imprime un resumen final del proceso."""
    print("=" * 70)
    print("ETL EJECUTADO CORRECTAMENTE")
    print("=" * 70)
    print(f"Total registros procesados en archivo final: {len(df)}")
    print(f"Total columnas generadas: {len(df.columns)}")
    print(f"Archivo final generado: {ARCHIVO_FINAL}")
    print(f"Archivo API REST generado: {API_REST_CSV}")
    print(f"Archivo Web Scraping generado: {WEB_SCRAPING_CSV}")
    print("=" * 70)
    print("Vista previa:")
    print(df.head(10).to_string(index=False))


# ==========================================================
# PUNTO DE ENTRADA
# ==========================================================

def main() -> None:
    try:
        df = ejecutar_etl()
        mostrar_resumen(df)
    except Exception as error:
        print("=" * 70)
        print("ERROR AL EJECUTAR EL ETL")
        print("=" * 70)
        print(f"Detalle: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
