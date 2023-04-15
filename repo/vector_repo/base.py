class VectorDB:
    def __init__(self):
        pass

    def add_vector_data(self, **kwargs):
        pass

    def fetch_similar_vector_data(self, **kwargs):
        pass

    def delete_vector(self, **kwargs):
        pass

def get_vector_db_client(debug=False):
    from repo.vector_repo.pgvector import PgVectorDB
    return PgVectorDB()