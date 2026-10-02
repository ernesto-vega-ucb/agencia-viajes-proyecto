import json
from pathlib import Path

OUT_PATH = Path(__file__).resolve().parents[1] / "app" / "data" / "synthetic_interactions.json"

SAMPLES = [
    {
        "id": "int-01",
        "message": "¡Hola! estoy buscando unas vacaciones.",
        "intent": "saludo",
        "entities": {},
    },
    {
        "id": "int-02",
        "message": "Buenas tardes, espero que me puedas ayudar.",
        "intent": "saludo",
        "entities": {},
    },
    {
        "id": "int-03",
        "message": "Muchas gracias, hasta luego.",
        "intent": "despedida",
        "entities": {},
    },
    {
        "id": "int-04",
        "message": "¿Cuánto cuesta un viaje a Lisboa por 3 días?",
        "intent": "presupuesto",
        "entities": {"destination": ["Lisboa"], "category": ["ciudad"], "duration": [3]},
    },
    {
        "id": "int-05",
        "message": "Tengo un presupuesto de 800 euros para la playa.",
        "intent": "presupuesto",
        "entities": {"category": ["playa"], "budget": [800.0]},
    },
    {
        "id": "int-06",
        "message": "¿Qué me recomiendas para una escapada cultural en Praga?",
        "intent": "recomendar",
        "entities": {"destination": ["Praga"], "category": ["ciudad"]},
    },
    {
        "id": "int-07",
        "message": "Ayúdame a decidir, me interesa la aventura en Perú.",
        "intent": "recomendar",
        "entities": {"destination": ["Cusco"], "category": ["aventura"]},
    },
    {
        "id": "int-08",
        "message": "Dame ideas para un viaje familiar en julio.",
        "intent": "recomendar",
        "entities": {"category": ["familiar"], "start_date": ["2026-07"]},
    },
    {
        "id": "int-09",
        "message": "Quiero un paquete a Cancún para dos personas en octubre.",
        "intent": "buscar_paquetes",
        "entities": {"destination": ["Cancún"], "travelers": [2], "start_date": ["2026-10"]},
        "expected_code": "PVP-CUN-001",
    },
    {
        "id": "int-10",
        "message": "Busco una semana de playa en el Caribe con presupuesto de 1500 euros.",
        "intent": "buscar_paquetes",
        "entities": {
            "destination": ["Cancún"],
            "category": ["playa"],
            "budget": [1500.0],
            "duration": [7],
        },
        "expected_code": "PVP-CUN-001",
    },
    {
        "id": "int-11",
        "message": "Necesito opciones de fin de semana en Lisboa.",
        "intent": "buscar_paquetes",
        "entities": {"destination": ["Lisboa"], "category": ["ciudad"], "duration": [2]},
        "expected_code": "PVP-LIS-001",
    },
    {
        "id": "int-12",
        "message": "Ofertas de trekking a Machu Picchu para 4 personas.",
        "intent": "buscar_paquetes",
        "entities": {"destination": ["Cusco"], "category": ["aventura"], "travelers": [4]},
        "expected_code": "PVP-AND-001",
    },
    {
        "id": "int-13",
        "message": "Vacaciones familiares en la Costa Brava con los niños.",
        "intent": "buscar_paquetes",
        "entities": {"destination": ["Costa Brava"], "category": ["familiar"]},
        "expected_code": "PVP-BCN-001",
    },
    {
        "id": "int-14",
        "message": "Escapada urbana a Barcelona en junio, presupuesto 600.",
        "intent": "buscar_paquetes",
        "entities": {
            "destination": ["Barcelona"],
            "category": ["ciudad"],
            "start_date": ["2026-06"],
            "budget": [600.0],
        },
    },
    {
        "id": "int-15",
        "message": "Quiero reservar el paquete a Cancún para mis vacaciones de julio.",
        "intent": "reservar_paquete",
        "entities": {"destination": ["Cancún"], "start_date": ["2026-07"]},
        "expected_code": "PVP-CUN-001",
    },
    {
        "id": "int-16",
        "message": "Reserva el trekking de Cusco para 6 personas.",
        "intent": "reservar_paquete",
        "entities": {"destination": ["Cusco"], "travelers": [6]},
        "expected_code": "PVP-AND-001",
    },
    {
        "id": "int-17",
        "message": "Por favor contrata la escapada a Lisboa para el fin de semana.",
        "intent": "reservar_paquete",
        "entities": {"destination": ["Lisboa"], "duration": [2]},
        "expected_code": "PVP-LIS-001",
    },
    {
        "id": "int-18",
        "message": "Necesito reservar un viaje familiar a la Costa Brava para octubre.",
        "intent": "reservar_paquete",
        "entities": {
            "destination": ["Costa Brava"],
            "category": ["familiar"],
            "start_date": ["2026-10"],
        },
        "expected_code": "PVP-BCN-001",
    },
    {
        "id": "int-19",
        "message": "Quiero ver paquetes de último momento a Roma.",
        "intent": "buscar_paquetes",
        "entities": {"destination": ["Roma"], "category": ["ciudad"]},
    },
    {
        "id": "int-20",
        "message": "Sugerencias para viajar a Tokio en octubre.",
        "intent": "recomendar",
        "entities": {"destination": ["Tokio"], "category": ["ciudad"], "start_date": ["2026-10"]},
    },
]


def main() -> None:
    if len(SAMPLES) > 20:
        raise SystemExit("El conjunto sintético debe tener como máximo 20 registros")
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(
        json.dumps(SAMPLES, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"{len(SAMPLES)} muestras escritas en {OUT_PATH}")


if __name__ == "__main__":
    main()
