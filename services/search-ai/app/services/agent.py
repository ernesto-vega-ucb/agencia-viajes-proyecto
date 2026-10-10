"""Agente de IA autónomo para el asistente de reservas (ReAct + Tool Calling).

Tres herramientas:
- search_local_packages: consulta el índice unificado (catálogo + sintéticos + scrapeados).
- trigger_async_scraper: lanza el scraping asíncrono de opciones externas.
- prepare_package_sync: prepara/registra un paquete en el backend central (lazy upsert).

El agente razona con un LLM configurable (Ollama/OpenAI/DeepSeek) cuando está
disponible; en modo offline usa un planificador determinista basado en el NLP
existente (intención + entidades) para que la demo y las métricas sean estables.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from app.config import get_settings
from app.services.assistant import ChatAssistant, build_assistant
from app.services.fusion import refresh_scraped_packages
from app.services.llm import LLMBackend, get_llm_backend
from app.services.package_sync import sync_package
from app.services.search_engine import PackageDoc, get_search_engine
from app.services.text_prep import normalize_es

ToolExecutor = Callable[[dict], Awaitable[dict]]

WEB_TRIGGERS = (
    "internet",
    "web",
    "extern",
    "online",
    "nuevas opciones",
    "actualizado",
    "actualizados",
    "ultima hora",
    "última hora",
    "ultimo momento",
    "último momento",
    "tiempo real",
    "via web",
)

SYSTEM_PROMPT = (
    "Eres el Agente de IA de una agencia de viajes. Hablas en español y ayudas a "
    "buscar y reservar paquetes turísticos.\n"
    "Para resolver la petición puedes llamar a estas herramientas:\n"
    "- search_local_packages: consulta el índice unificado de paquetes (catálogo "
    "interno, sintéticos y scrapeados). Úsala para buscar, recomendar o filtrar por "
    "presupuesto, e incluye todos los filtros que deduzcas del mensaje.\n"
    "- trigger_async_scraper: actualiza opciones externas por scraping asíncrono. "
    "Úsala SOLO cuando el usuario pida explícitamente datos externos, de internet, "
    "actualizados, de última hora o 'nuevas opciones' que no estén en el catálogo.\n"
    "- prepare_package_sync: prepara y registra un paquete para reserva en el backend "
    "central. Úsala cuando el usuario quiera reservar/contratar/añadir a reserva un paquete.\n"
    "Reglas:\n"
    "1. Razona en tu mensaje y luego llama a la herramienta adecuada (o a varias si el "
    "flujo lo requiere: p. ej. buscar y después preparar la reserva).\n"
    "2. Cuando recibas el resultado de la herramienta, responde al usuario en español "
    "de forma clara y breve, citando títulos, destino y precio cuando haga falta.\n"
    "3. Si no puedes resolverlo, pide los datos que falten (destino, fechas, presupuesto)."
)


_TOOL_METHODS: dict[str, str] = {
    "search_local_packages": "_run_search",
    "trigger_async_scraper": "_run_scraper",
    "prepare_package_sync": "_run_sync",
}


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict

    @property
    def schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


@dataclass
class AgentStep:
    thought: str
    tool: str | None = None
    tool_params: dict = field(default_factory=dict)
    tool_output: dict = field(default_factory=dict)


class AIAgent:
    def __init__(
        self,
        assistant: ChatAssistant | None = None,
        *,
        tool_overrides: dict[str, ToolExecutor] | None = None,
    ) -> None:
        self._assistant = assistant or build_assistant()
        self._overrides = tool_overrides or {}
        self._tools = {tool.name: tool for tool in self._build_tools()}

    # ---------- herramientas ----------

    @staticmethod
    def _build_tools() -> list[Tool]:
        return [
            Tool(
                name="search_local_packages",
                description=(
                    "Busca paquetes turísticos en el índice unificado del servicio "
                    "(catálogo interno, sintéticos y externos scrapeados)."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Consulta o tema del viaje"},
                        "destination": {"type": "string", "description": "Destino deseado"},
                        "category": {"type": "string", "description": "Categoría (playa, urbano, cultura…)"},
                        "max_budget": {"type": "number", "description": "Presupuesto máximo en euros"},
"limit": {"type": "integer", "description": "Nº máximo de resultados", "default": 5},
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="trigger_async_scraper",
                description=(
                    "Lanza el scraping asíncrono para incorporar opciones externas "
                    "actualizadas (fuentes configuradas) y reconstruir el índice."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Contexto de lo que busca el usuario"}
                    },
                    "required": [],
                },
            ),
            Tool(
                name="prepare_package_sync",
                description=(
                    "Prepara un paquete para reserva registrándolo en el backend central "
                    "(lazy upsert). Indica package_id o code del paquete elegido."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "package_id": {"type": "integer", "description": "Id del paquete en el índice"},
                        "code": {"type": "string", "description": "Código del paquete (p. ej. SYN-001)"},
                    },
                    "required": [],
                },
            ),
        ]

    async def _run_search(self, params: dict) -> dict:
        engine = get_search_engine()
        query = str(params.get("query") or "")
        if not query:
            return {"total": 0, "resumen": [], "paquetes": [], "detalle": "consulta vacía"}
        limit = max(1, min(int(params.get("limit") or 5), 20))
        docs = await asyncio.to_thread(
            engine.search,
            query,
            category=params.get("category"),
            destination=params.get("destination"),
            max_budget=params.get("max_budget"),
            limit=limit,
        )
        packages = [doc.to_dict() for doc in docs]
        summary = [
            {
                "id": doc.id,
                "code": doc.code,
                "title": doc.title,
                "destination": doc.destination,
                "basePrice": doc.basePrice,
                "source": doc.source,
            }
            for doc in docs
        ]
        return {"total": len(packages), "resumen": summary, "paquetes": packages}

    async def _run_scraper(self, params: dict) -> dict:
        summary = await refresh_scraped_packages()
        summary["detalle"] = "opciones externas actualizadas y el índice se reconstruyó"
        return summary

    async def _run_sync(self, params: dict) -> dict:
        engine = get_search_engine()
        doc: PackageDoc | None = None
        package_id = params.get("package_id")
        if package_id is not None:
            doc = await asyncio.to_thread(engine.doc, int(package_id))
        if doc is None and params.get("code"):
            doc = next(
                (candidate for candidate in engine.docs if candidate.code == params["code"]),
                None,
            )
        if doc is None:
            return {
                "sincronizado": False,
                "detalle": "no se pudo identificar el paquete: falta package_id o code",
            }
        base = {"id": doc.id, "code": doc.code, "title": doc.title, "destination": doc.destination}
        if doc.source == "catalogo":
            return {"sincronizado": True, "ya_existia": True, "paquete": base}
        payload = await asyncio.to_thread(sync_package, doc)
        return {
            "sincronizado": True,
            "ya_existia": False,
            "booking_id": payload.get("id"),
            "paquete": base,
        }

    # ---------- planificación determinista (offline) ----------

    def plan(self, message: str, nlp: dict) -> dict:
        """Devuelve la secuencia de acciones offline y la herramienta principal."""
        intent = nlp["intent"]
        context = nlp["context"]
        query = " ".join(chunk for chunk in [message, context["destination"] or ""] if chunk)
        search_params = {
            "query": query,
            "destination": context["destination"],
            "category": context["category"],
            "max_budget": context["max_budget"],
            "limit": 5,
        }
        if intent in {"saludo", "despedida"}:
            return {"sequence": [], "primary": None}
        raw = normalize_es(message, keep_stopwords=True)
        wants_web = any(trigger in raw for trigger in WEB_TRIGGERS)
        if wants_web:
            return {
                "sequence": [
                    {"tool": "trigger_async_scraper", "params": {"query": message}},
                    {"tool": "search_local_packages", "params": search_params},
                ],
                "primary": "trigger_async_scraper",
            }
        if intent == "reservar_paquete":
            suggestions = nlp["suggestions"]
            sync_params: dict[str, Any] = {}
            if suggestions:
                sync_params["package_id"] = suggestions[0]["id"]
            sequence = [{"tool": "search_local_packages", "params": search_params}]
            if suggestions:
                sequence.append({"tool": "prepare_package_sync", "params": sync_params})
            return {"sequence": sequence, "primary": "prepare_package_sync"}
        return {
            "sequence": [{"tool": "search_local_packages", "params": search_params}],
            "primary": "search_local_packages",
        }

    def _thought_for(self, message: str, tool: str, params: dict) -> str:
        if tool == "trigger_async_scraper":
            return (
                "El usuario pide opciones externas/actualizadas; el catálogo local "
                "podría estar desfasado. Lanzo el scraping asíncrono y reconstruyo el índice."
            )
        if tool == "prepare_package_sync":
            return (
                "La intención es reservar un paquete: localizo el paquete elegido y lo "
                "preparo en el backend central con lazy upsert."
            )
        filters = ", ".join(
            f"{key}={value}"
            for key, value in params.items()
            if value not in (None, "") and key in ("destination", "category", "max_budget")
        )
        detail = f" (filtros aplicados: {filters})" if filters else ""
        return f"Interpreto la petición como una búsqueda de paquetes en el índice unificado{detail}."

    async def _execute(self, name: str, params: dict) -> dict:
        if name in self._overrides:
            return await self._overrides[name](params)
        method_name = _TOOL_METHODS.get(name)
        if method_name is None:
            return {"ok": False, "error": f"herramienta desconocida: {name}"}
        try:
            return await getattr(self, method_name)(params)
        except Exception as exc:  # noqa: BLE001 (respuesta estable ante fallos)
            return {"ok": False, "error": str(exc), "tool": name}

    @staticmethod
    def _compact_output(output: dict) -> dict:
        if "paquetes" in output:
            return {key: value for key, value in output.items() if key != "paquetes"}
        return output

    # ---------- bucle ReAct ----------

    async def run(self, message: str, *, tool_overrides: dict[str, ToolExecutor] | None = None) -> dict:
        nlp = self._assistant.handle(message)
        if tool_overrides:
            self._overrides = dict(self._overrides, **tool_overrides)
        backend = get_llm_backend()
        if backend is None:
            return await self._run_deterministic(message, nlp)
        return await self._run_llm(message, nlp, backend)

    async def _run_deterministic(self, message: str, nlp: dict) -> dict:
        plan = self.plan(message, nlp)
        steps: list[AgentStep] = []
        search_cache: list[dict] = []
        for action in plan["sequence"]:
            tool = action["tool"]
            params = dict(action.get("params") or {})
            if tool == "prepare_package_sync" and "package_id" not in params and "code" not in params:
                if search_cache:
                    params["package_id"] = search_cache[0]["id"]
                else:
                    continue
            thought = self._thought_for(message, tool, params)
            output = await self._execute(tool, params)
            if tool == "search_local_packages":
                search_cache = output.get("paquetes", [])
            steps.append(AgentStep(thought=thought, tool=tool, tool_params=params, tool_output=self._compact_output(output)))
        suggestions = search_cache or nlp["suggestions"]
        reply = self._reply_from_steps(steps, nlp)
        trace = self._build_trace(steps, mode="planner", model="TF-IDF + Regresión Logística")
        return self._compose(nlp, suggestions, reply, trace)

    async def _run_llm(self, message: str, nlp: dict, backend: LLMBackend) -> dict:
        settings = get_settings()
        messages: list[dict] = [{"role": "user", "content": message}]
        steps: list[AgentStep] = []
        search_cache: list[dict] = []
        schemas = [tool.schema for tool in self._tools.values()]
        final_text = ""
        max_steps = max(1, settings.agent_max_steps)
        for _ in range(max_steps):
            outcome = await asyncio.to_thread(
                backend.chat_with_tools, SYSTEM_PROMPT, messages, schemas
            )
            text = (outcome.get("content") or "").strip()
            calls = outcome.get("tool_calls") or []
            if not calls:
                final_text = text or self._reply_from_steps(steps, nlp)
                break
            assistant_message: dict[str, Any] = {"role": "assistant", "content": text}
            messages.append(assistant_message)
            for index, call in enumerate(calls, start=1):
                tool = call.get("name") or ""
                params = call.get("arguments") or {}
                thought = text or f"El modelo decidió invocar la herramienta {tool}."
                output = await self._execute(tool, params)
                if tool == "search_local_packages":
                    search_cache = output.get("paquetes", [])
                compact = self._compact_output(output)
                steps.append(AgentStep(thought=thought, tool=tool, tool_params=params, tool_output=compact))
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.get("id") or f"call_{index}_{len(steps)}",
                        "content": json.dumps(compact, ensure_ascii=False, default=str),
                    }
                )
        else:
            final_text = "He completado el ciclo de razonamiento sin agotar la tarea: " + self._reply_from_steps(steps, nlp)
        suggestions = search_cache or nlp["suggestions"]
        trace = self._build_trace(steps, mode="llm", model=backend.model_label)
        return self._compose(nlp, suggestions, final_text, trace)

    def _compose(self, nlp: dict, suggestions: list[dict], reply: str, trace: dict) -> dict:
        return {
            "intent": nlp["intent"],
            "confidence": nlp["confidence"],
            "scores": nlp["scores"],
            "entities": nlp["entities"],
            "context": nlp["context"],
            "suggestions": suggestions,
            "message": reply,
            "nlp_debug": nlp["nlp_debug"],
            "agent_trace": trace,
        }

    def _reply_from_steps(self, steps: list[AgentStep], nlp: dict) -> str:
        if not steps:
            return nlp["message"]
        parts: list[str] = []
        last_search: AgentStep | None = None
        last_sync: AgentStep | None = None
        last_scrape: AgentStep | None = None
        for step in steps:
            if step.tool == "search_local_packages":
                last_search = step
            elif step.tool == "prepare_package_sync":
                last_sync = step
            elif step.tool == "trigger_async_scraper":
                last_scrape = step
        if last_scrape is not None:
            output = last_scrape.tool_output
            parts.append(f"Actualicé las opciones externas: {output.get('extraidos', 0)} paquetes")
            if output.get("nuevos_guardados"):
                parts.append(f"y {output['nuevos_guardados']} nuevos")
            parts.append("incorporados al índice.")
        if last_search is not None:
            output = last_search.tool_output
            total = output.get("total", 0)
            if total:
                noun = "opción" if total == 1 else "opciones"
                listing = " | ".join(
                    f"{item['title']} ({item['destination']}, desde {item['basePrice']:.0f} €)"
                    for item in output.get("resumen", [])[:3]
                )
                parts.append(
                    f"Encontré {total} {noun} en el índice unificado. Destacan: {listing}."
                )
            else:
                parts.append("No encontré opciones que encajen; refina destino, fechas o presupuesto.")
        if last_sync is not None:
            output = last_sync.tool_output
            if output.get("sincronizado"):
                package = output.get("paquete", {})
                title = package.get("title", "")
                if output.get("ya_existia"):
                    parts.append(f"El paquete \"{title}\" ya está en el catálogo; puedes reservarlo desde la tarjeta.")
                else:
                    booking = output.get("booking_id")
                    suffix = f" (id de reserva {booking})" if booking is not None else ""
                    parts.append(f"Preparé la reserva de \"{title}\" en el backend central{suffix}.")
            else:
                parts.append("No pude preparar la reserva: identifica el paquete (id o código).")
        if not parts:
            parts.append(nlp["message"])
        return " ".join(parts)

    @staticmethod
    def _build_trace(steps: list[AgentStep], *, mode: str, model: str) -> dict:
        serialized = [
            {
                "step": index,
                "thought": step.thought,
                "tool": step.tool,
                "tool_params": step.tool_params,
                "tool_output": step.tool_output,
            }
            for index, step in enumerate(steps, start=1)
        ]
        return {
            "model": model,
            "mode": mode,
            "steps": serialized,
            "thought": steps[0].thought if steps else None,
            "tool_used": steps[-1].tool if steps else None,
            "tool_output": steps[-1].tool_output if steps else None,
        }


def build_agent() -> AIAgent:
    return AIAgent()