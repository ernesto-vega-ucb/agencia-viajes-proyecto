import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { useLocation } from "react-router-dom";
import { SearchSessionContext } from "./searchSessionContext";
import type { AgentTrace, NlpDebug, TourPackage } from "../types/domain";

export function SearchSessionProvider({ children }: { children: ReactNode }) {
  const { pathname } = useLocation();

  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [results, setResults] = useState<TourPackage[]>([]);
  const [searched, setSearched] = useState(false);
  const [nlpDebug, setNlpDebug] = useState<NlpDebug | null>(null);
  const [nlpReply, setNlpReply] = useState<string | null>(null);
  const [analyzedQuery, setAnalyzedQuery] = useState("");
  const [agentTrace, setAgentTrace] = useState<AgentTrace | null>(null);
  const [agentReply, setAgentReply] = useState<string | null>(null);

  const clear = useCallback(() => {
    setQuery("");
    setSuggestions([]);
    setResults([]);
    setSearched(false);
    setNlpDebug(null);
    setNlpReply(null);
    setAnalyzedQuery("");
    setAgentTrace(null);
    setAgentReply(null);
  }, []);

  const isSearchFlow = pathname === "/buscar" || pathname.startsWith("/paquetes/");
  const prevFlow = useRef(isSearchFlow);
  useEffect(() => {
    if (prevFlow.current && !isSearchFlow) {
      clear();
    }
    prevFlow.current = isSearchFlow;
  }, [isSearchFlow, clear]);

  const value = useMemo(
    () => ({
      query,
      suggestions,
      results,
      searched,
      nlpDebug,
      nlpReply,
      analyzedQuery,
      agentTrace,
      agentReply,
      setQuery,
      setSuggestions,
      setResults,
      setSearched,
      setNlpDebug,
      setNlpReply,
      setAnalyzedQuery,
      setAgentTrace,
      setAgentReply,
      clear,
    }),
    [
      query,
      suggestions,
      results,
      searched,
      nlpDebug,
      nlpReply,
      analyzedQuery,
      agentTrace,
      agentReply,
      clear,
    ],
  );

  return <SearchSessionContext.Provider value={value}>{children}</SearchSessionContext.Provider>;
}