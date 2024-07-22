import time
import Adafruit_PCA9685  # Biblioteca para controlar el PCA9685 PWM driver
import serial  # Biblioteca para comunicación serial
from simple_pid import PID  # Biblioteca para control PID
from flask import Flask, request, jsonify  # Biblioteca para crear la API web
import requests  # Biblioteca para enviar solicitudes HTTP
import unittest  # Biblioteca para pruebas unitarias

# URL del sistema de visión artificial
VISION_SYSTEM_URL = 'http://localhost:30000'  # Cambia la URL según sea necesario

class ActuatorControl:
    def __init__(self):
        """Inicializa el control del actuador con configuraciones predeterminadas."""
        self.servo_channel = 0  # Canal del servomotor en el PCA9685
        self.servo_min = 150  # Pulso mínimo para el servomotor
        self.servo_max = 600  # Pulso máximo para el servomotor
        self.pwm = Adafruit_PCA9685.PCA9685()  # Crea una instancia del controlador PCA9685
        self.pwm.set_pwm_freq(50)  # Configura la frecuencia del PWM a 50 Hz
        self.serial_port = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)  # Configura el puerto serial
        self.pid = PID(1, 0.1, 0.05, setpoint=90)  # Crea una instancia del controlador PID con valores predeterminados

    def set_servo_pulse(self, channel, pulse):
        """Configura el pulso del servomotor en el canal especificado.
        
        Args:
            channel (int): Canal del servomotor en el PCA9685.
            pulse (int): Valor del pulso a configurar.
        """
        pulse_length = 1000000.0 / 60 / 4096  # Calcula la longitud del pulso
        pulse *= 1000  # Convierte el pulso a microsegundos
        pulse /= pulse_length  # Calcula el pulso PWM
        self.pwm.set_pwm(channel, 0, int(pulse))  # Configura el pulso en el PCA9685
    
    def calculate_servo_position(self, angle):
        """Convierte el ángulo en una posición de pulso para el servomotor.
        
        Args:
            angle (float): Ángulo deseado para el servomotor.
        
        Returns:
            float: Valor del pulso correspondiente al ángulo.
        """
        pulse_range = self.servo_max - self.servo_min  # Rango de pulsos del servomotor
        return self.servo_min + (angle / 180.0) * pulse_range  # Calcula la posición del pulso
    
    def move_actuator(self, angle):
        """Mueve el actuador a un ángulo específico.
        
        Args:
            angle (float): Ángulo objetivo para el actuador.
        """
        pulse = self.calculate_servo_position(angle)  # Calcula el pulso para el ángulo
        self.set_servo_pulse(self.servo_channel, pulse)  # Configura el pulso en el servomotor
        time.sleep(1)  # Espera 1 segundo para permitir que el actuador se mueva
    
    def move_actuator_incremental(self, start_angle, end_angle, increment):
        """Mueve el actuador en incrementos de ángulo.
        
        Args:
            start_angle (float): Ángulo inicial.
            end_angle (float): Ángulo final.
            increment (float): Incremento de ángulo por paso.
        """
        for angle in range(start_angle, end_angle + 1, increment):  # Recorre los ángulos en incrementos
            self.move_actuator(angle)  # Mueve el actuador al ángulo actual
    
    def send_command_serial(self, command):
        """Envía un comando al actuador a través del puerto serial.
        
        Args:
            command (str): Comando a enviar al actuador.
        """
        self.serial_port.write(command.encode())  # Envía el comando al puerto serial
    
    def activate_cutting_mechanism(self):
        """Activa el mecanismo de corte del actuador enviando un comando al puerto serial."""
        self.send_command_serial('ACTIVATE_CUT')  # Comando para activar el mecanismo de corte
        time.sleep(1)  # Espera para asegurar que el comando se ejecute
    
    def calibrate_actuator(self, start_angle, end_angle):
        """Calibra el actuador moviéndolo a un rango de ángulos.
        
        Args:
            start_angle (float): Ángulo inicial para la calibración.
            end_angle (float): Ángulo final para la calibración.
        """
        self.move_actuator(start_angle)  # Mueve el actuador al ángulo inicial
        self.move_actuator(end_angle)  # Mueve el actuador al ángulo final
    
    def detect_obstacles(self):
        """Detecta obstáculos que puedan interferir con el actuador.
        
        Returns:
            bool: True si se detectan obstáculos, False en caso contrario.
        """
        # Implementa tu lógica para detectar obstáculos aquí
        return False  # Simulación, cambiar según el sensor utilizado
    
    def move_safely(self, angle):
        """Mueve el actuador de forma segura, considerando posibles obstáculos.
        
        Args:
            angle (float): Ángulo objetivo para el actuador.
        """
        if not self.detect_obstacles():  # Verifica si hay obstáculos
            self.move_actuator(angle)  # Mueve el actuador si no hay obstáculos
        else:
            print("Obstáculo detectado. Movimiento cancelado.")  # Mensaje de advertencia
    
    def optimize_speed(self, angle, speed):
        """Optimiza la velocidad del movimiento del actuador.
        
        Args:
            angle (float): Ángulo objetivo para el actuador.
            speed (float): Velocidad de movimiento en segundos.
        """
        pulse = self.calculate_servo_position(angle)  # Calcula el pulso para el ángulo
        self.set_servo_pulse(self.servo_channel, pulse)  # Configura el pulso en el servomotor
        time.sleep(speed)  # Espera según la velocidad especificada
    
    def log_movement(self, start_angle, end_angle):
        """Registra el movimiento del actuador en un archivo de log.
        
        Args:
            start_angle (float): Ángulo inicial del movimiento.
            end_angle (float): Ángulo final del movimiento.
        """
        with open('actuator_log.txt', 'a') as f:  # Abre el archivo de log en modo append
            f.write(f'Movimiento de {start_angle} a {end_angle} en {time.ctime()}\n')  # Registra el movimiento
    
    def move_servo_smoothly(self, start_angle, end_angle, movement_speed):
        """Mueve el servomotor suavemente entre dos ángulos y registra el movimiento.
        
        Args:
            start_angle (float): Ángulo inicial del movimiento.
            end_angle (float): Ángulo final del movimiento.
            movement_speed (float): Velocidad de movimiento en segundos.
        """
        start_pulse = self.calculate_servo_position(start_angle)  # Calcula el pulso para el ángulo inicial
        end_pulse = self.calculate_servo_position(end_angle)  # Calcula el pulso para el ángulo final
        steps = abs(end_angle - start_angle) // 1  # Calcula el número de pasos
        for step in range(steps + 1):  # Recorre los pasos
            angle = start_angle + step * (end_angle - start_angle) / steps  # Calcula el ángulo actual
            pulse = self.calculate_servo_position(angle)  # Calcula el pulso para el ángulo actual
            self.set_servo_pulse(self.servo_channel, pulse)  # Configura el pulso en el servomotor
            self.log_movement(start_angle, angle)  # Registra el movimiento
            time.sleep(movement_speed)  # Espera según la velocidad de movimiento
    
    def control_pid(self, target_angle):
        """Controla el actuador usando un controlador PID para precisión.
        
        Args:
            target_angle (float): Ángulo objetivo para el actuador.
        """
        current_angle = 0  # Leer ángulo actual del actuador aquí
        control = self.pid(current_angle)  # Calcula la salida del PID
        self.move_actuator(control)  # Mueve el actuador al ángulo calculado

# Configuración del servidor web usando Flask
app = Flask(__name__)
actuator = ActuatorControl()  # Crea una instancia de ActuatorControl

@app.route('/receive_data', methods=['POST'])
def receive_data():
    """Recibe datos del estado del cable y mueve el actuador si el cable está muerto."""
    try:
        data = request.json  # Obtiene los datos JSON del request
        cable_status = data.get('cable_status')  # Obtiene el estado del cable
        if cable_status == 'dead':  # Si el cable está muerto
            actuator.activate_cutting_mechanism()  # Activa el mecanismo de corte
            actuator.move_servo_smoothly(0, 90, 0.1)  # Mueve el actuador para cortar el cable
            return jsonify({"status": "success", "message": "Mecanismo de corte activado y actuador movido"}), 200
        else:
            return jsonify({"status": "success", "message": "No se requiere acción"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500  # Manejo de errores

@app.route('/send_command', methods=['POST'])
def send_command():
    """Envía comandos al sistema de visión artificial."""
    try:
        command = request.json.get('command')  # Obtiene el comando del request
        response = requests.post(VISION_SYSTEM_URL, json={'command': command})  # Envía el comando al sistema de visión
        return jsonify(response.json()), response.status_code  # Devuelve la respuesta del sistema de visión
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500  # Manejo de errores

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)  # Inicia el servidor web en el puerto 5000

# Configuración del servidor web para el sistema de visión artificial
app_vision = Flask(__name__)

@app_vision.route('/detect', methods=['POST'])
def detect():
    """Detecta el estado del cable basado en el comando recibido."""
    try:
        command = request.json.get('command')  # Obtiene el comando del request
        cable_status = 'dead' if command == 'cut_cable' else 'alive'  # Determina el estado del cable basado en el comando
        return jsonify({"cable_status": cable_status}), 200  # Devuelve el estado del cable
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500  # Manejo de errores

if __name__ == '__main__':
    app_vision.run(host='0.0.0.0', port=5001, debug=True)  # Inicia el servidor web para el sistema de visión en el puerto 5001

# Pruebas y validación
class TestActuatorControl(unittest.TestCase):
    def setUp(self):
        """Configura el entorno de pruebas."""
        self.actuator = ActuatorControl()  # Crea una instancia de ActuatorControl para las pruebas

    def test_calculate_servo_position(self):
        """Prueba la función calculate_servo_position para verificar la conversión de ángulo a pulso."""
        angle = 90  # Ángulo de prueba
        expected_pulse = self.actuator.servo_min + (angle / 180.0) * (self.actuator.servo_max - self.actuator.servo_min)  # Pulso esperado
        pulse = self.actuator.calculate_servo_position(angle)  # Calcula el pulso
        self.assertAlmostEqual(pulse, expected_pulse, delta=1)  # Compara el pulso calculado con el esperado

    def test_move_servo_smoothly(self):
        """Prueba la función move_servo_smoothly para verificar el movimiento suave del servomotor."""
        try:
            self.actuator.move_servo_smoothly(0, 90, 0.1)  # Mueve el servomotor de 0 a 90 grados
        except Exception as e:
            self.fail(f'Error en move_servo_smoothly: {e}')  # Reporta errores si ocurren

if __name__ == '__main__':
    unittest.main()  # Ejecuta las pruebas unitarias
