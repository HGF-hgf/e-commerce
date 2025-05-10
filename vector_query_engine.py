class VectorQueryEngine:
    def __init__(self, collection, embedding_model, vector_index_name, num_candidates):
        self.collection = collection
        self.embedding_model = embedding_model
        self.vector_index_name = vector_index_name
        self.num_candidates = num_candidates

    def query(self, query_text, limit=4):
        query_embedding = self.embedding_model(query_text)
        num_candidates = self.num_candidates
        
        vector_search_stage = {
            "$vectorSearch": {
                "index": self.vector_index_name,
                "path": "embedding",
                "queryVector": query_embedding,
                "numCandidates": num_candidates,
                "limit": limit
            }
        }

        project_stage = {
            "$project": {
                "_id": 0,
                "product_id": 1,
                "name": 1,
                "price": 1,
                "image": 1,
                "brand": 1,
                "description": 1,
                "technical_info": 1,
                "score": {"$meta": "vectorSearchScore"}
            }
        }

        pipeline = [vector_search_stage, project_stage]
        results = self.collection.aggregate(pipeline)
        return list(results)
    
    
    def queries(self, query_text, limit=4):
        query_embedding = self.embedding_model(query_text)
        num_candidates = self.num_candidates
        
        vector_search_stage = {
            "$vectorSearch": {
                "index": self.vector_index_name,
                "path": "embedding",
                "queryVector": query_embedding,
                "numCandidates": num_candidates,
                "limit": limit
            }
        }

        project_stage = {
            "$project": {
                "_id": 0,
                "product_id": 1,
                "score": {"$meta": "vectorSearchScore"}
            }
        }

        pipeline = [vector_search_stage, project_stage]
        results = self.collection.aggregate(pipeline)
        return list(results)