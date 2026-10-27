# Orquestador concurrente de modelos

Ejercicio del Módulo 1 (AI Engineering): simula un backend que consulta varias fuentes de IA de forma eficiente con `asyncio`. Solo usa la librería estándar.

## Qué demuestra

| Requisito | Cómo se resuelve |
|---|---|
| Tres llamadas simuladas | `gpt_4_call`, `claude_3_call`, `local_llama_call` con `await asyncio.sleep()` de distinta duración |
| Orquestación | `asyncio.gather` dispara las tres a la vez |
| Resiliencia | `asyncio.timeout(2)` sobre la ejecución total; `TimeoutError` capturado, el programa sigue |
| Control de flujo | `asyncio.Semaphore(2)`: de 10 llamadas, solo 2 corren simultáneamente |
| Sin bloqueo | No se usa `time.sleep` |

## Escenarios que ejecuta

1. Tres modelos en paralelo: caben en el timeout.
2. Un modelo lento (3 s): se dispara el `TimeoutError`.
3. 10 llamadas con `Semaphore(2)`: caben en el timeout y el máximo simultáneo observado es 2.
4. 10 llamadas con `Semaphore(2)` más lentas: superan el timeout y se captura el error.

En los logs, las tres llamadas del escenario 1 inician en el mismo milisegundo.

## Cómo ejecutarlo

Requiere Python 3.12+ (usa `asyncio.timeout`).

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
python orquestador.py
```
