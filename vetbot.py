"""
VetBot - Bot de turnos de la Veterinaria "Patitas Felices".
Trabajo Practico Integrador - Organizacion Empresarial (TUPaD - UTN).

Implementa la maquina de estados con los tres puntos de decision (gateways):
  [G1] cliente registrado?   [G2] urgencia o turno comun?   [G3] hay disponibilidad?
La persistencia se realiza sobre archivos CSV (clientes, pacientes y turnos).
"""

import csv
import os
from enum import Enum, auto

CARPETA_DATOS = os.path.join(os.path.dirname(__file__), "datos")
ARCHIVO_CLIENTES = os.path.join(CARPETA_DATOS, "clientes.csv")
ARCHIVO_PACIENTES = os.path.join(CARPETA_DATOS, "pacientes.csv")
ARCHIVO_TURNOS = os.path.join(CARPETA_DATOS, "turnos.csv")

# Horarios de atencion de la veterinaria (turnos en hora en punto, de 09 a 17 hs)
HORARIOS_ATENCION = [
    "09:00", "10:00", "11:00", "12:00", "13:00",
    "14:00", "15:00", "16:00", "17:00",
]


# ---------------------------------------------------------------------------
# Estados de la maquina de estados
# ---------------------------------------------------------------------------
class Estado(Enum):
    INICIO = auto()
    ESPERANDO_DNI = auto()
    ESPERANDO_ALTA = auto()
    MENU_PRINCIPAL = auto()
    ESPERANDO_TIPO_ATENCION = auto()
    DERIVADO_URGENCIA = auto()
    ESPERANDO_FECHA_HORA = auto()
    VERIFICANDO_DISPONIBILIDAD = auto()
    OFRECIENDO_ALTERNATIVAS = auto()
    TURNO_CONFIRMADO = auto()


ESTADOS_FINALES = {Estado.DERIVADO_URGENCIA, Estado.TURNO_CONFIRMADO}

ESTADOS_INTERACTIVOS = {
    Estado.ESPERANDO_DNI,
    Estado.ESPERANDO_ALTA,
    Estado.ESPERANDO_TIPO_ATENCION,
    Estado.ESPERANDO_FECHA_HORA,
    Estado.OFRECIENDO_ALTERNATIVAS,
}


# ===========================================================================
# CAPA DE PERSISTENCIA
# ===========================================================================
def leer_csv(ruta):
    """Devuelve la lista de filas (como diccionarios) de un archivo CSV."""
    with open(ruta, newline="", encoding="utf-8") as archivo:
        return list(csv.DictReader(archivo))


def buscar_cliente(dni):
    """[G1] Busca un cliente por DNI. Devuelve la fila o None si no existe."""
    for cliente in leer_csv(ARCHIVO_CLIENTES):
        if cliente["dni"] == dni:
            return cliente
    return None


def pacientes_de(dni):
    """Devuelve la lista de pacientes (mascotas) de un cliente."""
    return [paciente for paciente in leer_csv(ARCHIVO_PACIENTES)
            if paciente["dni_cliente"] == dni]


def guardar_cliente(dni, nombre, telefono):
    """Agrega un cliente nuevo al CSV."""
    with open(ARCHIVO_CLIENTES, "a", newline="", encoding="utf-8") as archivo:
        csv.writer(archivo).writerow([dni, nombre, telefono])


def guardar_paciente(dni, nombre_paciente, especie):
    """Agrega un paciente nuevo al CSV, calculando el proximo id."""
    pacientes = leer_csv(ARCHIVO_PACIENTES)
    nuevo_id = max((int(paciente["id_paciente"]) for paciente in pacientes), default=0) + 1
    with open(ARCHIVO_PACIENTES, "a", newline="", encoding="utf-8") as archivo:
        csv.writer(archivo).writerow([nuevo_id, dni, nombre_paciente, especie])


def franja_ocupada(fecha, hora):
    """[G3] True si ya existe un turno confirmado en esa fecha y hora."""
    for turno in leer_csv(ARCHIVO_TURNOS):
        if (turno["fecha"] == fecha and turno["hora"] == hora
                and turno["estado"] == "confirmado"):
            return True
    return False


def horarios_libres(fecha):
    """Devuelve los horarios de atencion que siguen libres en una fecha."""
    return [hora for hora in HORARIOS_ATENCION if not franja_ocupada(fecha, hora)]


def guardar_turno(dni, nombre_paciente, fecha, hora, tipo):
    """Registra un turno confirmado y devuelve su id."""
    turnos = leer_csv(ARCHIVO_TURNOS)
    nuevo_id = max((int(turno["id_turno"]) for turno in turnos), default=0) + 1
    with open(ARCHIVO_TURNOS, "a", newline="", encoding="utf-8") as archivo:
        csv.writer(archivo).writerow(
            [nuevo_id, dni, nombre_paciente, fecha, hora, tipo, "confirmado"]
        )
    return nuevo_id


# ===========================================================================
# PRESENTACION: lo que el bot dice en cada estado
# ===========================================================================
def bot(mensaje):
    """Imprime un mensaje del bot con prefijo."""
    print(f"VetBot> {mensaje}")


def mostrar_estado(estado, contexto):
    match estado:
        case Estado.INICIO:
            bot("Hola! Soy VetBot, de la Veterinaria Patitas Felices.")

        case Estado.ESPERANDO_DNI:
            bot("Para empezar, ingresa tu DNI (sin puntos):")

        case Estado.ESPERANDO_ALTA:
            preguntas = {
                "nombre": "Como es tu nombre y apellido?",
                "telefono": "Cual es tu telefono de contacto?",
                "paciente": "Como se llama tu mascota?",
                "especie": "Que especie es? (ej. Perro, Gato)",
            }
            bot(preguntas[contexto["paso_alta"]])

        case Estado.MENU_PRINCIPAL:
            bot("Que tipo de atencion necesitas?")
            bot("  1) Urgencia (atencion inmediata)")
            bot("  2) Turno comun (elegis dia y horario)")

        case Estado.ESPERANDO_FECHA_HORA:
            bot("Para que dia y hora queres el turno? (AAAA-MM-DD HH:MM)")

        case Estado.OFRECIENDO_ALTERNATIVAS:
            bot("Horarios disponibles ese dia:")
            for numero, hora in enumerate(contexto["alternativas"], start=1):
                print(f"        {numero}) {hora}")
            bot("Elegi el numero del horario que prefieras:")

        case Estado.DERIVADO_URGENCIA:
            bot("Entendido, es una URGENCIA.")
            bot("Te derivo de inmediato con el veterinario de guardia.")

        case Estado.TURNO_CONFIRMADO:
            bot(f"Turno confirmado! #{contexto['id_turno']}")
            bot(f"   Paciente: {contexto['paciente']} | "
                f"Fecha: {contexto['fecha']} | Hora: {contexto['hora']}")
            bot("Te esperamos en Patitas Felices. Gracias!")


# ===========================================================================
# LOGICA DE TRANSICION: segun la entrada, decide el estado siguiente
# ===========================================================================
def siguiente_estado(estado, entrada, contexto):
    match estado:

        case Estado.INICIO:
            return Estado.ESPERANDO_DNI

        case Estado.MENU_PRINCIPAL:
            return Estado.ESPERANDO_TIPO_ATENCION

        case Estado.VERIFICANDO_DISPONIBILIDAD:
            return _verificar_disponibilidad(contexto)

        case Estado.ESPERANDO_DNI:
            contexto["dni"] = entrada
            cliente = buscar_cliente(entrada)          # [G1] consulta al CSV
            if cliente:                                # [G1] = SI -> registrado
                contexto["nombre"] = cliente["nombre"]
                bot(f"Hola de nuevo, {cliente['nombre']}!")
                return Estado.MENU_PRINCIPAL
            bot("No te encontre en el sistema. Vamos a registrarte.")  # [G1] = NO
            contexto["paso_alta"] = "nombre"
            return Estado.ESPERANDO_ALTA

        case Estado.ESPERANDO_ALTA:
            return _procesar_alta(entrada, contexto)

        case Estado.ESPERANDO_TIPO_ATENCION:
            if entrada.strip() == "1":                 # [G2] = urgencia
                return Estado.DERIVADO_URGENCIA
            return Estado.ESPERANDO_FECHA_HORA         # [G2] = turno comun

        case Estado.ESPERANDO_FECHA_HORA:
            fecha, hora = entrada.split()
            contexto["fecha"], contexto["hora"] = fecha, hora
            return Estado.VERIFICANDO_DISPONIBILIDAD

        case Estado.OFRECIENDO_ALTERNATIVAS:
            hora_elegida = contexto["alternativas"][int(entrada.strip()) - 1]
            return _registrar_turno(contexto, contexto["fecha"], hora_elegida)

    return estado


def _procesar_alta(entrada, contexto):
    """Procesa un dato del alta segun el paso actual y avanza al siguiente."""
    paso = contexto["paso_alta"]
    texto = entrada.strip()

    if paso == "nombre":
        contexto["nombre"] = texto
        contexto["paso_alta"] = "telefono"
        return Estado.ESPERANDO_ALTA

    if paso == "telefono":
        contexto["telefono"] = texto
        contexto["paso_alta"] = "paciente"
        return Estado.ESPERANDO_ALTA

    if paso == "paciente":
        contexto["paciente"] = texto
        contexto["paso_alta"] = "especie"
        return Estado.ESPERANDO_ALTA

    # paso == "especie": ultimo dato, persistimos cliente y paciente.
    guardar_cliente(contexto["dni"], contexto["nombre"], contexto["telefono"])
    guardar_paciente(contexto["dni"], contexto["paciente"], texto)
    bot(f"Listo {contexto['nombre']}, quedaste registrado junto a {contexto['paciente']}.")
    return Estado.MENU_PRINCIPAL


def _verificar_disponibilidad(contexto):
    """[G3] Decide si confirmar el turno u ofrecer horarios alternativos."""
    fecha, hora = contexto["fecha"], contexto["hora"]
    if not franja_ocupada(fecha, hora):                # [G3] = hay disponibilidad
        return _registrar_turno(contexto, fecha, hora)
    bot(f"El horario {hora} del {fecha} ya esta ocupado.")  # [G3] = sin disponibilidad
    contexto["alternativas"] = horarios_libres(fecha)
    return Estado.OFRECIENDO_ALTERNATIVAS


def _registrar_turno(contexto, fecha, hora):
    """Persiste el turno y deja los datos en el contexto para mostrarlos."""
    paciente = contexto.get("paciente")
    if not paciente:
        # Si el cliente ya existia, tomamos su primer paciente registrado.
        pacientes = pacientes_de(contexto["dni"])
        paciente = pacientes[0]["nombre_paciente"] if pacientes else "Sin especificar"
    contexto["id_turno"] = guardar_turno(contexto["dni"], paciente, fecha, hora, "comun")
    contexto["paciente"] = paciente
    contexto["fecha"], contexto["hora"] = fecha, hora
    return Estado.TURNO_CONFIRMADO


# ===========================================================================
# BUCLE PRINCIPAL
# ===========================================================================
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
