import asyncio

from app.services.assistant import ChatAssistant, EntityExtractor, IntentClassifier
from app.services.metrics import (
    AGENT_EVALS,
    _hermetic_agent,
    build_engine,
    load_synthetic_samples,
    task_success_rate,
    tool_selection_accuracy,
)


def _offline_agent():
    engine = build_engine()
    samples = load_synthetic_samples()
    classifier = IntentClassifier()
    classifier.fit([s["message"] for s in samples], [s["intent"] for s in samples])
    assistant = ChatAssistant(engine, classifier, EntityExtractor(engine.docs))
    agent = _hermetic_agent(engine, assistant)
    return agent


def test_agent_returns_agent_trace_with_thought_and_tool() -> None:
    agent = _offline_agent()

    result = asyncio.run(agent.run("busca paquetes de playa en Cancún por 1500 euros"))
    trace = result["agent_trace"]
    assert trace["mode"] == "planner"
    assert isinstance(trace["steps"], list) and trace["steps"]
    first = trace["steps"][0]
    assert first["thought"]
    assert first["tool"] == "search_local_packages"
    assert "Cancún" in first["tool_params"].get("destination", "")
    assert result["suggestions"]
    assert isinstance(result["message"], str)


def test_agent_triggers_scraper_when_user_asks_for_internet() -> None:
    agent = _offline_agent()

    result = asyncio.run(agent.run("busca en internet ofertas de última hora en el Caribe"))
    tools = [step["tool"] for step in result["agent_trace"]["steps"] if step["tool"]]
    assert tools[0] == "trigger_async_scraper"
    assert tools[1] == "search_local_packages"
    first_step = result["agent_trace"]["steps"][0]
    assert first_step["tool_output"].get("extraidos", 0) > 0


def test_agent_reserve_flow_prepares_sync() -> None:
    agent = _offline_agent()

    result = asyncio.run(agent.run("quiero reservar el paquete a Santorini"))
    trace = result["agent_trace"]
    sync = next(
        (step for step in trace["steps"] if step.get("tool") == "prepare_package_sync"),
        None,
    )
    assert sync is not None
    assert sync["tool_output"]["sincronizado"] is True
    assert "reserva" in result["message"]


def test_agent_saludo_uses_no_tools() -> None:
    agent = _offline_agent()

    result = asyncio.run(agent.run("hola buenos días"))
    assert result["agent_trace"]["steps"] == []
    assert result["agent_trace"]["tool_used"] is None


def test_tool_selection_accuracy_and_task_success_in_range() -> None:
    agent = _offline_agent()
    selection = tool_selection_accuracy(agent)
    success = task_success_rate(agent)
    assert 0.0 <= selection <= 1.0
    assert 0.0 <= success <= 1.0
    assert selection >= 0.8
    assert success >= 0.8


def test_agent_evals_fixtures_are_consistent() -> None:
    for case in AGENT_EVALS:
        assert case["message"]
        assert case["expected_tool"] in {
            "search_local_packages",
            "trigger_async_scraper",
            "prepare_package_sync",
        }