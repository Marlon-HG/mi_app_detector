from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from tensorflow.keras.models import load_model
from PIL import Image
import numpy as np
import cv2
import math
import io
import mysql.connector
from mysql.connector import Error
from decimal import Decimal, getcontext

# Configurar precisión para factorial grande
getcontext().prec = 10000

app = FastAPI()

# Static and template folders
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

modelo = load_model("modelo_mnist.keras")

def factorial_reducido(n: int) -> str:
    try:
        if n > 10000:
            return "Demasiado grande (limite 10,000)"
        result = Decimal(1)
        for i in range(2, n + 1):
            result *= i
        result_str = str(result.normalize())
        return f"{result_str[:10]}e+{len(result_str) - 1}" if len(result_str) > 15 else result_str
    except:
        return "Factorial no disponible"

def numero_a_palabras(numero: int) -> str:
    unidades = ["", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve"]
    decenas = ["", "diez", "veinte", "treinta", "cuarenta", "cincuenta", "sesenta", "setenta", "ochenta", "noventa"]
    centenas = ["", "cien", "doscientos", "trescientos", "cuatrocientos", "quinientos", "seiscientos",
                "setecientos", "ochocientos", "novecientos"]

    if numero == 0:
        return "cero"
    if numero < 10:
        return unidades[numero]
    if numero < 100:
        return decenas[numero // 10] + (" y " + unidades[numero % 10] if numero % 10 != 0 else "")
    if numero < 1000:
        if numero == 100:
            return "cien"
        return centenas[numero // 100] + (" " + numero_a_palabras(numero % 100) if numero % 100 != 0 else "")
    if numero < 10000:
        miles = numero // 1000
        resto = numero % 1000
        mil_texto = "mil" if miles == 1 else unidades[miles] + " mil"
        return mil_texto + (" " + numero_a_palabras(resto) if resto != 0 else "")
    if numero < 100000:
        decenas_miles = numero // 1000
        resto = numero % 1000
        return numero_a_palabras(decenas_miles) + " mil" + (" " + numero_a_palabras(resto) if resto != 0 else "")
    return str(numero)

def analizar_imagen(imagen_pil):
    img = np.array(imagen_pil.convert("L"))
    img = cv2.bitwise_not(img)
    _, thresh = cv2.threshold(img, 100, 255, cv2.THRESH_BINARY)
    kernel = np.ones((2, 2), np.uint8)
    thresh = cv2.dilate(thresh, kernel, iterations=1)
    contornos, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contornos = sorted(contornos, key=lambda c: cv2.boundingRect(c)[0])
    digitos = []
    for c in contornos:
        x, y, w, h = cv2.boundingRect(c)
        if w < 5 or h < 5:
            continue
        roi = thresh[y:y+h, x:x+w]
        roi = cv2.resize(roi, (18, 18))
        roi = cv2.copyMakeBorder(roi, 5, 5, 5, 5, cv2.BORDER_CONSTANT, value=0)
        roi = roi.astype("float32") / 255.0
        roi = np.expand_dims(roi, axis=-1)
        roi = np.expand_dims(roi, axis=0)
        pred = modelo.predict(roi, verbose=0)
        digito = np.argmax(pred)
        digitos.append(str(digito))
    return "".join(digitos)

def insertar_en_base(numero: str, factorial: str, nombre: str = "Marlon Estuardo Hernández Girón") -> str:
    try:
        connection = mysql.connector.connect(
            host="www.server.daossystem.pro",
            port=3301,
            database="bd_ia_lf_2025",
            user="usr_ia_lf_2025",
            password="5sr_31_lf_2025"
        )
        if connection.is_connected():
            cursor = connection.cursor()
            query = """
                INSERT INTO segundo_parcial (valor, factorial, nombre_estudiante)
                VALUES (%s, %s, %s)
            """
            cursor.execute(query, (numero, factorial, nombre))
            connection.commit()
            return "✅ Datos insertados correctamente."
    except Error as e:
        return f"❌ Error al insertar en base de datos: {str(e)}"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/detectar")
async def detectar_numero(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        imagen_pil = Image.open(io.BytesIO(contents))
        numero = analizar_imagen(imagen_pil)
        if not numero:
            raise HTTPException(status_code=400, detail="No se detectó ningún número.")
        numero = numero.strip()[:10]
        if not numero.isdigit():
            raise HTTPException(status_code=400, detail="Número inválido detectado.")
        num_int = int(numero)
        resultado = {
            "numero": numero,
            "palabras": numero_a_palabras(num_int),
            "factorial": factorial_reducido(num_int),
        }
        resultado["mensaje_db"] = insertar_en_base(numero, resultado["factorial"])
        return JSONResponse(content=resultado)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
