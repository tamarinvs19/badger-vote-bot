import datetime
from collections import Counter
from typing import Callable

from sqlalchemy.orm import Session

from models import Suggestion, Vote
import config as cfg
import database


def get_db() -> Session:
    return database.SessionLocal()


class Storage(object):
    obj = None
    suggestions: dict[int, Suggestion] = {}  # suggestion_id -> Suggestion
    votes: dict[int, Vote] = {}  # user_id -> suggestion_id
    url: str = cfg.URL
    db: Callable[[], Session] = get_db
    session: Session

    @classmethod
    def __new__(cls, *args):
        if cls.obj is None:
            cls.obj = object.__new__(cls)
        cls.load_suggestions()
        return cls.obj

    @classmethod
    def load_suggestions(cls):
        session = cls.db()
        cls.session = session
        suggestions = session.query(Suggestion).all()
        cls.suggestions = {
            suggestion.pk: suggestion
            for suggestion in suggestions
        }
        votes = session.query(Vote).all()
        cls.votes = {
            vote.user_id: vote
            for vote in votes
        }

    @classmethod
    def save(cls, objs):
        cls.session.add_all(objs)
        cls.session.commit()

    def clear(self) -> str:
        """Clear today votes and return the most popular suggestion."""

        results = self.get_results()
        session = self.session
        try:
            most_popular = results.most_common()[0][0]
            most_popular_suggestion = self.get_suggestion_id_by_text(most_popular)
            mp = session.query(Suggestion).get(most_popular_suggestion.pk)
            session.delete(mp)
        except KeyError:
            most_popular = "Ни одного предложения"

        for vote in self.votes.values():
            v = session.query(Vote).get(vote.pk)
            session.delete(v)

        session.commit()

        return most_popular

    def get_suggestion_id_by_text(self, text: str) -> Suggestion:
        for pk, suggestion in self.suggestions.items():
            if suggestion.text == text:
                return suggestion

    def can_user_add_suggestion_today(self, user_id: int) -> bool:
        for suggestion in self.suggestions.values():
            date_check = (datetime.date.today() - suggestion.created_at.date()) < datetime.timedelta(days=1)
            if suggestion.creator_id == user_id and date_check:
                return False
        return True

    def add_suggestion(self, suggestion: Suggestion):
        self.save([suggestion])

    def get_results(self) -> Counter[str]:
        results = Counter()

        for vote in self.votes.values():
            results[self.suggestions[vote.suggestion_id].text] += 1

        for suggestion in self.suggestions.values():
            if suggestion.text not in results:
                results[suggestion.text] = 0

        return results

