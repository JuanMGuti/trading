# Expert Advisor Trading Bot — MetaTrader 5

Bot de trading automatizado para MetaTrader 5, escrito en Python.
Esta versión incorpora correcciones de bugs, logging estructurado y buenas prácticas.

## Archivos

| Archivo | Descripción |
|---|---|
| `mt5-init.py` | Inicialización de MT5 con detección automática de rutas |
| `config_manager.py` | Carga, validación y persistencia de configuración JSON |
| `account-info.py` | Consulta y verificación del estado de la cuenta |
| `test-function.py` | Órdenes de prueba con cálculo correcto de lot size |
| `config.json` | Configuración del bot (símbols, riesgo, análisis, MT5) |

## Instalación

```bash
pip install -r requirements.txt
```

## Mejoras aplicadas

### `mt5-init.py`
- Corregido: uso de `glob.glob()` para resolver rutas con wildcards (`*`)
- Añadido: `mt5.shutdown()` al detectar fallo post-inicialización
- Añadido: logging estructurado con `logging.getLogger`
- Añadido: validación de tipo y valor no-vacío en `terminal_path`

### `config_manager.py`
- Añadido: validación de tipos y rangos para todos los campos de `trading`
- Añadido: backup automático (`.bak`) antes de sobrescribir el archivo
- Mejorado: `load_config()` detecta archivos vacíos
- Reemplazado: `print()` por `logging` en toda la clase
- Mejorado: `set()` usa `dict.setdefault` para crear claves intermedias

### `account-info.py`
- Corregido: evita inicializar MT5 si ya está conectado (`_ensure_initialized`)
- Añadido: logging estructurado en todas las funciones
- Mejorado: formato de salida más limpio y consistente

### `test-function.py`
- **Bug crítico corregido**: el cálculo de SL/TP para pares JPY estaba duplicado
  y usaba un multiplicador incorrecto. Ahora se calcula `pip_size` una sola vez.
- Corregido: `MAGIC_NUMBER` unificado con `config.json` (234567)
- Corregido: `min_lot` ya no puede quedar fuera de scope en el bloque `except`
- Añadido: validación de `order_type` antes de ejecutar cualquier operación
- Añadido: guarda contra `result is None` en `order_send`

### General
- Añadido: `requirements.txt` con dependencia `MetaTrader5`
- Añadido: `.gitignore` para Python (cachés, venvs, logs, secretos)

## Uso rápido

```bash
# 1. Verificar conexión
python mt5-init.py

# 2. Ver información de cuenta
python account-info.py

# 3. Ejecutar orden de prueba
python test-function.py
```

## Licencia

MIT