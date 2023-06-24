from pymongo import MongoClient

MONGO_URL = "mongodb://localhost:27017"
MONGO_DB = "DBFilm"


def main():
    mongodb_client = MongoClient(MONGO_URL)
    database = mongodb_client[MONGO_DB]
    database["movies_metadata"].create_index("production_countries.iso_3166_1")


if __name__ == '__main__':
    main()
