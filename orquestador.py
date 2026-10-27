"""Orquestador concurrente de modelos (simulado).

Simula un backend que consulta varias fuentes de IA a la vez usando asyncio:
gather para la concurrencia, timeout para la resiliencia y Semaphore para
limitar cuantas llamadas corren simultaneamente.
"""

import asyncio
import logging
import sys

TIMEOUT_TOTAL = 2.0  # segundos para la ejecucion total
MAX_CONCURRENTES = 2  # llamadas simultaneas permitidas por el Semaphore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d | %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
log = logging.getLogger("orquestador")


async def gpt_4_call(prompt: str, latencia: float = 1.2) -> str:
    log.info("INICIO  gpt_4_call")
    await asyncio.sleep(latencia)
    log.info("FIN     gpt_4_call (%.1fs)", latencia)
    return f"[gpt-4] respuesta a '{prompt}'"


async def claude_3_call(prompt: str, latencia: float = 0.8) -> str:
    log.info("INICIO  claude_3_call")
    await asyncio.sleep(latencia)
    log.info("FIN     claude_3_call (%.1fs)", latencia)
    return f"[claude-3] respuesta a '{prompt}'"


async def local_llama_call(prompt: str, latencia: float = 0.4) -> str:
    log.info("INICIO  local_llama_call")
    await asyncio.sleep(latencia)
    log.info("FIN     local_llama_call (%.1fs)", latencia)
    return f"[llama-local] respuesta a '{prompt}'"


async def escenario_gather(titulo: str, **latencias: float) -> None:
    """Dispara los tres modelos a la vez bajo un timeout total."""
    log.info("=== %s ===", titulo)
    try:
        async with asyncio.timeout(TIMEOUT_TOTAL):
            resultados = await asyncio.gather(
                gpt_4_call("hola", latencias.get("gpt", 1.2)),
                claude_3_call("hola", latencias.get("claude", 0.8)),
                local_llama_call("hola", latencias.get("llama", 0.4)),
            )
        for r in resultados:
            log.info("RESULTADO %s", r)
    except TimeoutError:
        log.error(
            "TimeoutError: la ejecucion supero %.1fs; se cancelan las llamadas "
            "pendientes y el programa continua.",
            TIMEOUT_TOTAL,
        )


class Medidor:
    """Cuenta cuantas llamadas estan activas y guarda el maximo observado."""

    def __init__(self) -> None:
        self.activas = 0
        self.maximo = 0


async def llamada_simulada(
    i: int, semaforo: asyncio.Semaphore, medidor: Medidor, latencia: float
) -> str:
    async with semaforo:
        medidor.activas += 1
        medidor.maximo = max(medidor.maximo, medidor.activas)
        log.info("INICIO  llamada #%02d (activas=%d)", i, medidor.activas)
        try:
            await asyncio.sleep(latencia)
        finally:
            medidor.activas -= 1
        log.info("FIN     llamada #%02d", i)
        return f"resultado #{i}"


async def escenario_semaforo(titulo: str, latencia: float) -> None:
    """Lanza 10 llamadas pero el Semaphore deja correr solo 2 a la vez."""
    log.info("=== %s ===", titulo)
    semaforo = asyncio.Semaphore(MAX_CONCURRENTES)
    medidor = Medidor()
    try:
        async with asyncio.timeout(TIMEOUT_TOTAL):
            resultados = await asyncio.gather(
                *(llamada_simulada(i, semaforo, medidor, latencia) for i in range(1, 11))
            )
        log.info(
            "OK: %d llamadas completadas, maximo simultaneo = %d",
            len(resultados),
            medidor.maximo,
        )
    except TimeoutError:
        log.error(
            "TimeoutError: la ejecucion supero %.1fs (maximo simultaneo = %d); "
            "el programa continua.",
            TIMEOUT_TOTAL,
            medidor.maximo,
        )


async def main() -> None:
    await escenario_gather("1. Tres modelos en paralelo (cabe en el timeout)")
    await escenario_gather(
        "2. Un modelo lento fuerza el timeout", gpt=3.0
    )
    await escenario_semaforo("3. 10 llamadas, Semaphore(2), cabe en el timeout", 0.3)
    await escenario_semaforo("4. 10 llamadas, Semaphore(2), supera el timeout", 0.5)
    log.info("Programa terminado sin interrupciones.")


if __name__ == "__main__":
    asyncio.run(main())
