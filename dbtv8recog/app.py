from flask import Flask, render_template, redirect, url_for, request
import mysql.connector
import subprocess  # Importa el módulo subprocess para ejecutar comandos externos

app = Flask(__name__)

# Configuración de la base de datos MySQL
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'vehiculos_db'
}


def get_db_connection():
    return mysql.connector.connect(**db_config)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/vehiculos', methods=['GET'])
def get_vehiculos():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute('SELECT * FROM vehiculos')
    vehiculos = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('vehiculos.html', vehiculos=vehiculos)


@app.route('/vehiculos/<int:id>', methods=['GET'])
def get_vehiculo(id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute('SELECT * FROM vehiculos WHERE id = %s', (id,))
    vehiculo = cursor.fetchone()
    cursor.close()
    connection.close()
    return render_template('vehiculo.html', vehiculo=vehiculo)


@app.route('/vehiculos/create', methods=['GET', 'POST'])
def create_vehiculo():
    if request.method == 'POST':
        data = request.form
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            'INSERT INTO vehiculos (Plate, Nombre_del_Propietario, Numero_de_Serie, Numero_de_Motor, Color, Marca, Modelo, Estado, Sede, Tiempo_init) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
            (data['Plate'], data['Nombre_del_Propietario'], data['Numero_de_Serie'], data['Numero_de_Motor'],
             data['Color'], data['Marca'], data['Modelo'], data['Estado'], data['Sede'], data['Tiempo_init'])
        )
        connection.commit()
        cursor.close()
        connection.close()
        return redirect(url_for('get_vehiculos'))
    else:
        return render_template('create.html')


@app.route('/vehiculos/<int:id>/update', methods=['GET', 'POST'])
def update_vehiculo(id):
    if request.method == 'POST':
        data = request.form
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            'UPDATE vehiculos SET Plate = %s, Nombre_del_Propietario = %s, Numero_de_Serie = %s, Numero_de_Motor = %s, Color = %s, Marca = %s, Modelo = %s, Estado = %s, Sede = %s, Tiempo_init = %s WHERE id = %s',
            (data['Plate'], data['Nombre_del_Propietario'], data['Numero_de_Serie'], data['Numero_de_Motor'],
             data['Color'], data['Marca'], data['Modelo'], data['Estado'], data['Sede'], data['Tiempo_init'], id)
        )
        connection.commit()
        cursor.close()
        connection.close()
        return redirect(url_for('get_vehiculos'))
    else:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT * FROM vehiculos WHERE id = %s', (id,))
        vehiculo = cursor.fetchone()
        cursor.close()
        connection.close()
        return render_template('update.html', vehiculo=vehiculo)


@app.route('/vehiculos/<int:id>/delete', methods=['POST'])
def delete_vehiculo(id):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('DELETE FROM vehiculos WHERE id = %s', (id,))
    connection.commit()
    cursor.close()
    connection.close()
    return redirect(url_for('get_vehiculos'))


@app.route('/detectar_vehiculos', methods=['POST'])
def detectar_vehiculos():
    # Ruta para ejecutar el script detecrecov8.py
    # Cambia el comando dependiendo de la ubicación y los parámetros necesarios
    subprocess.run(['python', 'detecrecov8.py'])

    # Después de ejecutar, puedes redirigir a la página principal o a cualquier otra página
    return redirect(url_for('get_vehiculos'))


if __name__ == '__main__':
    app.run(debug=True)
