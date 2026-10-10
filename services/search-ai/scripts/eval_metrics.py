import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.metrics import (  # noqa: E402
    AGENT_EVALS,
    ENTITY_KEYS,
    EVAL_QUERIES,
    StaticCatalog,
    booking_success_rate,
    build_engine,
    entity_exact_f1,
    evaluate_all,
    get_metrics_summary,
    load_synthetic_samples,
    macro_f1_intents,
    ndcg_at_k,
    search_ndcg,
    task_success_rate,
    tool_selection_accuracy,
)

__all__ = [
    "AGENT_EVALS",
    "ENTITY_KEYS",
    "EVAL_QUERIES",
    "StaticCatalog",
    "booking_success_rate",
    "build_engine",
    "entity_exact_f1",
    "evaluate_all",
    "get_metrics_summary",
    "load_synthetic_samples",
    "macro_f1_intents",
    "ndcg_at_k",
    "search_ndcg",
    "task_success_rate",
    "tool_selection_accuracy",
]


def main() -> None:
    report = get_metrics_summary()
    dataset = report["datos"]
    agente = report["agente"]
    print("========== MActricas formales del asistente y buscador ==========")
    print(
        f"Dataset fusionado: {dataset['total_fusion']} paquetes indexados "
        f"({dataset['paquetes_sinteticos']} sintActicos, "
        f"{dataset['scrapeados']} externos scrapeados; "
        f"{dataset['interacciones_sinteticas']} interacciones). "
        f"Embeddings: {dataset['embeddings']}"
    )
    print(
        "Asistente  -> Macro-F1 intenciones (CV 5): "
        f"{report['asistente']['macro_f1_intenciones']}"
    )
    print(
        "             Booking success rate (top-1): "
        f"{report['asistente']['booking_success_rate']}"
    )
    print(
        "             F1 exacto por entidad: "
        + ", ".join(f"{key}={value}" for key, value in report["entidades"].items())
    )
    print(f"Buscador   -> nDCG@5: {report['buscador']['ndcg_at_5']}")
    print(
        "Agente     -> Tool Selection Accuracy: "
        f"{agente['tool_selection_accuracy']} · Task Success Rate: "
        f"{agente['task_success_rate']} (modo {agente['mode']})"
    )
    print("=================================================================")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()