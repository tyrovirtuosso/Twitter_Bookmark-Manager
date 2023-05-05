import os
from dotenv import load_dotenv
load_dotenv()

mongo_atlas_pass = os.environ.get("MONGODB_ATLAS_PASS")

MONGO_CLOUD = True
MONGODB_CLUSTER_LOCAL= os.environ.get("MONGODB_CLUSTER_LOCAL")
MONGODB_CLUSTER_CLOUD= f"mongodb+srv://tyrovirtuosso:{mongo_atlas_pass}@cluster0.qee0lg0.mongodb.net/?retryWrites=true&w=majority"