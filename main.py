from etl import ejecutar_etl


def main():
    df = ejecutar_etl()

    print("=" * 50)
    print("ETL ejecutado correctamente")
    print("=" * 50)
    print(f"Total registros procesados: {len(df)}")
    print("Archivo generado: output/data_master_clean.csv")


if __name__ == "__main__":
    main()