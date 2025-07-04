from flask import Flask, render_template, jsonify, request
import requests
import json
from datetime import datetime, timedelta
import threading
import time
import sqlite3
import os
from collections import defaultdict

app = Flask(__name__)

# Configuración
ESP32_IP = "192.168.1.41"  # Cambia por la IP de tu ESP32
ESP32_PORT = 80

# Variables globales para almacenar datos
sensor_data = {
    'temperature': 0,
    'humidity': 0,
    'co2_ppm': 0,
    'timestamp': None,
    'status': 'disconnected'
}

# Configuración de la base de datos
DATABASE = 'sensor_data.db'

def init_database():
    """Inicializar la base de datos SQLite"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Crear tabla para almacenar datos históricos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            temperature REAL,
            humidity REAL,
            co2_ppm REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Crear tabla para estadísticas diarias
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE,
            avg_temperature REAL,
            avg_humidity REAL,
            avg_co2 REAL,
            max_temperature REAL,
            min_temperature REAL,
            max_humidity REAL,
            min_humidity REAL,
            max_co2 REAL,
            min_co2 REAL,
            readings_count INTEGER
        )
    ''')
    
    conn.commit()
    conn.close()

def save_sensor_data(temperature, humidity, co2_ppm):
    """Guardar datos del sensor en la base de datos"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO sensor_readings (temperature, humidity, co2_ppm)
            VALUES (?, ?, ?)
        ''', (temperature, humidity, co2_ppm))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error guardando datos: {e}")
        return False

def get_historical_data(hours=24):
    """Obtener datos históricos de las últimas N horas"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Obtener datos de las últimas N horas
        time_threshold = datetime.now() - timedelta(hours=hours)
        
        cursor.execute('''
            SELECT temperature, humidity, co2_ppm, timestamp
            FROM sensor_readings
            WHERE timestamp >= ?
            ORDER BY timestamp ASC
        ''', (time_threshold,))
        
        data = cursor.fetchall()
        conn.close()
        
        return [
            {
                'temperature': row[0],
                'humidity': row[1],
                'co2_ppm': row[2],
                'timestamp': row[3]
            }
            for row in data
        ]
    except Exception as e:
        print(f"Error obteniendo datos históricos: {e}")
        return []

def get_daily_statistics(days=7):
    """Obtener estadísticas diarias de los últimos N días"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Obtener estadísticas de los últimos N días
        date_threshold = datetime.now() - timedelta(days=days)
        
        cursor.execute('''
            SELECT date, avg_temperature, avg_humidity, avg_co2,
                   max_temperature, min_temperature, max_humidity, min_humidity,
                   max_co2, min_co2, readings_count
            FROM daily_stats
            WHERE date >= ?
            ORDER BY date ASC
        ''', (date_threshold.date(),))
        
        data = cursor.fetchall()
        conn.close()
        
        return [
            {
                'date': row[0],
                'avg_temperature': row[1],
                'avg_humidity': row[2],
                'avg_co2': row[3],
                'max_temperature': row[4],
                'min_temperature': row[5],
                'max_humidity': row[6],
                'min_humidity': row[7],
                'max_co2': row[8],
                'min_co2': row[9],
                'readings_count': row[10]
            }
            for row in data
        ]
    except Exception as e:
        print(f"Error obteniendo estadísticas: {e}")
        return []

def calculate_daily_stats():
    """Calcular estadísticas diarias"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Obtener datos de hoy
        today = datetime.now().date()
        
        cursor.execute('''
            SELECT 
                AVG(temperature) as avg_temp,
                AVG(humidity) as avg_hum,
                AVG(co2_ppm) as avg_co2,
                MAX(temperature) as max_temp,
                MIN(temperature) as min_temp,
                MAX(humidity) as max_hum,
                MIN(humidity) as min_hum,
                MAX(co2_ppm) as max_co2,
                MIN(co2_ppm) as min_co2,
                COUNT(*) as count
            FROM sensor_readings
            WHERE DATE(timestamp) = ?
        ''', (today,))
        
        result = cursor.fetchone()
        
        if result and result[0] is not None:
            # Verificar si ya existe estadística para hoy
            cursor.execute('SELECT id FROM daily_stats WHERE date = ?', (today,))
            existing = cursor.fetchone()
            
            if existing:
                # Actualizar estadística existente
                cursor.execute('''
                    UPDATE daily_stats SET
                        avg_temperature = ?, avg_humidity = ?, avg_co2 = ?,
                        max_temperature = ?, min_temperature = ?,
                        max_humidity = ?, min_humidity = ?,
                        max_co2 = ?, min_co2 = ?, readings_count = ?
                    WHERE date = ?
                ''', result + (today,))
            else:
                # Insertar nueva estadística
                cursor.execute('''
                    INSERT INTO daily_stats 
                    (date, avg_temperature, avg_humidity, avg_co2, max_temperature, 
                     min_temperature, max_humidity, min_humidity, max_co2, min_co2, readings_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (today,) + result)
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error calculando estadísticas: {e}")

def get_esp32_data():
    """Función para obtener datos del ESP32"""
    try:
        response = requests.get(f"http://{ESP32_IP}:{ESP32_PORT}/data", timeout=5)
        if response.status_code == 200:
            data = response.json()
            sensor_data.update(data)
            sensor_data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            sensor_data['status'] = 'connected'
            
            # Guardar datos en la base de datos
            if data.get('temperature') and data.get('humidity') and data.get('co2_ppm'):
                save_sensor_data(data['temperature'], data['humidity'], data['co2_ppm'])
            
            return True
    except Exception as e:
        print(f"Error conectando con ESP32: {e}")
        sensor_data['status'] = 'disconnected'
        return False

def background_data_fetcher():
    """Función que se ejecuta en segundo plano para obtener datos"""
    while True:
        get_esp32_data()
        time.sleep(2)  # Obtener datos cada 2 segundos

def background_stats_calculator():
    """Función que se ejecuta en segundo plano para calcular estadísticas"""
    while True:
        calculate_daily_stats()
        time.sleep(300)  # Calcular estadísticas cada 5 minutos

# Inicializar base de datos
init_database()

# Iniciar hilos en segundo plano
data_thread = threading.Thread(target=background_data_fetcher, daemon=True)
stats_thread = threading.Thread(target=background_stats_calculator, daemon=True)
data_thread.start()
stats_thread.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/historial')
def historial():
    return render_template('historial.html')

@app.route('/estadisticas')
def estadisticas():
    return render_template('estadisticas.html')

@app.route('/reporte-clima')
def reporte_clima():
    return render_template('reporte_clima.html')

@app.route('/api/data')
def api_data():
    return jsonify(sensor_data)

@app.route('/api/esp32_status')
def esp32_status():
    success = get_esp32_data()
    return jsonify({'connected': success, 'ip': ESP32_IP})

@app.route('/api/historical')
def api_historical():
    hours = request.args.get('hours', 24, type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    interval = request.args.get('interval', 1, type=int)  # minutos

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    # Agrupar por intervalos de tiempo (en minutos) y ajustar a UTC-5 (Ecuador)
    cursor.execute(f'''
        SELECT 
            strftime('%Y-%m-%d %H:%M', datetime(timestamp, '-5 hours')) as interval_time,
            AVG(temperature), AVG(humidity), AVG(co2_ppm), MIN(datetime(timestamp, '-5 hours'))
        FROM sensor_readings
        WHERE timestamp >= datetime('now', ?)
        GROUP BY (strftime('%s', timestamp) / (? * 60))
        ORDER BY MIN(timestamp) DESC
        LIMIT ? OFFSET ?
    ''', (f'-{hours} hours', interval, per_page, (page-1)*per_page))
    data = cursor.fetchall()
    conn.close()

    result = [
        {
            'timestamp': row[0],
            'temperature': row[1],
            'humidity': row[2],
            'co2_ppm': row[3]
        }
        for row in data
    ]
    return jsonify(result)

@app.route('/api/statistics')
def api_statistics():
    days = request.args.get('days', 7, type=int)
    data = get_daily_statistics(days)
    return jsonify(data)

@app.route('/api/weather_report')
def api_weather_report():
    """Generar reporte del clima basado en los datos actuales"""
    try:
        # Obtener datos actuales
        current_data = sensor_data.copy()
        
        # Obtener datos históricos de las últimas 24 horas
        historical_data = get_historical_data(24)
        
        if not historical_data:
            return jsonify({'error': 'No hay datos suficientes'})
        
        # Calcular promedios
        avg_temp = sum(d['temperature'] for d in historical_data) / len(historical_data)
        avg_humidity = sum(d['humidity'] for d in historical_data) / len(historical_data)
        avg_co2 = sum(d['co2_ppm'] for d in historical_data) / len(historical_data)
        
        # Determinar condiciones del clima
        temp_condition = "Normal"
        if current_data['temperature'] > 30:
            temp_condition = "Caluroso"
        elif current_data['temperature'] < 15:
            temp_condition = "Frío"
        
        humidity_condition = "Normal"
        if current_data['humidity'] > 70:
            humidity_condition = "Húmedo"
        elif current_data['humidity'] < 30:
            humidity_condition = "Seco"
        
        air_quality = "Buena"
        if current_data['co2_ppm'] > 1000:
            air_quality = "Regular"
        elif current_data['co2_ppm'] > 2000:
            air_quality = "Mala"
        
        report = {
            'current_conditions': {
                'temperature': current_data['temperature'],
                'humidity': current_data['humidity'],
                'co2_ppm': current_data['co2_ppm'],
                'temp_condition': temp_condition,
                'humidity_condition': humidity_condition,
                'air_quality': air_quality
            },
            'averages_24h': {
                'temperature': round(avg_temp, 1),
                'humidity': round(avg_humidity, 1),
                'co2_ppm': round(avg_co2, 1)
            },
            'recommendations': []
        }
        
        # Añadir recomendaciones
        if current_data['temperature'] > 28:
            report['recommendations'].append("Considera usar ventilación o aire acondicionado")
        if current_data['humidity'] > 75:
            report['recommendations'].append("La humedad es alta, considera usar deshumidificador")
        if current_data['co2_ppm'] > 1000:
            report['recommendations'].append("Ventila el ambiente para mejorar la calidad del aire")
        
        return jsonify(report)
        
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)