from pymongo import MongoClient
import csv
import os

MONGO_URL = "mongodb://localhost:27017"
MONGO_DB = "DBFilm"
PATH_WITH_CSV = "/home/dar9586/Downloads/theMoviesDataset"


def convert_folder_csv_to_json(folder_path, mongo):
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.csv'):
            mongo[file_name].drop()
            mongo[file_name[:-4]].drop()
            csv_file = os.path.join(folder_path, file_name)
            csv_to_json(csv_file, file_name, mongo)


def csv_to_json(csv_file, file_name, mongo):
    print("parsing " + file_name)
    data = []
    i = 1
    with open(csv_file, 'r') as file:
        csv_data = csv.DictReader(file)
        for row in csv_data:
            k: dict = row
            new_k = dict()
            for key, value in k.items():
                if value in ["id", "..."]:
                    new_k[key] = value
                    continue
                try:
                    new_k[key] = eval(value)
                    continue
                except:
                    pass
                new_k[key] = value
            data.append(new_k)
            if len(data) == 100000:
                print("batch " + str(i))
                i += 1
                try:
                    mongo[file_name[:-4]].insert_many(data, ordered=False)
                except:
                    print("ERROR ROW", row, "\n", new_k)
                    exit(1)
                data.clear()
    print(data[0])
    mongo[file_name[:-4]].insert_many(data, ordered=False)
    print("parsed " + file_name)


def main():
    mongodb_client = MongoClient(MONGO_URL)
    database = mongodb_client[MONGO_DB]
    convert_folder_csv_to_json(PATH_WITH_CSV, database)


if __name__ == '__main__':
    main()
