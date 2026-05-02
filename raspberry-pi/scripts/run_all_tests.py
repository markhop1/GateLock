#!/usr/bin/env python3
"""
Script maestro para ejecutar todos los tests.

Ejecuta tests en orden lógico y muestra resumen de resultados.
"""
import argparse
import os
import sys
import subprocess
import time
from pathlib import Path
from typing import List, Tuple
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def find_face_image_for_test(base_dir: Path) -> Path | None:
    """Find first face image in fixtures or known_faces for Recognition test."""
    for search_dir in [
        base_dir / "tests" / "fixtures" / "test_images",
        base_dir / "known_faces",
    ]:
        if not search_dir.exists():
            continue
        for person_dir in search_dir.iterdir():
            if person_dir.is_dir():
                for ext in ("*.jpg", "*.jpeg", "*.png"):
                    for img in person_dir.glob(ext):
                        return img
    return None


# Lista de tests a ejecutar
TESTS = [
    {
        'name': 'Config',
        'script': 'tests/unit/test_config.py',
        'requires': [],
        'category': 'unit'
    },
    {
        'name': 'Face Database Logic',
        'script': 'tests/unit/test_face_db_logic.py',
        'requires': [],
        'category': 'unit'
    },
    {
        'name': 'Utils',
        'script': 'tests/unit/test_utils.py',
        'requires': [],
        'category': 'unit'
    },
    {
        'name': 'Database',
        'script': 'tests/test_database.py',
        'requires': [],
        'category': 'integration'
    },
    {
        'name': 'Build Database',
        'script': 'tests/test_build_database.py',
        'requires': ['insightface'],
        'category': 'integration'
    },
    {
        'name': 'API Auth',
        'script': 'tests/test_api_auth.py',
        'requires': [],
        'category': 'integration',
        'skip_if': '--skip-api'
    },
    {
        'name': 'API Client',
        'script': 'tests/test_api_client.py',
        'requires': [],
        'category': 'integration',
        'skip_if': '--skip-api',
        'args': ['--mock']  # Usar mock por defecto
    },
    {
        'name': 'Video Recorder',
        'script': 'tests/test_video_recorder.py',
        'requires': [],
        'category': 'integration',
        'skip_if': '--skip-camera'
    },
    {
        'name': 'Detection',
        'script': 'tests/test_detection.py',
        'requires': ['insightface'],
        'category': 'hardware',
        'skip_if': '--skip-camera'
    },
    {
        'name': 'Recognition',
        'script': 'tests/test_recognition.py',
        'requires': ['tensorflow'],
        'category': 'hardware',
        'skip_if': '--skip-camera',
        'needs_image': True,
        'note': 'Requiere imágenes en tests/fixtures/test_images o known_faces'
    },
]


def run_test(test_info: dict, base_dir: Path, skip_flags: set) -> Tuple[bool, float]:
    """
    Ejecuta un test individual.
    
    Returns:
        (success, elapsed_time) o (None, 0.0) si se saltó
    """
    script_path = base_dir / test_info['script']
    
    if not script_path.exists():
        logger.warning(f"⚠ Script no encontrado: {script_path}")
        return False, 0.0
    
    # Verificar si debe saltarse
    if test_info.get('skip_if') and test_info['skip_if'] in skip_flags:
        logger.info(f"⊘ Saltando {test_info['name']} ({test_info['skip_if']})")
        return None, 0.0
    
    # Verificar dependencias
    requires = test_info.get('requires', [])
    for req in requires:
        try:
            __import__(req)
        except ImportError:
            logger.warning(f"⚠ Saltando {test_info['name']}: {req} no disponible")
            return None, 0.0
    
    # Para Recognition: buscar imagen si no hay args
    if test_info.get('needs_image') and 'args' not in test_info:
        img_path = find_face_image_for_test(base_dir)
        if img_path is None:
            logger.warning(
                f"⚠ Saltando {test_info['name']}: no hay imágenes en "
                "tests/fixtures/test_images o known_faces"
            )
            return None, 0.0
        test_info = dict(test_info)
        test_info['args'] = ['--image', str(img_path)]
    
    logger.info(f"▶ Ejecutando {test_info['name']}...")
    
    # Para tests unitarios, usar pytest
    if test_info.get('category') == 'unit':
        cmd = [sys.executable, '-m', 'pytest', str(script_path), '-v', '--tb=short']
    else:
        # Para scripts de prueba, ejecutar directamente
        cmd = [sys.executable, str(script_path)]
        # Añadir argumentos adicionales si existen
        if 'args' in test_info:
            cmd.extend(test_info['args'])
    
    # Ejecutar con PYTHONPATH para que los imports (database, api, video, etc.) funcionen
    env = os.environ.copy()
    existing = env.get('PYTHONPATH', '')
    env['PYTHONPATH'] = str(base_dir) + (os.pathsep + existing if existing else '')
    
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            cwd=str(base_dir),
            env=env,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutos máximo por test
        )
        elapsed = time.time() - start_time
        
        # Mostrar salida
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        if result.returncode == 0:
            logger.info(f"✓ {test_info['name']} pasó ({elapsed:.1f}s)")
            return True, elapsed
        else:
            logger.error(f"✗ {test_info['name']} falló ({elapsed:.1f}s)")
            return False, elapsed
            
    except subprocess.TimeoutExpired:
        logger.error(f"✗ {test_info['name']} excedió el tiempo límite")
        return False, time.time() - start_time
    except Exception as e:
        logger.error(f"✗ Error ejecutando {test_info['name']}: {e}")
        return False, time.time() - start_time


def main():
    parser = argparse.ArgumentParser(
        description="Ejecuta todos los tests del sistema",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python scripts/run_all_tests.py                    # Ejecutar todos los tests
  python scripts/run_all_tests.py --skip-camera     # Saltar tests que requieren cámara
  python scripts/run_all_tests.py --skip-api        # Saltar tests de API
  python scripts/run_all_tests.py --unit-only       # Solo tests unitarios
        """
    )
    parser.add_argument(
        '--skip-camera',
        action='store_true',
        help='Saltar tests que requieren cámara'
    )
    parser.add_argument(
        '--skip-api',
        action='store_true',
        help='Saltar tests que requieren API backend'
    )
    parser.add_argument(
        '--unit-only',
        action='store_true',
        help='Ejecutar solo tests unitarios'
    )
    parser.add_argument(
        '--category',
        choices=['unit', 'integration', 'hardware'],
        help='Ejecutar solo tests de una categoría'
    )
    
    args = parser.parse_args()
    
    base_dir = Path(__file__).resolve().parent.parent
    
    logger.info("=" * 70)
    logger.info("Ejecutando Todos los Tests")
    logger.info("=" * 70)
    logger.info(f"Directorio base: {base_dir}")
    
    skip_flags = set()
    if args.skip_camera:
        skip_flags.add('--skip-camera')
    if args.skip_api:
        skip_flags.add('--skip-api')
    
    # Filtrar tests según opciones
    tests_to_run = TESTS.copy()
    
    if args.unit_only:
        tests_to_run = [t for t in tests_to_run if t['category'] == 'unit']
    
    if args.category:
        tests_to_run = [t for t in tests_to_run if t['category'] == args.category]
    
    # Ejecutar tests
    results = []
    total_time = 0.0
    
    for test_info in tests_to_run:
        success, elapsed = run_test(test_info, base_dir, skip_flags)
        
        if success is not None:  # None significa que se saltó
            results.append({
                'name': test_info['name'],
                'success': success,
                'elapsed': elapsed,
                'category': test_info['category']
            })
            total_time += elapsed
    
    # Resumen
    logger.info("=" * 70)
    logger.info("Resumen de Resultados")
    logger.info("=" * 70)
    
    passed = sum(1 for r in results if r['success'])
    failed = sum(1 for r in results if not r['success'])
    skipped = len(tests_to_run) - len(results)
    
    logger.info(f"Total tests: {len(tests_to_run)}")
    logger.info(f"  ✓ Pasaron: {passed}")
    logger.info(f"  ✗ Fallaron: {failed}")
    logger.info(f"  ⊘ Saltados: {skipped}")
    logger.info(f"Tiempo total: {total_time:.1f}s")
    
    # Detalles por categoría
    categories = {}
    for r in results:
        cat = r['category']
        if cat not in categories:
            categories[cat] = {'passed': 0, 'failed': 0}
        if r['success']:
            categories[cat]['passed'] += 1
        else:
            categories[cat]['failed'] += 1
    
    if categories:
        logger.info("\nPor categoría:")
        for cat, counts in categories.items():
            logger.info(f"  {cat}: {counts['passed']} pasaron, {counts['failed']} fallaron")
    
    # Tests que fallaron
    failed_tests = [r for r in results if not r['success']]
    if failed_tests:
        logger.info("\nTests que fallaron:")
        for r in failed_tests:
            logger.info(f"  ✗ {r['name']} ({r['elapsed']:.1f}s)")
    
    logger.info("=" * 70)
    
    # Exit code
    if failed > 0:
        logger.error(f"Algunos tests fallaron ({failed})")
        sys.exit(1)
    else:
        logger.info("✓ Todos los tests pasaron")
        sys.exit(0)


if __name__ == "__main__":
    main()
