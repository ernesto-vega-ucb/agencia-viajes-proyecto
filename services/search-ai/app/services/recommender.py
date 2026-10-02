from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import UserHistory
from app.services.search_engine import PackageDoc, SearchEngine


class Recommender:
    def __init__(self, engine: SearchEngine) -> None:
        self.engine = engine

    def recommend(self, db: Session, user_id: str, limit: int = 5) -> list[dict]:
        history = db.scalars(
            select(UserHistory)
            .where(UserHistory.user_id == user_id)
            .order_by(UserHistory.created_at.desc())
            .limit(5)
        ).all()

        queries = [entry.query or "" for entry in history if entry.query]
        if not queries:
            queries = [entry.destination or "" for entry in history if entry.destination]

        docs: list[PackageDoc]
        if not queries:
            docs = self.engine.popular(limit)
        else:
            docs = self.engine.search_multi(queries, limit=limit)
        return [doc.to_dict() for doc in docs]

    def record(self, db: Session, **fields: str) -> UserHistory:
        entry = UserHistory(**fields)
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry
