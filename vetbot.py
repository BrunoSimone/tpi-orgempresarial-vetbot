"""
VetBot - Esqueleto de navegacion del bot de turnos (Veterinaria "Patitas Felices").
Trabajo Practico Integrador - Organizacion Empresarial (TUPaD - UTN).

Implementa la estructura base de la MAQUINA DE ESTADOS: saluda, pide el DNI,
busca al cliente y ofrece el menu de atencion.
"""

import csv
import os
from enum import Enum, auto

CARPETA_DATOS = os.path.join(os.path.dirname(__file__), "datos")
ARCHIVO_CLIENTES = os.path.join(CARPETA_DATOS, "clientes.csv")


# ---------------------------------------------------------------------------
# Estados de la maquina de estados
# ---------------------------------------------------------------------------
class Estado(Enum):
    INICIO = auto()
    ESPERANDO_DNI = auto()
    MENU_PRINCIPAL = auto()
    ESPERANDO_TIPO_ATENCION = auto()
    DERIVADO_URGENCIA = auto()         
    ESPERANDO_FECHA_HORA = auto()
    TURNO_CONFIRMADO = auto()           


ESTADOS_FINALES = {Estado.DERIVADO_URGENCIA, Estado.TURNO_CONFIRMADO}

ESTADOS_INTERACTIVOS = {
    Estado.ESPERANDO_DNI,
    Estado.ESPERANDO_TIPO_ATENCION,
    Estado.ESPERANDO_FECHA_HORA,
}


# ---------------------------------------------------------------------------
# Acceso a datos
# ---------------------------------------------------------------------------
def leer_csv(ruta):
    """Devuelve la lista de filas (como diccionarios) de un archivo CSV."""
    with open(ruta, newline="", encoding="utf-8") as archivo:
        return list(csv.DictReader(archivo))


def buscar_cliente(dni):
    """Busca un cliente por DNI. Devuelve la fila o None si no existe."""
    for cliente in leer_csv(ARCHIVO_CLIENTES):
        if cliente["dni"] == dni:
            return cliente
    return None


# ---------------------------------------------------------------------------
# Presentacion: lo que el bot dice en cada estado
# ---------------------------------------------------------------------------
def bot(mensaje):
    """Imprime un mensaje del bot con prefijo."""
    print(f"VetBot> {mensaje}")


def mostrar_estado(estado, contexto):
    match estado:
        case Estado.INICIO:
            bot("Hola! Soy VetBot, de la Veterinaria Patitas Felices.")
        case Estado.ESPERANDO_DNI:
            bot("Para empezar, ingresa tu DNI (sin puntos):")
        case Estado.MENU_PRINCIPAL:
            bot("Que tipo de atencion necesitas?")
            bot("  1) Urgencia (atencion inmediata)")
            bot("  2) Turno comun (elegis dia y horario)")
        case Estado.ESPERANDO_FECHA_HORA:
            bot("Para que dia y hora queres el turno? (AAAA-MM-DD HH:MM)")
        case Estado.DERIVADO_URGENCIA:
            bot("Es una urgencia. Te derivo con el veterinario de guardia.")
        case Estado.TURNO_CONFIRMADO:
            bot(f"Turno confirmado para {contexto['fecha']} {contexto['hora']}. Gracias!")


# ---------------------------------------------------------------------------
# Logica de transicion: segun la entrada, decide el estado siguiente
# ---------------------------------------------------------------------------
def siguiente_estado(estado, entrada, contexto):
    match estado:
        case Estado.INICIO:
            return Estado.ESPERANDO_DNI

        case Estado.ESPERANDO_DNI:
            contexto["dni"] = entrada
            cliente = buscar_cliente(entrada)
            if cliente:
                bot(f"Hola de nuevo, {cliente['nombre']}!")
            return Estado.MENU_PRINCIPAL

        case Estado.MENU_PRINCIPAL:
            return Estado.ESPERANDO_TIPO_ATENCION

        case Estado.ESPERANDO_TIPO_ATENCION:
            if entrada.strip() == "1":
                return Estado.DERIVADO_URGENCIA
            return Estado.ESPERANDO_FECHA_HORA

        case Estado.ESPERANDO_FECHA_HORA:
            fecha, hora = entrada.split()
            contexto["fecha"], contexto["hora"] = fecha, hora
            return Estado.TURNO_CONFIRMADO

    return estado


# ---------------------------------------------------------------------------
# Bucle principal
# ---------------------------------------------------------------------------
def main():
    estado = Estado.INICIO
    contexto = {}

    while estado not in ESTADOS_FINALES:
        mostrar_estado(estado, contexto)
        if estado in ESTADOS_INTERACTIVOS:
            entrada = input("Tu> ")
            estado = siguiente_estado(estado, entrada, contexto)
        else:
            estado = siguiente_estado(estado, None, contexto)

    mostrar_estado(estado, contexto)


    main()
