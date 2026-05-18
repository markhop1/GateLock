"""
Registro de eventos de reconocimiento para sesiones de evaluación.

Escribe una fila CSV por cada evento de detección de rostro, en modo append,
para que los datos estén seguros aunque el programa se interrumpa.

Formato del CSV:
    timestamp, event_id, predicted_name, similarity, matched,
    threshold_used, true_name (vacío — rellenar en Excel tras la sesión)

Deduplicación:
    La misma cara puede aparecer en decenas de frames seguidos. Para no generar
    miles de filas idénticas se aplica un cooldown por identidad: solo se registra
    un nuevo evento si han pasado más de MIN_EVENT_GAP_SECONDS desde el último
    evento de ese predicted_name.
"""

import csv
import logging
import time
import uuid
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Segundos mínimos entre dos eventos del mismo predicted_name para considerarlos
# eventos distintos (nueva aproximación a la cámara).
MIN_EVENT_GAP_SECONDS: float = 3.0

# Columnas del CSV
FIELDNAMES = [
    "timestamp",
    "event_id",
    "predicted_name",
    "similarity",
    "matched",
    "threshold_used",
    "true_name",   # ← rellenar manualmente en Excel tras la sesión
    "notes",       # ← campo libre para anotar en Excel
]


class SessionLogger:
    """
    Registra eventos de reconocimiento facial en un CSV.

    Uso típico:
        session_logger = SessionLogger(Path("evaluation/sessions/session_001.csv"))
        session_logger.log_event(predicted_name="alice", similarity=0.72, matched=True, threshold=0.35)
        session_logger.log_event(predicted_name=None, similarity=0.21, matched=False, threshold=0.35)
    """

    def __init__(self, csv_path: Path, min_event_gap: float = MIN_EVENT_GAP_SECONDS):
        self.csv_path = Path(csv_path)
        self.min_event_gap = min_event_gap
        self._last_event_time: dict[str, float] = {}  # predicted_key -> last log timestamp
        self._file = None
        self._writer = None
        self._open()

    def _open(self) -> None:
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        new_file = not self.csv_path.exists()
        self._file = open(self.csv_path, "a", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._file, fieldnames=FIELDNAMES)
        if new_file:
            self._writer.writeheader()
            self._file.flush()
        logger.info(f"SessionLogger: registrando en {self.csv_path}")

    def log_event(
        self,
        predicted_name: Optional[str],
        similarity: float,
        matched: bool,
        threshold: float,
    ) -> bool:
        """
        Registra un evento de detección si no está dentro del gap de deduplicación.

        Args:
            predicted_name: Nombre predicho por la DB, o None si no hubo match.
            similarity:      Score de similitud coseno [0, 1].
            matched:         True si similarity >= threshold.
            threshold:       Umbral usado en esta detección.

        Returns:
            True si se escribió la fila, False si se descartó por deduplicación.
        """
        key = predicted_name or "UNKNOWN"
        now = time.monotonic()

        last = self._last_event_time.get(key)
        if last is not None and (now - last) < self.min_event_gap:
            return False  # mismo evento todavía activo

        self._last_event_time[key] = now

        row = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "event_id": str(uuid.uuid4())[:8],
            "predicted_name": key,
            "similarity": round(similarity, 4),
            "matched": int(matched),
            "threshold_used": threshold,
            "true_name": "",
            "notes": "",
        }

        self._writer.writerow(row)
        self._file.flush()  # garantiza persistencia aunque el programa se cierre inesperadamente
        return True

    def close(self) -> None:
        if self._file and not self._file.closed:
            self._file.close()
            logger.info(f"SessionLogger cerrado: {self.csv_path}")

    def __del__(self) -> None:
        self.close()
