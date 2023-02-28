import yaml
from pydantic import BaseSettings
from pymongo import MongoClient


def get_db_connection():
    with open("config.yaml", "r") as f:
        db_config = yaml.safe_load(f)
    return db_config


class Client(BaseSettings):
    uri: str
    client: MongoClient = None

    def connect(self):
        self.client = MongoClient(self.uri)


DB_CONFIG = get_db_connection()
assert (
    DB_CONFIG["mongodb"]["uri"] is not None
), "MongoDB mongodb.uri is not set, check config.yaml"
BUSSE_PRICING_DATA = DB_CONFIG["mongodb"]["databases"]["busse_pricing"]["key"]
assert (
    BUSSE_PRICING_DATA is not None
), "MongoDB databases.busse_pricing.key is not set, check config.yaml"
CONTRACTS = DB_CONFIG["mongodb"]["databases"]["busse_pricing"]["contracts"]
assert (
    CONTRACTS is not None
), "MongoDB databases.busse_pricing.contracts is not set, check config.yaml"
COSTS = DB_CONFIG["mongodb"]["databases"]["busse_pricing"]["costs"]
assert (
    COSTS is not None
), "MongoDB databases.busse_pricing.costs is not set, check config.yaml"


client = Client(uri=DB_CONFIG["mongodb"]["uri"])
client.connect()

contracts = client.client[BUSSE_PRICING_DATA][CONTRACTS]
costs = client.client[BUSSE_PRICING_DATA][COSTS]

if __name__ == "__main__":
    print(contracts)
