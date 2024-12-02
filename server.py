from flask import Flask, request, send_file, jsonify, Response
import numpy as np
import cv2
import face_recognition
import os
 
app = Flask("Recive-image")

# Ruta del archivo recibido
received_image_path = 'received_image.byn'
processed_image_path = 'received_image.jpg'

# Endpoint para subir la imagen
@app.route('/upload', methods=['POST'])
def upload_image():
    if request.data:
        # Eliminar el archivo anterior si existe
        if os.path.exists(received_image_path):
            os.remove(received_image_path)
            print('Previous image deleted.')

        if os.path.exists(processed_image_path):
            os.remove(processed_image_path)
            print('Processed image deleted.')

        # Guardar el nuevo archivo
        with open(received_image_path, 'wb') as f:
            f.write(request.data)
        print('Image received and saved as received_image.byn')
        return 'Image received', 200
    else:
        print('No image data found in request')
        return 'No image data found in request', 400

# Endpoint para descargar la imagen
@app.route('/download', methods=['GET'])
def download_image():
    try:
        return send_file(received_image_path, as_attachment=True)
    except Exception as e:
        return str(e), 500

# Endpoint para procesar la imagen y mostrar el resultado
@app.route('/process', methods=['GET'])
def process_image():
    try:
        print("Processing image...")
       
        # Leer la imagen guardada
        with open(received_image_path, 'rb') as f:
            image_data = f.read()

        # Convertir los datos binarios a un array de numpy
        image_array = np.frombuffer(image_data, dtype=np.uint8)

        # Decodificar la imagen comprimida
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        if image is None:
            print("Error: No se pudo decodificar la imagen.")
            return 'Error: No se pudo decodificar la imagen.', 500

        # Redimensionar la imagen a 1024x960
        image_resized = cv2.resize(image, (1024, 960))

        # Guardar la imagen redimensionada para verificar que se envió correctamente
        cv2.imwrite(processed_image_path, image_resized)

        # Cargar la imagen de referencia
        imagen_referencia = face_recognition.load_image_file('imagen_gris.jpg')
        encodings_referencia = face_recognition.face_encodings(imagen_referencia)

        if len(encodings_referencia) == 0:
            return 'No se encontró un rostro en la imagen de referencia.', 500

        encoding_referencia = encodings_referencia[0]

        # Cargar la imagen de prueba
        imagen_prueba = face_recognition.load_image_file(processed_image_path)
        ubicaciones_rostros_prueba = face_recognition.face_locations(imagen_prueba)
        encodings_prueba = face_recognition.face_encodings(imagen_prueba, ubicaciones_rostros_prueba)

        # Crear una copia para mostrar resultados
        imagen_prueba_bgr = cv2.cvtColor(imagen_prueba, cv2.COLOR_RGB2BGR)

        if not ubicaciones_rostros_prueba:
            # Si no se detectan rostros, agregar un mensaje en la imagen
            mensaje = "No se detectaron rostros"
            cv2.putText(imagen_prueba_bgr, mensaje, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        else:
            # Iterar sobre los rostros encontrados
            for (ubicacion, encoding_prueba) in zip(ubicaciones_rostros_prueba, encodings_prueba):
                # Comparar el rostro con el rostro aprendido
                resultados = face_recognition.compare_faces([encoding_referencia], encoding_prueba)
                distancia = face_recognition.face_distance([encoding_referencia], encoding_prueba)

                # Obtener coordenadas del rostro
                top, right, bottom, left = ubicacion

                # Dibujar un rectángulo alrededor del rostro
                color = (0, 255, 0) if resultados[0] else (0, 0, 255)
                cv2.rectangle(imagen_prueba_bgr, (left, top), (right, bottom), color, 2)

                # Mostrar el nombre si hay coincidencia
                texto = f"Juan Esteban ({distancia[0]:.2f})" if resultados[0] else "Desconocido"
                cv2.putText(imagen_prueba_bgr, texto, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Convertir la imagen a formato JPEG
        _, buffer = cv2.imencode('.jpg', imagen_prueba_bgr)
        response_image = buffer.tobytes()

        return Response(response_image, mimetype='image/jpeg')

    except Exception as e:
        print(f"Error: {e}")
        return str(e), 500


@app.route('/hello', methods=['GET'])
def function_hello():
    return 'Hello'

app.run(host='0.0.0.0', port=5000)