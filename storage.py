import datetime
from collections import Counter

from models import Suggestion


class Storage(object):
    obj = None
    suggestions: dict[int, Suggestion] = {}  # suggestion_id -> Suggestion
    votes: dict[int, int] = {}  # user_id -> suggestion_id

    @classmethod
    def __new__(cls, *args):
        if cls.obj is None:
            cls.obj = object.__new__(cls)
            cls.suggestions = {}
            cls.votes = {}
        return cls.obj

    def get_suggestion_id_by_text(self, text: str) -> int:
        for pk, suggestion in self.suggestions.items():
            if suggestion.text == text:
                return pk

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

        for suggestion_id in self.votes.values():
            results[self.suggestions[suggestion_id].text] += 1

        for suggestion in self.suggestions.values():
            if suggestion.text not in results:
                results[suggestion.text] = 0

        return results

    def clear(self) -> str:
        """Clear today votes and return the most popular suggestion."""

        results = self.get_results()
        try:
            most_popular = results.most_common()[0][0]
            self.suggestions.pop(self.get_suggestion_id_by_text(most_popular))
        except KeyError:
            most_popular = "Ни одного предложения"

        self.votes = {}
        return most_popular

