from datetime import datetime


class IdGenerator(object):
    obj = None
    current_id = 0

    @classmethod
    def __new__(cls, *args):
        if cls.obj is None:
            cls.obj = object.__new__(cls)
        return cls.obj

    def next_id(self):
        self.current_id += 1
        return self.current_id


class Suggestion(object):
    pk: int
    text: str
    voter_count: int
    creator_id: int
    created_at: datetime.date

    def __init__(
            self,
            text: str,
            creator_id: int,
    ) -> None:
        self.pk = IdGenerator().next_id()
        self.text = text
        self.voter_count = 0
        self.creator_id = creator_id
        self.created_at = datetime.today()

    def __str__(self) -> str:
        return self.text
