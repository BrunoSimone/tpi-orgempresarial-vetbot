"""
VetBot - Bot de turnos de la Veterinaria "Patitas Felices".
Trabajo Practico Integrador - Organizacion Empresarial (TUPaD - UTN).

Implementa la maquina de estados con los tres puntos de decision (gateways):
  [G1] cliente registrado?   [G2] urgencia o turno comun?   [G3] hay disponibilidad?
La persistencia se realiza sobre archivos CSV (clientes, pacientes y turnos).
"""

import csv
import os
from datetime import datetime
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
    CANCELADO = auto()


ESTADOS_FINALES = {Estado.DERIVADO_URGENCIA, Estado.TURNO_CONFIRMADO, Estado.CANCELADO}

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
# VALIDACIONES (manejo del "camino infeliz")
# ===========================================================================
def dni_valido(texto):
    """El DNI debe ser numerico de 7 u 8 digitos."""
    return texto.isdigit() and 7 <= len(texto) <= 8


def parsear_fecha_hora(texto):
    """
    Interpreta la entrada 'dia/mes hora' usando el anio actual (ej. '25/06 15').
    Devuelve (fecha, hora) en formato canonico (AAAA-MM-DD, HH:MM) si es valida
    y no esta en el pasado; de lo contrario devuelve (None, mensaje_error).
    """
    partes = texto.strip().split()
    if len(partes) != 2:
        return None, "Formato: dia/mes y hora. Ejemplo: 25/06 15"

    fecha_texto, hora_texto = partes

    # Hora: un numero entero dentro del horario de atencion (de 9 a 17).
    if not hora_texto.isdigit() or not (9 <= int(hora_texto) <= 17):
        return None, "La hora debe ser un numero de 9 a 17. Ejemplo: 15"
    hora = HORARIOS_ATENCION[int(hora_texto) - 9]

    # Fecha: dia/mes. El anio siempre es el actual (no se pide al usuario).
    dia_mes = fecha_texto.split("/")
    if len(dia_mes) != 2 or not (dia_mes[0].isdigit() and dia_mes[1].isdigit()):
        return None, "La fecha debe ser dia/mes. Ejemplo: 25/06"
    dia, mes = int(dia_mes[0]), int(dia_mes[1])
    anio_actual = datetime.now().year
    try:
        momento = datetime(anio_actual, mes, dia, int(hora_texto))
    except ValueError:
        return None, "Esa fecha no existe. Proba con otra (dia/mes)."

    if momento < datetime.now():
        return None, "Esa fecha ya paso. Elegi un dia futuro."

    return (momento.strftime("%Y-%m-%d"), hora), None


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
            bot("(Escribi 'cancelar' en cualquier momento para salir.)")

        case Estado.ESPERANDO_FECHA_HORA:
            ahora = datetime.now()
            bot(f"Hoy es {ahora.strftime('%d/%m/%Y')} y son las {ahora.strftime('%H:%M')} hs.")
            bot("Para que dia y hora queres el turno? (atendemos de 9 a 17 hs)")
            bot("Ingresa dia/mes y hora. Ejemplo: 25/06 15")

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

        case Estado.CANCELADO:
            bot("Operacion cancelada. Podes volver cuando quieras. Hasta pronto!")


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
            if not dni_valido(entrada):
                bot("El DNI debe ser numerico de 7 u 8 digitos. Proba de nuevo:")
                return Estado.ESPERANDO_DNI
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
            opcion = entrada.strip()
            if opcion == "1":                          # [G2] = urgencia
                return Estado.DERIVADO_URGENCIA
            if opcion == "2":                          # [G2] = turno comun
                return Estado.ESPERANDO_FECHA_HORA
            bot("Opcion invalida. Escribi 1 (urgencia) o 2 (turno comun):")
            return Estado.ESPERANDO_TIPO_ATENCION

        case Estado.ESPERANDO_FECHA_HORA:
            resultado, error = parsear_fecha_hora(entrada)
            if error:
                bot(error)
                return Estado.ESPERANDO_FECHA_HORA
            contexto["fecha"], contexto["hora"] = resultado
            return Estado.VERIFICANDO_DISPONIBILIDAD

        case Estado.OFRECIENDO_ALTERNATIVAS:
            opcion = entrada.strip()
            alternativas = contexto["alternativas"]
            if opcion.isdigit() and 1 <= int(opcion) <= len(alternativas):
                hora_elegida = alternativas[int(opcion) - 1]
                return _registrar_turno(contexto, contexto["fecha"], hora_elegida)
            bot(f"Opcion invalida. Elegi un numero entre 1 y {len(alternativas)}:")
            return Estado.OFRECIENDO_ALTERNATIVAS

    return estado


def _procesar_alta(entrada, contexto):
    """Procesa un dato del alta segun el paso actual y avanza al siguiente."""
    paso = contexto["paso_alta"]
    texto = entrada.strip()

    if paso == "nombre":
        if not texto:
            bot("El nombre no puede estar vacio. Ingresalo de nuevo:")
            return Estado.ESPERANDO_ALTA
        contexto["nombre"] = texto
        contexto["paso_alta"] = "telefono"
        return Estado.ESPERANDO_ALTA

    if paso == "telefono":
        if not texto.isdigit():
            bot("El telefono debe ser numerico. Ingresalo de nuevo:")
            return Estado.ESPERANDO_ALTA
        contexto["telefono"] = texto
        contexto["paso_alta"] = "paciente"
        return Estado.ESPERANDO_ALTA

    if paso == "paciente":
        if not texto:
            bot("El nombre de la mascota no puede estar vacio:")
            return Estado.ESPERANDO_ALTA
        contexto["paciente"] = texto
        contexto["paso_alta"] = "especie"
        return Estado.ESPERANDO_ALTA

    # paso == "especie": ultimo dato, persistimos cliente y paciente.
    especie = texto or "Sin especificar"
    guardar_cliente(contexto["dni"], contexto["nombre"], contexto["telefono"])
    guardar_paciente(contexto["dni"], contexto["paciente"], especie)
    bot(f"Listo {contexto['nombre']}, quedaste registrado junto a {contexto['paciente']}.")
    return Estado.MENU_PRINCIPAL


def _verificar_disponibilidad(contexto):
    """[G3] Decide si confirmar el turno u ofrecer horarios alternativos."""
    fecha, hora = contexto["fecha"], contexto["hora"]
    if not franja_ocupada(fecha, hora):                # [G3] = hay disponibilidad
        return _registrar_turno(contexto, fecha, hora)

    libres = horarios_libres(fecha)                    # [G3] = sin disponibilidad
    if not libres:
        bot(f"No hay horarios libres para el {fecha}. Proba otro dia.")
        return Estado.ESPERANDO_FECHA_HORA
    bot(f"El horario {hora} del {fecha} ya esta ocupado.")
    contexto["alternativas"] = libres
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
            if entrada.strip().lower() == "cancelar":
                estado = Estado.CANCELADO
            else:
                estado = siguiente_estado(estado, entrada, contexto)
        else:
            estado = siguiente_estado(estado, None, contexto)

    mostrar_estado(estado, contexto)

    # Traza de diagnostico: evidencia que la FSM termino en un estado final.
    print(f"\n[FSM] Estado final alcanzado: {estado.name}")


main()
