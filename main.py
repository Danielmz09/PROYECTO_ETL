from utils import generar_datos
from etl import extraer, transformar, cargar
import matplotlib.pyplot as plt
from matplotlib.sankey import Sankey


def main():
    # GENERAR DATOS
    generar_datos()

    # EXTRACCIÓN
    ventas, inventario, perfiles, logs = extraer()

    # TRANSFORMACIÓN
    df = transformar(
        ventas,
        inventario,
        perfiles
    )

    # BOXPLOT
    plt.figure(figsize=(8, 5))
    plt.boxplot(df["monto"])
    plt.title("Detección de Outliers en Monto de Ventas")
    plt.ylabel("Monto")
    plt.show()

    # SCATTER PCA
    plt.figure(figsize=(8, 5))
    plt.scatter(
        df["pca1"],
        df["pca2"]
    )
    plt.title("Clusters PCA")
    plt.xlabel("PCA 1")
    plt.ylabel("PCA 2")
    plt.show()

    # SANKEY
    plt.figure(figsize=(8, 5))

    sankey = Sankey(unit=None)
    sankey.add(
        flows=[1, -1],
        labels=["Visitas Web", "Compras Finales"]
    )
    sankey.finish()

    plt.title("Flujo Usuario Web -> Compra")
    plt.show()

    # CARGA
    cargar(df)


if __name__ == "__main__":
    main()