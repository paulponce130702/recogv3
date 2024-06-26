import cv2
import numpy as np
import pytesseract
from PIL import Image
from datetime import datetime
import pandas as pd
import os
import mysql.connector


# Cargar datos desde el archivo Excel
def load_data_from_excel(file_path):
    if not os.path.exists(file_path):
        print(f"Error: El archivo '{file_path}' no se encuentra.")
        return None
    df = pd.read_excel(file_path)
    print("Columnas en el archivo Excel:", df.columns)  # Mostrar las columnas para verificación
    return df


# Preprocesar el marco para recortar el área de interés
def preprocess_frame(frame):
    al, an, c = frame.shape
    x1 = int(an / 3)
    x2 = int(x1 * 2)
    y1 = int(al / 3)
    y2 = int(y1 * 2)
    recorte = frame[y1:y2, x1:x2]
    return recorte, x1, y1


# Detectar área de la placa
def detect_plate_area(recorte):
    mB, mG, mR = recorte[:, :, 0], recorte[:, :, 1], recorte[:, :, 2]
    color_diff = cv2.absdiff(mG, mB)
    _, umbral = cv2.threshold(color_diff, 40, 255, cv2.THRESH_BINARY)
    contornos, _ = cv2.findContours(umbral, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contornos = sorted(contornos, key=lambda x: cv2.contourArea(x), reverse=True)
    return contornos


# Extraer la placa
def extract_plate(frame, contorno, x1, y1):
    x, y, ancho, alto = cv2.boundingRect(contorno)
    xpi, ypi = x + x1, y + y1
    xpf, ypf = x + ancho + x1, y + y1 + alto
    placa = frame[ypi:ypf, xpi:xpf]
    return placa, (xpi, ypi, xpf, ypf)


# Preprocesar la imagen de la placa para OCR
def preprocess_plate(placa):
    mRp, mGp = placa[:, :, 2], placa[:, :, 1]
    Mva = 255 - np.maximum(mRp, mGp)
    _, bin_img = cv2.threshold(Mva, 150, 255, cv2.THRESH_BINARY)
    bin_img = Image.fromarray(bin_img.astype(np.uint8)).convert("L")
    return bin_img


# Detectar texto en la imagen de la placa usando Tesseract
def detect_text(bin_img):
    config = "--psm 1"
    texto = pytesseract.image_to_string(bin_img, config=config)
    return texto


# Buscar información en el archivo Excel
def search_in_excel(df, plate_text):
    try:
        # Limpiar el texto detectado para evitar caracteres especiales
        plate_text = plate_text.strip()
        result = df[df['Plate'].str.contains(plate_text, case=False, na=False, regex=False)]
        if not result.empty:
            return result.iloc[0].to_dict()
        else:
            return {}
    except KeyError:
        print("Error: La columna 'Plate' no existe en el archivo Excel.")
        print("Columnas disponibles:", df.columns)  # Mostrar las columnas disponibles
        return {}


# Insertar datos en la base de datos MySQL
def insert_data_to_mysql(db_config, data):
    connection = mysql.connector.connect(
        host=db_config['host'],
        user=db_config['user'],
        password=db_config['password'],
        database=db_config['database']
    )
    cursor = connection.cursor()

    sql = """
    INSERT INTO vehiculos (Plate, Nombre_del_Propietario, Numero_de_Serie, Numero_de_Motor, Color, Marca, Modelo, Estado, Sede, Tiempo_init)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(sql, (
        data['Plate'],
        data['Nombre del Propietario'],
        data['Número de Serie'],
        data['Número de Motor'],
        data['Color'],
        data['Marca'],
        data['Modelo'],
        data['Estado'],
        data['Sede'],
        data['Tiempo init']
    ))

    connection.commit()
    cursor.close()
    connection.close()


def main():
    cap = cv2.VideoCapture(0)
    Ctexto, Ctiempo = '', ''
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

    # Ruta del archivo Excel
    excel_file_path = 'data_vehiculos.xlsx'

    # Cargar datos del archivo Excel
    df = load_data_from_excel(excel_file_path)
    if df is None:
        print(
            f"Error: No se pudo cargar el archivo '{excel_file_path}'. Asegúrese de que el archivo exista en la ruta especificada.")
        return

    # Preparar DataFrame para guardar la información detectada con las mismas columnas que el archivo original
    columns = df.columns
    output_df = pd.DataFrame(columns=columns)

    # Ruta del archivo Excel para guardar los resultados
    output_file_path = 'output_data.xlsx'

    # Configuración de la base de datos MySQL
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '',
        'database': 'vehiculos_db'
    }

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        cv2.rectangle(frame, (1070, 750), (1270, 850), (0, 0, 0), cv2.FILLED)
        cv2.putText(frame, Ctexto[:7], (900, 810), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.rectangle(frame, (int(frame.shape[1] / 3), int(frame.shape[0] / 3)),
                      (int(2 * frame.shape[1] / 3), int(2 * frame.shape[0] / 3)), (0, 255, 0), 2)
        cv2.rectangle(frame, (int(frame.shape[1] / 3) + 160, int(frame.shape[0] / 3) + 500),
                      (1120, 940), (0, 0, 0), cv2.FILLED)
        cv2.putText(frame, 'Procesando la Placa del Vehiculo',
                    (int(frame.shape[1] / 3) + 180, int(frame.shape[0] / 3) + 550),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        recorte, x1, y1 = preprocess_frame(frame)
        contornos = detect_plate_area(recorte)

        for contorno in contornos:
            area = cv2.contourArea(contorno)
            if 500 < area < 5000:
                placa, (xpi, ypi, xpf, ypf) = extract_plate(frame, contorno, x1, y1)
                cv2.rectangle(frame, (xpi, ypi), (xpf, ypf), (255, 255, 0), 2)
                bin_img = preprocess_plate(placa)

                if placa.shape[0] >= 36 and placa.shape[1] >= 82:
                    texto = detect_text(bin_img)
                    if len(texto) >= 7:
                        Ctexto = texto
                        Ctiempo = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        info = search_in_excel(df, Ctexto)
                        if info:
                            info['Tiempo init'] = Ctiempo  # Añadir el tiempo al diccionario de información
                            info_str = f"Placa detectada: {Ctexto} a las {Ctiempo} - Información: {info}"
                            print(info_str)

                            # Guardar la información en el DataFrame
                            new_row = pd.DataFrame([info])
                            output_df = pd.concat([output_df, new_row], ignore_index=True)

                            # Guardar el DataFrame en un archivo Excel automáticamente
                            output_df.to_excel(output_file_path, index=False)
                            print(f"Datos guardados en el archivo '{output_file_path}' automáticamente.")

                            # Insertar los datos en la base de datos MySQL
                            insert_data_to_mysql(db_config, info)
                        else:
                            print(f"Placa detectada: {Ctexto} a las {Ctiempo} - No se encontró información")

                break

        cv2.putText(frame, f'Placa: {Ctexto}', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f'Tiempo: {Ctiempo}', (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("vehiculos", frame)

        if cv2.waitKey(1) == 27:
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
