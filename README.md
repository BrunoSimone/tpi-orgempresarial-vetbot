# VetBot 🐾 — Bot de turnos para Veterinaria "Patitas Felices"

Bot conversacional **simulado por consola** que automatiza la toma de turnos de una
veterinaria. Desarrollado como Trabajo Práctico Integrador de la materia
**Organización Empresarial** (Tecnicatura Universitaria en Programación a Distancia — UTN).

La lógica del bot está implementada como una **Máquina de Estados Finita (FSM)** y
responde fielmente al modelo **BPMN 2.0** diseñado para el proceso.

## 👥 Integrantes

- Bruno Simone
- Shaiel Peters

## 📋 Descripción del proceso

El bot automatiza el proceso administrativo de **gestión de turnos**, que hoy la
veterinaria realiza de forma manual (teléfono / WhatsApp). Guía al usuario por tres
puntos de decisión (gateways):

1. **¿El cliente está registrado?** → si no, lo da de alta junto a su mascota.
2. **¿Es urgencia o turno común?** → la urgencia se deriva a atención inmediata.
3. **¿Hay disponibilidad en el horario pedido?** → si no, ofrece horarios alternativos.

## 📁 Estructura del repositorio

```
.
├── vetbot.py            # Programa principal: FSM + lógica de los gateways
├── datos/               # Base de datos simulada (archivos CSV)
│   ├── clientes.csv     # Clientes registrados (dni, nombre, telefono)
│   ├── pacientes.csv    # Pacientes/mascotas (id_paciente, dni_cliente, nombre_paciente, especie)
│   └── turnos.csv       # Turnos reservados (id_turno, dni, nombre_paciente, fecha, hora, tipo, estado)
├── .gitignore
└── README.md
```

## ⚙️ Requisitos

- **Python 3.10 o superior** (se usa la sentencia `match`, disponible desde 3.10).
- No requiere librerías externas: solo usa la biblioteca estándar (`csv`, `datetime`, `enum`, `os`).

## ▶️ Cómo ejecutarlo

1. Cloná el repositorio:
   ```bash
   git clone https://github.com/BrunoSimone/tpi-orgempresarial-vetbot.git
   cd tpi-orgempresarial-vetbot
   ```
2. Ejecutá el bot:
   ```bash
   python vetbot.py
   ```
3. Seguí las indicaciones por consola. Para probar con datos de ejemplo:
   - Cliente registrado: `30111222` (María González) o `28999888` (Juan Pérez).
   - Cliente no registrado: cualquier otro número de 7-8 dígitos → inicia el alta.
   - Para pedir un turno común, ingresá día/mes y hora (ej. `25/06 15`).
   - Para ver el camino "sin disponibilidad": pedí un turno el `20/06` a las `10` (esa franja ya está ocupada).
   - Escribí `cancelar` en cualquier momento para abortar la operación.

> ℹ️ Los archivos CSV se **modifican** al registrar clientes, pacientes o turnos
> (el bot tiene persistencia real). Si querés volver al estado inicial, restaurá
> los CSV desde el control de versiones (`git checkout datos/`).

## 🧠 Arquitectura: Máquina de Estados

El bot mantiene un único **estado actual** a la vez y transiciona según la entrada del
usuario. Las responsabilidades están separadas en dos funciones:

- `mostrar_estado()` → lo que el bot **dice** en cada estado (presentación).
- `siguiente_estado()` → la **lógica** que decide el estado siguiente según la entrada.

La matriz de transiciones está documentada al inicio de `vetbot.py`.
Estados finales: `TURNO_CONFIRMADO`, `DERIVADO_URGENCIA`, `CANCELADO`.

## 🛡️ Robustez (camino infeliz)

El bot valida las entradas y maneja los errores sin cortarse:

- DNI no numérico o con cantidad incorrecta de dígitos.
- Teléfono no numérico durante el alta.
- Opción de menú inexistente.
- Fecha en el pasado, fecha inexistente o fuera del horario de atención.
- Horario ya ocupado (deriva a la oferta de alternativas).
