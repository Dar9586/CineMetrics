from bson import ObjectId
from flask import Flask, render_template, request, redirect, jsonify
from pymongo import MongoClient

app = Flask(__name__)
client = MongoClient("mongodb://localhost:27017/")
db = client["DBFilm"]
movies_collection = db["movies_metadata"]


@app.route('/create-document-admin', methods=['POST'])
@app.route('/create-document', methods=['POST'])
def create_object():
    field_names = request.form.getlist('field_name[]')
    field_values = request.form.getlist('field_value[]')
    table = request.form.get("table")
    # Create object dynamically
    new_object = dict()
    for name, value in zip(field_names, field_values):
        new_object[name] = value

    # Example: Accessing the dynamically created object
    for name, value in new_object.items():
        print(f"{name}: {value}")

    db[table].insert_one(new_object)

    return "Object created successfully!"


@app.route('/apply-search', methods=['GET'])
def apply_search():
    page = int(request.args.get("page"))
    field_names = request.args.getlist('field_name[]')
    field_operation = request.args.getlist('field_operation[]')
    field_values = request.args.getlist('field_value[]')
    print(field_names, field_operation, field_values, sep="\n")
    table = request.args.get("table")
    # Create object dynamically
    new_object = dict()
    for name, op, value in zip(field_names, field_operation, field_values):
        new_object[name] = {op: value}

    # Example: Accessing the dynamically created object
    print(field_names, field_operation, field_values, new_object, sep="\n")
    cursor = db[table].find(new_object)
    count = db[table].count_documents(new_object)
    print(count)
    skip = (page - 1) * ITEMS_PER_PAGE
    # Fetch the items from the collection with pagination
    items = cursor

    # Count the total number of items in the collection
    total_items = count

    # Calculate the total number of pages based on the total items and items per page
    total_pages = total_items // ITEMS_PER_PAGE + (1 if total_items % ITEMS_PER_PAGE > 0 else 0)
    print(items)
    return render_template('view-data.html', col_name=table, items=items, total_page=total_pages,
                           current_page=page)


@app.route('/get-fields')
def ciao():
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

    # Extract the fields from the result
    fields = result.next()["fields"]

    fields = list(fields)
    fields.remove("_id")
    fields.sort()
    return jsonify(fields)


# Number of items per page
ITEMS_PER_PAGE = 10


@app.route('/show/<collection_name>/<page>')
def get_data(collection_name, page):
    # Get the current page number from the query parameter
    page = int(page)
    # Calculate the skip count based on the page number and items per page
    skip = (page - 1) * ITEMS_PER_PAGE
    collection = db[collection_name]
    # Fetch the items from the collection with pagination
    items = collection.find().skip(skip).limit(ITEMS_PER_PAGE)

    # Count the total number of items in the collection
    total_items = collection.count_documents({})

    # Calculate the total number of pages based on the total items and items per page
    total_pages = total_items // ITEMS_PER_PAGE + (1 if total_items % ITEMS_PER_PAGE > 0 else 0)
    print(items)
    return render_template('view-data.html', col_name=collection_name, items=items, total_page=total_pages,
                           current_page=page)


@app.route('/delete/<collection_name>/<document_id>', methods=['POST'])
def delete_document(collection_name, document_id):
    print(collection_name, document_id)
    collection = db[collection_name]
    document_id = ObjectId(document_id)
    # Delete the document from the collection
    result = collection.delete_one({'_id': document_id})
    # Return the number of deleted documents
    return jsonify({'deleted_count': result.deleted_count})


# Custom Jinja2 filter
@app.template_filter('range_custom')
def range_custom(start, end):
    return range(start, end)


@app.route('/add-document')
def add_document():
    # Get field names from the collection
    field_names = list(movies_collection.find_one().keys())
    field_names.remove("_id")
    field_names.sort()
    collection_names = db.list_collection_names()
    collection_names.sort()
    return render_template('add-document.html', col=collection_names)


@app.route('/search')
def search():
    # Get field names from the collection
    field_names = list(movies_collection.find_one().keys())
    field_names.remove("_id")
    field_names.sort()
    collection_names = db.list_collection_names()
    collection_names.sort()
    return render_template('search-document.html', col=collection_names)


@app.route('/add-document-admin')
def add_document_admin():
    # Get field names from the collection
    field_names = list(movies_collection.find_one().keys())
    field_names.remove("_id")
    field_names.sort()
    return render_template('add-document-admin.html')


if __name__ == '__main__':
    app.run(debug=True)
