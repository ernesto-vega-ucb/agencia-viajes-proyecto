from dataclasses import dataclass, field

from sklearn.feature_extraction.text import TfidfVectorizer

from app.services.catalog import CatalogClient
from app.services.text_prep import CATEGORY_SYNONYMS, TOKEN_RE, normalize_es


@dataclass
class Analysis:
    query: str
    tokens: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    destinations: list[str] = field(default_factory=list)


class NlpService:
    def __init__(self, catalog: CatalogClient) -> None:
        self.catalog = catalog
        self._vectorizer: TfidfVectorizer | None = None
        self._corpus: list[str] = []

    def analyze(self, query: str) -> Analysis:
        normalized = self._normalize(query)
        tokens = normalized.split()

        analysis = Analysis(query=query, tokens=tokens)
        for token in tokens:
            for category, synonyms in CATEGORY_SYNONYMS.items():
                if token in synonyms and category not in analysis.categories:
                    analysis.categories.append(category)

        for package in self.catalog.packages():
            destination = package.get("destination", "").lower()
            country = package.get("country", "").lower()
            if any(word in destination or word in country for word in tokens):
                analysis.destinations.append(package["destination"])
        return analysis

    def rank(self, query: str, limit: int = 20) -> list[dict]:
        analysis = self.analyze(query)
        packages = self.catalog.packages()

        if not analysis.tokens and not analysis.categories:
            return sorted(packages, key=lambda p: p.get("rating", 0), reverse=True)[:limit]

        corpus = [self._package_document(package).lower() for package in packages]
        vectorizer = TfidfVectorizer(
            token_pattern=TOKEN_RE,
            ngram_range=(1, 2),
        )
        try:
            matrix = vectorizer.fit_transform(corpus)
            query_vec = vectorizer.transform([query.lower()])
            scores = (matrix @ query_vec.T).toarray().flatten()
        except ValueError:
            scores = [0.0] * len(packages)

        ranked = sorted(
            zip(packages, scores, strict=True),
            key=lambda pair: (pair[1], pair[0].get("rating", 0)),
            reverse=True,
        )
        return [package for package, _ in ranked[:limit]]

    def suggestions_for(self, query: str, limit: int = 4) -> list[str]:
        analysis = self.analyze(query)
        suggestions: list[str] = []
        for category in analysis.categories:
            suggestions.append(f"mejor categoría {category}")
        if analysis.destinations:
            suggestions.append(f"destinos: {', '.join(analysis.destinations)}")
        suggestions.extend(self._popular_hints(limit - len(suggestions)))
        return suggestions[:limit]

    def _popular_hints(self, limit: int) -> list[str]:
        popular = sorted(self.catalog.packages(), key=lambda p: p.get("rating", 0), reverse=True)[
            :limit
        ]
        return [f"{p['title']} ({p['destination']})" for p in popular]

    def _package_document(self, package: dict) -> str:
        parts = [
            package.get("title", ""),
            package.get("destination", ""),
            package.get("country", ""),
            package.get("category", ""),
            package.get("description", ""),
        ]
        return " ".join(parts).lower()

    def _normalize(self, text: str) -> str:
        return normalize_es(text)
