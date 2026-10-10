import { createContext, useContext } from "react";
import type { AgentTrace, NlpDebug, TourPackage } from "../types/domain";

export interface SearchSessionValue {
  query: string;
  suggestions: string[];
  results: TourPackage[];
  searched: boolean;
  nlpDebug: NlpDebug | null;
  nlpReply: string | null;
  analyzedQuery: string;
  agentTrace: AgentTrace | null;
  agentReply: string | null;
  setQuery: (value: string) => void;
  setSuggestions: (value: string[]) => void;
  setResults: (value: TourPackage[]) => void;
  setSearched: (value: boolean) => void;
  setNlpDebug: (value: NlpDebug | null) => void;
  setNlpReply: (value: string | null) => void;
  setAnalyzedQuery: (value: string) => void;
  setAgentTrace: (value: AgentTrace | null) => void;
  setAgentReply: (value: string | null) => void;
  clear: () => void;
}

export const SearchSessionContext = createContext<SearchSessionValue | null>(null);

export function useSearchSession(): SearchSessionValue {
  const context = useContext(SearchSessionContext);
  if (!context) {
    throw new Error("useSearchSession debe usarse dentro de SearchSessionProvider");
  }
  return context;
}