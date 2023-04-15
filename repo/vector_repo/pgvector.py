from typing import List
from pgvector.sqlalchemy import Vector
from sqlalchemy import insert, Integer, String, text, create_engine, select
from sqlalchemy.orm import Session, declarative_base, mapped_column

from repo.vector_repo.base import VectorDB
from settings import PG_DB_NAME, PG_HOST, PG_PASSWORD, PG_PORT, PG_USER

# TODO: create a separate migration file and use alembic to migrate the database
Base = declarative_base()
class MyTable(Base):
    __tablename__ = 'my_table'

    id = mapped_column(Integer, primary_key=True)
    function_name = mapped_column(String)
    vector = mapped_column(Vector(3))

    def __repr__(self):
        return f'<MyTable(id={self.id}, function_name={self.function_name}, vector={self.vector})>'

class PgVectorDB(VectorDB):
    def __init__(self):
        # create a database session
        engine = create_engine(f'postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB_NAME}')
        with engine.connect() as conn:
            conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
            conn.commit()
        self.session = Session(engine)

        # create the table if it doesn't exist
        Base.metadata.create_all(engine)

    def add_vector_data(self, data_list: List[dict]):
        self.session.execute(insert(MyTable), data_list)

    def fetch_similar_vector_data(self, query_vector, query_limit):
        results = self.session.scalars(select(MyTable).order_by(MyTable.vector.max_inner_product(query_vector)).limit(query_limit))
        return results
    
    def fetch_all_data(self):
        results = self.session.query(MyTable).all()
        return results
    
    def delete_vector(self, function_name):
        record_to_delete = self.session.scalars(select(MyTable).filter(MyTable.function_name == function_name)).first()
        if record_to_delete:
             self.session.delete(record_to_delete)