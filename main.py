from utils import generar_datos
from etl import extraer, transformar, cargar
import matplotlib.pyplot as plt

def main():
    generar_datos()

    ventas, inventario, perfiles = extraer()
    df = transformar(ventas, inventario, perfiles)

    # BOXPLOT
    plt.boxplot(df["monto"])
    plt.title("Outliers en ventas")
    plt.show()

    # SCATTER PCA
    plt.scatter(df["pca1"], df["pca2"])
    plt.title("PCA Clusters")
    plt.show()

    cargar(df)

if __name__ == "__main__":
    main()