import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import eval_metrics as evaluate  # noqa: E402
from app.services.assistant import ChatAssistant, EntityExtractor, IntentClassifier  # noqa: E402
from app.services.metrics import (  # noqa: E402
    _hermetic_agent,
    task_success_rate,
    tool_selection_accuracy,
)
from app.services.scraper import PackageScraper  # noqa: E402
from app.services.synthetic import load_synthetic_packages  # noqa: E402


def test_scraped_fixture_has_at_least_fifteen() -> None:
    packages = PackageScraper().scrape_all()
    assert 15 <= len(packages) <= 20
    normalized = packages[0]
    for key in ("category", "country", "durationDays", "rating", "source"):
        assert key in normalized


def test_synthetic_dataset_bounded_at_twenty() -> None:
    samples = evaluate.load_synthetic_samples()
    assert len(samples) <= 20
    assert len(samples) >= 10


def test_synthetic_packages_dataset_bounded_and_unified() -> None:
    packages = load_synthetic_packages()
    assert 15 <= len(packages) <= 20
    for package in packages:
        for key in (
            "title",
            "destination",
            "basePrice",
            "durationDays",
            "startDates",
            "description",
        ):
            assert key in package
            assert package[key]
    assert len({package["code"] for package in packages}) == len(packages)


def test_engine_fuses_three_sources() -> None:
    engine = evaluate.build_engine()
    sources = {doc.source for doc in engine.docs}
    assert {"catalogo", "sintetico", "external"}.issubset(sources)
    assert sum(1 for doc in engine.docs if doc.source == "sintetico") >= 15
    assert sum(1 for doc in engine.docs if doc.source == "external") >= 15


def test_assistant_handle_exposes_nlp_debug() -> None:
    engine = evaluate.build_engine()
    samples = evaluate.load_synthetic_samples()
    extractor = EntityExtractor(engine.docs)
    classifier = IntentClassifier()
    classifier.fit([s["message"] for s in samples], [s["intent"] for s in samples])
    assistant = ChatAssistant(engine, classifier, extractor)

    result = assistant.handle("quiero reservar un paquete a Cancún en julio")
    debug = result["nlp_debug"]
    assert debug["intent"] == "reservar_paquete"
    assert 0.0 <= debug["confidence"] <= 1.0
    assert debug["model"]
    assert "destination" in debug["entities"]
    assert set(debug["scores"].keys()) >= {"reservar_paquete", "buscar_paquetes"}


def test_metrics_summary_shape() -> None:
    report = evaluate.get_metrics_summary()
    assert {"datos", "asistente", "buscador", "entidades", "agente"}.issubset(report)
    assert report["datos"]["ml_enabled"] is False
    assert 0.0 <= report["asistente"]["macro_f1_intenciones"] <= 1.0
    assert 0.0 <= report["buscador"]["ndcg_at_5"] <= 1.0
    for key in evaluate.ENTITY_KEYS:
        assert 0.0 <= report["entidades"].get(key, 0.0) <= 1.0
    assert 0.0 <= report["agente"]["tool_selection_accuracy"] <= 1.0
    assert 0.0 <= report["agente"]["task_success_rate"] <= 1.0
    assert report["agente"]["mode"] in {"planner", "llm"}


def test_assistant_metrics_in_unit_range() -> None:
    engine = evaluate.build_engine()
    samples = evaluate.load_synthetic_samples()
    extractor = EntityExtractor(engine.docs)
    classifier = IntentClassifier()
    classifier.fit([s["message"] for s in samples], [s["intent"] for s in samples])
    assistant = ChatAssistant(engine, classifier, extractor)

    assert 0.0 <= evaluate.macro_f1_intents(samples) <= 1.0
    assert 0.0 <= evaluate.booking_success_rate(assistant, samples) <= 1.0
    for key in evaluate.ENTITY_KEYS:
        assert 0.0 <= evaluate.entity_exact_f1(extractor, samples, key) <= 1.0
    assert 0.0 <= evaluate.search_ndcg(engine) <= 1.0


def test_intent_classifier_uses_rules_and_logreg() -> None:
    classifier = IntentClassifier()
    intent, confidence, _ = classifier.predict("quiero reservar el paquete a Cancún")
    assert intent == "reservar_paquete"
    assert 0.0 <= confidence <= 1.0


def test_entity_extractor_detects_structured_fields() -> None:
    engine = evaluate.build_engine()
    extractor = EntityExtractor(engine.docs)
    entities = extractor.extract(
        "Busco una playa en Cancún por 1300 euros para 3 personas en julio"
    )
    assert entities["destination"] == ["Cancún"]
    assert entities["category"] == ["playa"]
    assert entities["budget"] == [1300.0]
    assert entities["travelers"] == [3]
    assert entities["start_date"] == ["2026-07"]


def test_search_engine_semantic_ranking_with_filters() -> None:
    engine = evaluate.build_engine()
    docs = engine.search(
        "vacaciones familiares costa brava",
        destination="Costa Brava",
        limit=5,
    )
    assert docs
    assert docs[0].destination == "Costa Brava"

    cheap = engine.search("playa", max_budget=900.0, limit=5)
    assert all(doc.basePrice <= 900.0 for doc in cheap)


def test_print_evaluation_report() -> None:
    """Genera un reporte legible en consola con las métricas del sistema NLP y Buscador."""
    engine = evaluate.build_engine()
    samples = evaluate.load_synthetic_samples()
    extractor = EntityExtractor(engine.docs)
    classifier = IntentClassifier()
    classifier.fit([s["message"] for s in samples], [s["intent"] for s in samples])
    assistant = ChatAssistant(engine, classifier, extractor)

    # Cálculo de métricas reales
    macro_f1 = evaluate.macro_f1_intents(samples)
    success_rate = evaluate.booking_success_rate(assistant, samples)
    ndcg_5 = evaluate.search_ndcg(engine)
    
    entity_f1_scores = {key: evaluate.entity_exact_f1(extractor, samples, key) for key in evaluate.ENTITY_KEYS}

    # Impresión del reporte formateado
    print("\n" + "=" * 65)
    print("       REPORTE DE EVALUACIÓN DE DESEMPEÑO: NLP & BUSCADOR")
    print("=" * 65)
    
    print("\n [1] MÓDULO ASISTENTE DE RESERVAS (NLP)")
    print(f" • Macro-F1 de Intenciones        : {macro_f1:.4f}")
    print("   -> (Mide la precisión y exhaustividad balanceada en la clasificación de intenciones)")
    
    print("\n • F1 Exacto por Entidad:")
    for entity, score in entity_f1_scores.items():
        print(f"    - {entity.ljust(15)} : {score:.4f}")
    print("   -> (Mide la exactitud en la extracción de parámetros clave del usuario)")

    print(f"\n • Tasa de Éxito de Reserva      : {success_rate:.4f}")
    print("   -> (Porcentaje de interacciones guiadas exitosamente hacia la reserva)")

    print("\n [2] MÓDULO BUSCADOR DE PAQUETES (Recomendación)")
    print(f" • nDCG@5 (Ranking de Relevancia) : {ndcg_5:.4f}")
    print("   -> (Evalúa la calidad del top 5 de resultados frente a las expectativas)")

    print("\n [3] MÓDULO AGENTE DE IA (ReAct + Tool Calling)")
    agent = _hermetic_agent(engine, assistant)
    selection = tool_selection_accuracy(agent)
    success = task_success_rate(agent)
    print(f" • Tool Selection Accuracy        : {selection:.4f}")
    print("   -> (Capacidad de elegir la herramienta adecuada según la intención)")
    print(f" • Task Success Rate              : {success:.4f}")
    print("   -> (Tareas de búsqueda/scráping/reserva completadas correctamente)")
    print("=" * 65 + "\n")

    # Aseguramos que sigan cumpliendo el rango válido
    assert 0.0 <= macro_f1 <= 1.0
    assert 0.0 <= ndcg_5 <= 1.0
    assert 0.0 <= selection <= 1.0
    assert 0.0 <= success <= 1.0