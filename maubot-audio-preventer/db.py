from sqlalchemy import Column, String, BigInteger
from sqlalchemy.engine.base import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from mautrix.types import UserID

from typing import NamedTuple, Optional

UserInfo = NamedTuple('UserInfo', text_warnings=int, kick_warnings=int)
Base = declarative_base()


class Warnings(Base):
    __tablename__ = "warnings"

    user_id: UserID = Column(String(255), primary_key=True, nullable=False)
    text_warnings = Column(BigInteger, primary_key=False, nullable=False)
    kick_warnings = Column(BigInteger, primary_key=False, nullable=False)


class Database:
    db: Engine

    def __init__(self, db: Engine) -> None:
        self.db = db
        Base.metadata.create_all(db)
        self.Session = sessionmaker(bind=self.db)

    def get_user(self, mxid: UserID) -> Optional[UserInfo]:
        s: Session = self.Session()
        try:
            row = s.query(Warnings).filter(Warnings.user_id == mxid).one()
            return UserInfo(text_warnings=row.text_warnings, kick_warnings=row.kick_warnings)
        finally:
            return None

    def add_user(self, mxid: UserID) -> None:
        token_row = Warnings(user_id=mxid, text_warnings=1, kick_warnings=0)
        s: Session = self.Session()
        s.add(token_row)
        s.commit()

    def increment_text_warnings(self, mxid: UserID, current_warnings: int) -> None:
        s: Session = self.Session()
        s.merge(Warnings(user_id=mxid, text_warnings=current_warnings+1))
        s.commit()

    def increment_kick_warnings(self, mxid: UserID, current_warnings: int) -> None:
        s: Session = self.Session()
        s.merge(Warnings(user_id=mxid, kick_warnings=current_warnings+1))
        s.commit()
