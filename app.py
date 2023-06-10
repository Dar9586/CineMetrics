import json
from typing import Mapping, Any

from bson import ObjectId
from flask import Flask, render_template, request, jsonify, redirect, url_for, Response
from pymongo import MongoClient

# Number of items per page
ITEMS_PER_PAGE = 25

app = Flask(__name__)
client = MongoClient("mongodb://localhost:27017/")
db = client["DBFilm"]


# Set landing page
@app.route('/')
def landing_page():
    return render_template('landing.html')


@app.route('/create-document', methods=['POST'])
def create_object():
    # Riceve i dati del form per creare un nuovo documento nel database
    field_names = request.form.getlist('field_name[]')
    field_values = request.form.getlist('field_value[]')
    table = request.form.get("table")

    # Crea un nuovo oggetto dinamicamente usando i dati ricevuti dal form
    new_object = dict()
    for name, value in zip(field_names, field_values):
        if name == "_id":
            value = ObjectId(value)
        try:
            value = json.loads(value)
        except:
            pass
        new_object[name] = value

    # Esempio: Accesso all'oggetto creato dinamicamente
    for name, value in new_object.items():
        print(f"{name}: {value}")

    # Inserisce il nuovo oggetto nel database nella collezione specificata
    result = db[table].insert_one(new_object)

    if result.acknowledged:
        return "Object created successfully!"
    else:
        return "Error in create"


def render_query(collection_name: str, query: Mapping[str, Any], page: int):
    # Calcola il numero di documenti da saltare in base al numero di pagina e al numero di documenti per pagina
    skip = (page - 1) * ITEMS_PER_PAGE
    collection = db[collection_name]
    # Recupera i documenti dalla collezione con la paginazione
    items = collection.find(query).skip(skip).limit(ITEMS_PER_PAGE)

    # Conta il numero totale di documenti nella collezione
    total_items = collection.count_documents(query)

    # Calcola il numero totale di pagine in base al numero totale di documenti e al numero di documenti per pagina
    total_pages = total_items // ITEMS_PER_PAGE + (1 if total_items % ITEMS_PER_PAGE > 0 else 0)

    # Renderizza il template 'view-data.html' con i dati recuperati
    return render_template('view-data.html', col_name=collection_name, items=items, total_page=total_pages,
                           current_page=page)


@app.route('/apply-search')
def apply_search():
    # Riceve i parametri di ricerca dalla query string
    page = int(request.args.get("page"))
    field_names = request.args.getlist('field_name[]')
    field_operation = request.args.getlist('field_operation[]')
    field_values = request.args.getlist('field_value[]')
    table = request.args.get("table")

    # Crea un nuovo oggetto di query dinamicamente usando i parametri ricevuti dalla query string
    query = {}

    for name, op, value in zip(field_names, field_operation, field_values):
        if name == "_id":
            value = ObjectId(value)
        try:
            value = json.loads(value)
        except:
            pass

        condition = {op: value}
        if name in query:
            query[name][op] = value
        else:
            query[name] = condition

    # Esegue la ricerca e il rendering dei risultati
    return render_query(table, query, page)


@app.route('/get-fields')
def get_field_of_collection():
    # Riceve il nome della collezione
    selected_collection = request.args.get('collection')

    # Utilizza l'aggregazione per ottenere tutti i campi unici della collezione
    pipeline = [
        {
            "$project": {
                "fields": {"$objectToArray": "$$ROOT"}
            }
        },
        {
            "$unwind": "$fields"
        },
        {
            "$group": {
                "_id": None,
                "fields": {"$addToSet": "$fields.k"}
            }
        },
        {
            "$project": {
                "_id": 0,
                "fields": 1
            }
        }
    ]
    result = db[selected_collection].aggregate(pipeline)
    fields = result.next()["fields"]

    fields = list(fields)
    fields.remove("_id")
    fields.sort()

    # Restituisce i campi come JSON
    return jsonify(fields)


@app.route('/show/<collection_name>/<page>')
def get_data(collection_name, page):
    # Reindirizza alla pagina di ricerca con la collezione e il numero di pagina
    return redirect(url_for("apply_search", page=page, table=collection_name))


@app.route('/delete/<collection_name>/<document_id>', methods=['POST'])
def delete_document(collection_name, document_id):
    # Riceve il nome della collezione e l'ID del documento da eliminare
    print(collection_name, document_id)
    collection = db[collection_name]
    document_id = ObjectId(document_id)

    # Elimina il documento dalla collezione
    result = collection.delete_one({'_id': document_id})

    # Restituisce il numero di documenti eliminati come JSON
    return jsonify({'deleted_count': result.deleted_count})


@app.route('/search')
def search():
    # Ottiene i nomi delle collezioni presenti nel database
    collection_names = db.list_collection_names()
    collection_names.sort()

    # Renderizza il template 'search-document.html' con i nomi delle collezioni
    return render_template('search-document.html', col=collection_names)


@app.route('/add-document/admin')
def add_document_admin():
    auth = request.authorization

    if auth and auth.username == 'root' and auth.password == 'root':
        return render_template('add-document.html', is_admin=True)
    else:
        return Response('Unauthorized', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})


@app.route('/')
def home():
    return render_template('index.html', is_admin=True)


@app.route('/statistics/average-revenue')
def media_revenue():
    collection = db['movies_metadata']
    genre_list = collection.distinct('genres.name')
    genre_list.sort()
    genre = request.args.get("genre")
    average_revenue = ""
    if genre is not None:
        films = collection.find({
            '$and': [
                {'genres.name': genre},
                {'revenue': {'$type': 'number'}}
            ]
        }, {'revenue': 1})
        revenue_list = [film['revenue'] for film in films]
        average_revenue = sum(revenue_list) / len(revenue_list) if revenue_list else 0
    return render_template('statistica.html', genre_list=genre_list, genre=genre, average_revenue=average_revenue)


@app.route('/add-document')
def add_document():
    # Ottiene i nomi delle collezioni presenti nel database
    collection_names = db.list_collection_names()
    collection_names.sort()

    # Renderizza il template 'add-document.html' per gli utenti non amministratori
    return render_template('add-document.html', col=collection_names, is_admin=False)


@app.route('/update/<collection_name>/<object_id>')
def update_form(collection_name, object_id):
    collection = db[collection_name]
    document = collection.find_one({"_id": ObjectId(object_id)})
    del document["_id"]
    return render_template('modify.html', collection=document, collection_name=collection_name, object_id=object_id)


@app.route('/apply-update/<collection_name>/<object_id>', methods=["POST"])
def apply_update(collection_name, object_id):
    field_names = request.form.getlist('field_name[]')
    field_values = request.form.getlist('field_value[]')
    new_object = dict()
    for name, value in zip(field_names, field_values):
        if name == "_id":
            value = ObjectId(value)
        try:
            value = json.loads(value)
        except:
            pass
        new_object[name] = value
    print(new_object)
    result = db[collection_name].update_one({'_id': ObjectId(object_id)}, {'$set': new_object})
    if result.acknowledged:
        return "Object updated successfully!"
    else:
        return "Error in update"


@app.template_filter('sort_dict')
def sort_dict(dictionary):
    return sorted(dictionary.items())


if __name__ == '__main__':
    app.run(debug=True)
