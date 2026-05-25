# Sistema de Reconocimiento Facial para Raspberry Pi

Sistema completo de reconocimiento facial que detecta rostros en tiempo real, graba clips de video cuando detecta un rostro, identifica a la persona comparando con una base de datos de embeddings, y envía alertas al backend mediante API.

## Modelos Utilizados

### Detección y Reconocimiento: InsightFace (buffalo_l)

Por defecto el sistema usa **InsightFace** con el modelo `buffalo_l`, que incluye:

- **RetinaFace** para detección: WIDER FACE hard test set - AP 91.4%
- **Embeddings (ResNet50 + ArcFace)** para reconocimiento

Los embeddings se extraen directamente de cada detección (`normed_embedding`) sin necesidad de un modelo MobileFaceNet separado. Son 512 dimensiones, L2-normalizados.

#### Métricas de referencia para comparación (fuente oficial)

Las métricas comparables para `buffalo_l` y `buffalo_s` están publicadas en el **InsightFace Model Zoo** (misma implementación y mismo protocolo de evaluación para ambos packs):

| Model Pack | Backbone | LFW | CFP-FP | AgeDB-30 | IJB-B (TAR@FAR=1e-4) | IJB-C (TAR@FAR=1e-4) | MegaFace (Rank-1@1e-6) |
|------------|----------|-----|--------|----------|----------------------|----------------------|-------------------------|
| `buffalo_l` | ResNet50 + ArcFace | 99.83 | 99.33 | 98.23 | 93.16 | 90.29 | 74.96 |
| `buffalo_s` | MobileFaceNet + ArcFace | 99.70 | 98.00 | 96.58 | 73.39 | 69.45 | 51.03 |

Fuente: [InsightFace Model Zoo - Recognition accuracy of python library model packs](https://github.com/deepinsight/insightface/tree/master/model_zoo)

Para evaluación tipo ROC/AUC en verificación, prioriza datasets como **IJB-B/IJB-C** (TAR@FAR), ya que LFW suele estar saturado cerca de 99%.

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
- **InsightFace** (RetinaFace + embeddings): se descarga automáticamente vía `buffalo_l`
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
RECOGNITION_THRESHOLD=0.35
FACE_DETECTION_CONFIDENCE=0.5

# Video
CLIP_DURATION_SECONDS=10
VIDEO_OUTPUT_DIR=./videos
VIDEO_FPS=30

# Base de datos
KNOWN_FACES_DIR=./known_faces
DATABASE_DIR=./database

# Imágenes por identidad (para build_database.py)
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
- **Producción**: Configurar la URL del backend según tu despliegue.

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

Para obtener imágenes reales rápidamente sin buscar fotos manualmente, usa el dataset LFW (Labeled Faces in the Wild). La descarga está integrada en el script de evaluación offline:

```bash
python scripts/evaluate_offline.py \
    --download-lfw /tmp/lfw \
    --output evaluacion_lfw.xlsx \
    --max-people 100 --min-photos 8
```

Esto descarga ~172 MB la primera vez y guarda imágenes en el directorio indicado, sin necesidad de TensorFlow.

### 2. Construir base de datos de embeddings

```bash
python database/build_database.py
```

Este script:
- Detecta rostros en todas las imágenes (RetinaFace)
- Extrae embeddings usando InsightFace directamente de cada detección original (o MobileFaceNet como fallback)
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
│   ├── evaluate_offline.py        # Evaluación offline con LFW u otras fotos
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
- Reduce `RETINAFACE_DET_SIZE` en `.env` (ej: `RETINAFACE_DET_SIZE=480,480`). El valor por defecto es 640×640, optimizado para precisión; reducirlo mejora la velocidad a costa de detectar peor rostros pequeños o lejanos.
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

## Protocolo de Evaluación (ROC/AUC y TAR@FAR)

Para comparar tu sistema con benchmarks de papers, evalua verificacion facial con pares
de imagenes y similitud coseno sobre embeddings normalizados.

### 1. Construir pares de evaluacion

- Pares genuinos (misma identidad): etiqueta `1`
- Pares impostores (identidades distintas): etiqueta `0`
- Recomendado: particion por sujeto (sin mezclar la misma persona entre train y test)
- Recomendado: incluir variaciones reales (iluminacion, distancia, angulo, oclusion)

### 2. Extraer scores

Para cada par, calcula el score de verificacion:

- $s = e_1 \cdot e_2$ (coseno, con embeddings L2-normalizados)

Guarda dos arreglos:

- `y_true`: etiquetas binarias (0/1)
- `y_score`: score de similitud por par

### 3. Calcular ROC/AUC y TAR@FAR

Ejemplo reproducible con `scikit-learn`:

```python
import numpy as np
from sklearn.metrics import roc_curve, roc_auc_score

def tar_at_far(y_true, y_score, target_far=1e-4):
  fpr, tpr, thr = roc_curve(y_true, y_score)
  valid = np.where(fpr <= target_far)[0]
  if len(valid) == 0:
    return 0.0, None
  idx = valid[-1]
  return float(tpr[idx]), float(thr[idx])

# y_true: array (N,) con 0/1
# y_score: array (N,) con similitud coseno
auc = roc_auc_score(y_true, y_score)
tar_1e4, thr_1e4 = tar_at_far(y_true, y_score, target_far=1e-4)
tar_1e5, thr_1e5 = tar_at_far(y_true, y_score, target_far=1e-5)

print(f"AUC: {auc:.6f}")
print(f"TAR@FAR=1e-4: {tar_1e4:.6f} (thr={thr_1e4})")
print(f"TAR@FAR=1e-5: {tar_1e5:.6f} (thr={thr_1e5})")
```

### 4. Comparar con referencias oficiales

Para comparacion justa:

- Usa el mismo tipo de metrica reportada por la referencia (por ejemplo TAR@FAR en IJB-B/IJB-C)
- Reporta el tamaño del set, protocolo de particion y condiciones de captura
- No uses solo accuracy en LFW para decisiones de produccion (tiende a saturar)

Valores de referencia publicados para comparar `buffalo_l` vs `buffalo_s` estan en:

- [InsightFace Model Zoo](https://github.com/deepinsight/insightface/tree/master/model_zoo)

Si quieres aproximar el comportamiento de IJB-C, reporta al menos:

- AUC
- TAR@FAR=1e-4
- TAR@FAR=1e-5
- Threshold seleccionado y criterio de seleccion (por ejemplo max TPR con FAR objetivo)

## Referencias

### InsightFace / RetinaFace
- Paper RetinaFace: [arXiv:1905.00641](https://arxiv.org/abs/1905.00641)
- Paper ArcFace (loss usada en buffalo_l y buffalo_s): [arXiv:1801.07698](https://arxiv.org/abs/1801.07698)
- Paper MobileFaceNet (backbone de buffalo_s): [arXiv:1804.07573](https://arxiv.org/abs/1804.07573)
- InsightFace Model Zoo (métricas oficiales por model pack): [model_zoo](https://github.com/deepinsight/insightface/tree/master/model_zoo)

## Licencia

Ver licencia del proyecto principal.
