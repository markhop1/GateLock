# Sistema de Reconocimiento Facial para Raspberry Pi

Sistema completo de reconocimiento facial que detecta rostros en tiempo real, graba clips de video cuando detecta un rostro, identifica a la persona comparando con una base de datos de embeddings (generada con augmentación), y envía alertas al backend mediante API.

## Modelos Utilizados

### Detección y Reconocimiento: InsightFace (buffalo_s)

Por defecto el sistema usa **InsightFace** con el modelo `buffalo_s`, que incluye:

- **RetinaFace** para detección: WIDER FACE hard test set - AP 91.4%
- **Embeddings (MBF/MobileFaceNet pre-entrenado)** para reconocimiento: LFW 99.70%, CFP-FP 98%

Los embeddings se extraen directamente de cada detección (`normed_embedding`) sin necesidad de un modelo MobileFaceNet separado. Son 512 dimensiones, L2-normalizados.

### Fallback: MobileFaceNet (TensorFlow)

Si no hay modelo InsightFace o no proporciona embedding, se usa **MobileFaceNet** vía TensorFlow/Keras (128 dimensiones). Para que sea útil, hay que configurar un modelo pre-entrenado en `config/config.py`.

## Requisitos

- Raspberry Pi 5 (recomendado) o Raspberry Pi 4
- Python 3.11
- Cámara USB o cámara oficial de Raspberry Pi
- Conexión a internet (para descargar modelos la primera vez)

## Instalación

### 1. Instalar dependencias del sistema

```bash
sudo apt update
sudo apt install python3-venv python3-full python3-opencv -y
```

**Python 3.11**: Raspberry Pi OS Bookworm (2024) incluye Python 3.11 por defecto. Si usas una versión anterior, instala Python 3.11 manualmente (TensorFlow no funciona con Python 3.13+).

### 2. Crear entorno virtual con Python 3.11

```bash
cd raspberry-pi
python3.11 -m venv .venv
source .venv/bin/activate
```

Si `python3.11` no está disponible, usa `python3` (en Bookworm es 3.11). Comprueba con `python3 --version`.

### 3. Instalar dependencias Python

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Nota**: La instalación de TensorFlow y InsightFace puede tardar varios minutos.

### 4. Descargar modelos

Los modelos se descargarán automáticamente la primera vez que ejecutes el programa:
- **InsightFace** (RetinaFace + embeddings): se descarga automáticamente vía `buffalo_s`
- **MobileFaceNet** (fallback): Solo si InsightFace no está disponible. Opcionalmente configura `MOBILEFACENET_MODEL_PATH` en `config/config.py` para un modelo pre-entrenado.

## Configuración

### Variables de entorno

Crea un archivo `.env` en el directorio `raspberry-pi/`:

```env
# API Backend
API_BASE_URL=http://localhost:5000/api
API_USERNAME=tu_usuario
API_PASSWORD=tu_contraseña

# Cámara
CAMERA_INDEX=0

# Reconocimiento
RECOGNITION_THRESHOLD=0.5
FACE_DETECTION_CONFIDENCE=0.5

# Video
CLIP_DURATION_SECONDS=10
VIDEO_OUTPUT_DIR=./videos
VIDEO_FPS=30

# Base de datos
KNOWN_FACES_DIR=./known_faces
DATABASE_DIR=./database

# Augmentación
AUG_PER_IMAGE=20
MAX_IMAGES_PER_ID=10
```

Puedes copiar `cp .env.example .env` y editar los valores.

### Conexión con el backend

La Raspberry Pi se conecta al backend para subir videos y crear alertas. Configura:

| Variable | Descripción | Ejemplo (red local) |
|----------|-------------|---------------------|
| `API_BASE_URL` | URL del backend (debe ser accesible desde la Raspberry) | `http://192.168.0.12:5000/api` |
| `API_USERNAME` | Email de una cuenta registrada en la app (el backend usa email para login) | `tu@email.com` |
| `API_PASSWORD` | Contraseña del usuario | `********` |

**Ejemplos por entorno:**
- **Mismo equipo**: `API_BASE_URL=http://localhost:5000/api`
- **Red local** (backend en 192.168.0.12): `API_BASE_URL=http://192.168.0.12:5000/api`
- **Producción**: `API_BASE_URL=https://api.tudominio.com/api`

**Verificar conexión:**
```bash
python tests/test_api_auth.py
python tests/test_api_client.py --real-backend
```

Al arrancar, el sistema comprueba la conexión tras autenticarse y registra un aviso si el backend no está alcanzable.

## Uso

### 1. Preparar imágenes de rostros conocidos

Coloca imágenes de cada persona en:
```
known_faces/
  persona1/
    foto1.jpg
    foto2.jpg
    ...
  persona2/
    foto1.jpg
    ...
```

**Recomendaciones**:
- Usa varias fotos por persona (mínimo 3-5)
- Diferentes ángulos y condiciones de iluminación
- Rostros centrados y bien visibles
- Buena calidad de imagen

#### Descargar imágenes de prueba con LFW (opcional)

Para obtener imágenes reales rápidamente sin buscar fotos manualmente, usa el dataset LFW (Labeled Faces in the Wild):

```bash
pip install tensorflow-datasets
python scripts/download_lfw_fixtures.py
```

Esto descarga ~172 MB la primera vez y guarda imágenes en `known_faces/` (5 personas, 5 fotos cada una por defecto).

Opciones:
```bash
# Cambiar destino (p. ej. para fixtures de tests)
python scripts/download_lfw_fixtures.py --output tests/fixtures/test_images

# Más personas e imágenes
python scripts/download_lfw_fixtures.py --max-people 10 --max-images-per 8
```

### 2. Construir base de datos de embeddings

```bash
python database/build_database.py
```

Este script:
- Detecta rostros en todas las imágenes (RetinaFace)
- Aplica augmentación para mejorar robustez
- Genera embeddings usando InsightFace (o MobileFaceNet como fallback)
- Guarda `face_embeddings.npy` y `face_labels.npy` en `database/`

### 3. Ejecutar sistema de reconocimiento

```bash
# Sin preview (recomendado para producción)
python main.py

# Con preview (para debugging)
python main.py --preview
```

El sistema:
1. Detecta rostros en tiempo real usando RetinaFace
2. Graba clips de 10 segundos cuando detecta un rostro
3. Extrae embeddings y compara con la base de datos
4. Si reconoce a alguien (similitud > threshold):
   - Guarda el clip con el nombre `clip_{identidad}_{timestamp}.mp4`
   - Sube el video al backend
   - Crea una alerta con el resultado

**Presiona 'q' en la ventana de preview para salir** (si usas `--preview`)

## Estructura del Proyecto

```
raspberry-pi/
├── config/              # Configuración
│   └── config.py
├── scripts/             # Utilidades
│   ├── download_lfw_fixtures.py   # Descarga imágenes LFW para known_faces
│   └── run_all_tests.py
├── database/            # Base de datos de embeddings
│   ├── build_database.py
│   └── face_db.py
├── detection/           # Detección de rostros
│   └── face_detector.py
├── recognition/         # Reconocimiento facial
│   └── face_recognizer.py
├── video/               # Grabación de clips
│   └── video_recorder.py
├── api/                 # Comunicación con backend
│   ├── auth.py
│   └── client.py
├── main.py              # Programa principal
├── requirements.txt
└── README.md
```

## Troubleshooting

### Error: "InsightFace no está disponible"
```bash
pip install insightface onnxruntime
```

### Error: "TensorFlow no está disponible" o "No module named 'imp'"
TensorFlow no es compatible con Python 3.13+. Usa Python 3.11 o 3.12:
```bash
# Elimina el venv actual y crea uno con Python 3.11
rm -rf .venv
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Error: "No se pudo abrir la cámara"
- Verifica que la cámara esté conectada: `lsusb`
- Prueba diferentes índices de cámara en `CAMERA_INDEX`
- Verifica permisos: `sudo usermod -a -G video $USER` (luego reinicia sesión)

### Error: "Base de datos no disponible"
Ejecuta `python database/build_database.py` primero.

### Rendimiento lento
- Reduce `RETINAFACE_DET_SIZE` en `config/config.py` (ej: (240, 240))
- InsightFace ya usa embeddings pre-entrenados (no requiere MobileFaceNet extra)
- Considera usar GPU si está disponible

### Advertencias QFontDatabase / fuentes Qt (al usar --preview)
Si ves `QFontDatabase: Cannot find font directory .../cv2/qt/fonts`, OpenCV no encuentra fuentes para el texto en la ventana de preview. Instala fuentes del sistema:
```bash
sudo apt install fonts-dejavu-core
```
O crea un enlace al directorio de fuentes (ajusta la ruta a tu `.venv`):
```bash
FONTS_DIR=".venv/lib/python3.11/site-packages/cv2/qt/fonts"
mkdir -p "$FONTS_DIR"
sudo ln -s /usr/share/fonts/truetype/dejavu/ "$FONTS_DIR/"
```

## Testing

El proyecto incluye scripts de prueba para validar cada componente individualmente y tests unitarios para CI.

### Instalación de dependencias de testing

```bash
pip install -r requirements-dev.txt
```

### Tests Unitarios (para CI/GitHub Actions)

Ejecuta solo tests que no requieren hardware:

```bash
# Todos los tests unitarios
pytest tests/unit/ -v

# Test específico
pytest tests/unit/test_config.py -v
```

### Scripts de Prueba Individuales (para Raspberry Pi)

Cada componente tiene su propio script de prueba:

```bash
# Prueba detección de rostros
python tests/test_detection.py --camera
python tests/test_detection.py --image path/to/image.jpg

# Prueba reconocimiento facial
python tests/test_recognition.py --image path/to/face.jpg

# Prueba base de datos
python tests/test_database.py

# Prueba grabación de video
python tests/test_video_recorder.py
python tests/test_video_recorder.py --camera

# Prueba autenticación API
python tests/test_api_auth.py
python tests/test_api_auth.py --skip-login

# Prueba cliente API (con mock)
python tests/test_api_client.py --mock

# Prueba construcción de base de datos
python tests/test_build_database.py
```

### Ejecutar Todos los Tests

Script maestro que ejecuta todos los tests en orden:

```bash
# Todos los tests
python scripts/run_all_tests.py

# Saltar tests que requieren cámara
python scripts/run_all_tests.py --skip-camera

# Saltar tests que requieren API backend
python scripts/run_all_tests.py --skip-api

# Solo tests unitarios
python scripts/run_all_tests.py --unit-only

# Solo tests de una categoría
python scripts/run_all_tests.py --category unit
python scripts/run_all_tests.py --category integration
```

### Tests en GitHub Actions

Los tests unitarios se ejecutan automáticamente en GitHub Actions cuando se modifican archivos en `raspberry-pi/`. Estos tests:

- Verifican imports y estructura básica
- Ejecutan tests de lógica sin modelos ML
- Validan sintaxis y configuración
- **No requieren** hardware ni modelos pesados

**Limitaciones de CI**:
- No ejecuta tests que requieren cámara
- No ejecuta tests que requieren modelos ML descargados
- No ejecuta tests de integración completa
- Solo verifica lógica, estructura e imports

Para validación completa, ejecuta los tests en tu Raspberry Pi antes de hacer commit.

## Referencias

### InsightFace / RetinaFace
- Paper RetinaFace: [arXiv:1905.00641](https://arxiv.org/abs/1905.00641)
- Embeddings (buffalo_s): LFW 99.70%, CFP-FP 98%

## Licencia

Ver licencia del proyecto principal.
