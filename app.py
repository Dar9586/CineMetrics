import json
from typing import Mapping, Any

from bson import ObjectId
from flask import Flask, render_template, request, jsonify, redirect, url_for
from pymongo import MongoClient

# Number of items per page
ITEMS_PER_PAGE = 25

app = Flask(__name__)
client = MongoClient("mongodb://localhost:27017/")
db = client["DBFilm"]


@app.route('/create-document', methods=['POST'])
def create_object():
    field_names = request.form.getlist('field_name[]')
    field_values = request.form.getlist('field_value[]')
    table = request.form.get("table")
    # Create object dynamically
    new_object = dict()
    for name, value in zip(field_names, field_values):
        if name == "_id":
            value = ObjectId(value)
        try:
            value = json.loads(value)
        except:
            pass
        new_object[name] = value

    # Example: Accessing the dynamically created object
    for name, value in new_object.items():
        print(f"{name}: {value}")

    db[table].insert_one(new_object)

    return "Object created successfully!"


def render_query(collection_name: str, query: Mapping[str, Any], page: int):
    # Calculate the skip count based on the page number and items per page
    skip = (page - 1) * ITEMS_PER_PAGE
    collection = db[collection_name]
    # Fetch the items from the collection with pagination
    items = collection.find(query).skip(skip).limit(ITEMS_PER_PAGE)

    # Count the total number of items in the collection
    total_items = collection.count_documents(query)

    # Calculate the total number of pages based on the total items and items per page
    total_pages = total_items // ITEMS_PER_PAGE + (1 if total_items % ITEMS_PER_PAGE > 0 else 0)
    return render_template('view-data.html', col_name=collection_name, items=items, total_page=total_pages,
                           current_page=page)


@app.route('/apply-search', methods=['GET'])
def apply_search():
    page = int(request.args.get("page"))
    field_names = request.args.getlist('field_name[]')
    field_operation = request.args.getlist('field_operation[]')
    field_values = request.args.getlist('field_value[]')
    table = request.args.get("table")
    # Create object dynamically
    new_object = dict()
    for name, op, value in zip(field_names, field_operation, field_values):
        if name == "_id":
            value = ObjectId(value)
        try:
            value = json.loads(value)
        except:
            pass
        new_object[name] = {op: value}

    return render_query(table, new_object, page)


@app.route('/get-fields')
def get_field_of_collection():
    selected_collection = request.args.get('collection')
    # Use aggregation to get all unique fields
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
    return jsonify(fields)


@app.route('/show/<collection_name>/<page>')
def get_data(collection_name, page):
    return redirect(url_for("apply_search", page=page, table=collection_name))


@app.route('/delete/<collection_name>/<document_id>', methods=['POST'])
def delete_document(collection_name, document_id):
    print(collection_name, document_id)
    collection = db[collection_name]
    document_id = ObjectId(document_id)
    # Delete the document from the collection
    result = collection.delete_one({'_id': document_id})
    # Return the number of deleted documents
    return jsonify({'deleted_count': result.deleted_count})


@app.route('/search')
def search():
    collection_names = db.list_collection_names()
    collection_names.sort()
    return render_template('search-document.html', col=collection_names)


@app.route('/add-document/admin')
def add_document_admin():
    return render_template('add-document.html', is_admin=True)


@app.route('/add-document')
def add_document():
    collection_names = db.list_collection_names()
    collection_names.sort()
    return render_template('add-document.html', col=collection_names, is_admin=False)


if __name__ == '__main__':
    app.run(debug=True)
