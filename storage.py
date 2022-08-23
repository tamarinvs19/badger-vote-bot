from collections import Counter

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from models import Suggestion, Vote
import config as cfg


class Storage(object):
    obj = None
    suggestions: dict[int, Suggestion] = {}  # suggestion_id -> Suggestion
    votes: dict[int, Vote] = {}  # user_id -> suggestion_id
    url: str = cfg.URL

    @classmethod
    def __new__(cls, *args):
        if cls.obj is None:
            cls.obj = object.__new__(cls)
        cls.load_suggestions()
        return cls.obj

    @classmethod
    def load_suggestions(cls):
        engine = create_engine(cls.url)
        session = Session(bind=engine)
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
    def save(cls):
        engine = create_engine(cls.url)
        session = Session(bind=engine)
        session.add_all(cls.suggestions.values())
        session.add_all(cls.votes.values())
        session.commit()

    def clear(self) -> str:
        """Clear today votes and return the most popular suggestion."""

        engine = create_engine(self.url)
        session = Session(bind=engine)

        results = self.get_results()
        try:
            most_popular = results.most_common()[0][0]
            most_popular_suggestion = self.get_suggestion_id_by_text(most_popular)
            session.delete(most_popular_suggestion)
        except KeyError:
            most_popular = "Ни одного предложения"

        session.delete(self.votes.values())
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
        self.suggestions[suggestion.pk] = suggestion

    def get_results(self) -> Counter[str]:
        results = Counter()

        for vote in self.votes.values():
            results[self.suggestions[vote.suggestion_id].text] += 1

        for suggestion in self.suggestions.values():
            if suggestion.text not in results:
                results[suggestion.text] = 0

        return results

