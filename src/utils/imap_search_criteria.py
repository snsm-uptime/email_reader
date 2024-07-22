from datetime import datetime


class IMAPSearchCriteria:
    def __init__(self):
        self.criteria = []

    def from_(self, email):
        self.criteria.append(f'FROM "{email}"')
        return self

    def to(self, email):
        self.criteria.append(f'TO "{email}"')
        return self

    def cc(self, email):
        self.criteria.append(f'CC "{email}"')
        return self

    def subject(self, subject):
        if subject:
            self.criteria.append(f'SUBJECT "{subject}"')
        return self

    def body(self, text):
        self.criteria.append(f'BODY "{text}"')
        return self

    def date_range(self, start_date: datetime, end_date: datetime):
        start = start_date.strftime("%d-%b-%Y")
        end = end_date.strftime("%d-%b-%Y")
        self.criteria.append(f'SINCE "{start}" BEFORE "{end}"')
        return self

    def unseen(self):
        self.criteria.append('UNSEEN')
        return self

    def deleted(self):
        self.criteria.append('DELETED')
        return self

    def draft(self):
        self.criteria.append('DRAFT')
        return self

    def flagged(self):
        self.criteria.append('FLAGGED')
        return self

    def recent(self):
        self.criteria.append('RECENT')
        return self

    def all(self):
        self.criteria.append('ALL')
        return self

    def and_(self, *criteria):
        combined = ' '.join(f'({c})' for c in criteria)
        self.criteria.append(f'({combined})')
        return self

    def or_(self, *criteria):
        combined = ' '.join(criteria)
        self.criteria.append(f'(OR {combined})')
        return self

    def not_(self, criterion):
        self.criteria.append(f'(NOT {criterion})')
        return self

    def build(self):
        return ' '.join(self.criteria)
