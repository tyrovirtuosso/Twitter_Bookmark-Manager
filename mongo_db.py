from pymongo import MongoClient

class MongoDB():
    def __init__(self) -> None:
        cluster = "mongodb://127.0.0.1:27017/?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongosh+1.8.2"    
        self.client = MongoClient(cluster)
     
    def check_collection(self, db_name, collection_name):
        if collection_name in db_name.list_collection_names():
            return True
        
    def check_db(self, db_name:str):
        if db_name in self.client.list_database_names():
            return True
        
if __name__ == "__main__":
    mongo = MongoDB()
    mongo.check_db('Twitter')

