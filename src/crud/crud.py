import sqlalchemy
from sqlalchemy import event, select, delete, and_
from sqlalchemy.orm import sessionmaker

from src.crud.sqlmodel import Session, SessionDescription, ConversationMemory
from src.brain.types import Interaction

import src.routers.schema.session as schema_session


class CRUD:
    def __init__(self, dbase: str):
        self._engine = sqlalchemy.create_engine(dbase)

        def _fk_pragma_on_connect(dbapi_con, _):
            dbapi_con.execute("pragma foreign_keys=ON")

        event.listen(self._engine, "connect", _fk_pragma_on_connect)

        self._sessionmaker = sessionmaker(self._engine)
        self._cleanse_unpersisted()

    def _cleanse_unpersisted(self):
        with self._sessionmaker() as session:
            stmt = delete(Session).where(Session.persist.is_(False))
            session.execute(stmt)
            session.commit()

    def get_session_id(self, session_name: str) -> int:
        with self._sessionmaker() as session:
            stmt = select(Session.session_id).where(Session.name == session_name)
            result = session.execute(stmt).scalar()
            if result is None:
                raise ValueError(f"No session with name {session_name}")
            return result

    def new_session(self, name, description):
        with self._sessionmaker() as session:
            new_session = Session(name=name, persist=False)
            session.add(new_session)
            session.flush()
            session_description = SessionDescription(
                session_id=new_session.session_id, description=description
            )
            session.add(session_description)
            session.commit()

    def list_sessions(self) -> list[schema_session.Session]:

        with self._sessionmaker() as session:
            stmt = (
                select(Session)
                .where(Session.persist.is_(True))
                .order_by(Session.session_id)
            )
            results = session.execute(stmt).scalars().all()

            return [
                schema_session.Session(session_id=result.session_id, name=result.name)
                for result in results
            ]

    def insert_session(self, session_name: str) -> int:
        with self._sessionmaker() as session:
            new_session = Session(name=session_name, persist=False)
            session.add(new_session)
            session.commit()
            return new_session.session_id

    def get_interactions(self, session_id: int) -> list[Interaction]:
        with self._sessionmaker() as session:
            stmt = (
                select(ConversationMemory)
                .join(
                    Session,
                    and_(
                        Session.session_id == ConversationMemory.session_id,
                        Session.session_id == session_id,
                    ),
                )
                .order_by(ConversationMemory.conversation_memory_id.asc())
            )
            result = session.execute(stmt).scalars().all()
            return [
                Interaction(
                    id_=memory.conversation_memory_id,
                    user_input=memory.user_input,
                    llm_output=memory.llm_output,
                )
                for memory in result
            ]

    def insert_interaction(self, session_id: int, interaction: Interaction):
        memory = ConversationMemory(
            session_id=session_id,
            user_input=interaction.user_input,
            llm_output=interaction.llm_output,
        )
        with self._sessionmaker() as session:
            session.add(memory)
            session.commit()


crud_instance = CRUD(dbase="sqlite:///memory.db")
