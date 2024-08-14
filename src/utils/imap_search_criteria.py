from datetime import datetime
from typing import List, Optional


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
        combined = ' '.join(f'{c}' for c in criteria)
        self.criteria.append(combined)
        return self

    def or_(self, *criteria):
        combined = ' '.join(f'{c}' for c in criteria)
        self.criteria.append(f'(OR {combined})')
        return self

    def not_(self, criterion):
        self.criteria.append(f'(NOT {criterion})')
        return self

    def build(self):
        return ' '.join(self.criteria)


def define_criteria(
    start_date: datetime,
    end_date: datetime,
    senders: Optional[List[str]] = None,
    subjects: Optional[List[str]] = None,
):
    criteria = IMAPSearchCriteria().date_range(start_date, end_date)

    and_conditions: list[str] = []

    if senders:
        if len(senders) > 1:
            sender_conditions = [IMAPSearchCriteria().from_(
                sender).build() for sender in senders]
            and_conditions.append(
                IMAPSearchCriteria().or_(*sender_conditions).build())
        else:
            and_conditions.append(
                IMAPSearchCriteria().from_(senders[0]).build())

    if subjects:
        if len(subjects) > 1:
            subject_conditions = [IMAPSearchCriteria().subject(
                subject).build() for subject in subjects]
            and_conditions.append(IMAPSearchCriteria().or_(
                *subject_conditions).build())
        else:
            and_conditions.append(
                IMAPSearchCriteria().subject(subjects[0]).build())

    if and_conditions:
        criteria.and_(*and_conditions)

    return criteria
