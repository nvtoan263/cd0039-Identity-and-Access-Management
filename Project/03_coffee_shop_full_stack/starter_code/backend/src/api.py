import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
db_drop_and_create_all()

# ROUTES
'''
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods=["GET"])
def get_drinks():
     try:
        select_drinks = Drink.query.order_by(Drink.id).all()
        print("Select drinks:",select_drinks)
        if len(select_drinks) ==0:
            return jsonify({
                'success':True,
                'drinks':[]
            })
        else:
            formatted_drinks = [drink.short() for drink in select_drinks ]
            return jsonify({
                'success':True,
                'drinks':formatted_drinks
            })
     except Exception as e:
         print("get drinks exception",e)

'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks-detail', methods=["GET"])
@requires_auth('get:drinks-detail')
def get_drinks_details(payload):
     try:
        select_drinks = Drink.query.order_by(Drink.id).all()   
        print("Select drinks:",select_drinks)
        if len(select_drinks) ==0:
            # return success with empty drinks
            return jsonify({
                'success':True,
                'drinks':[]
            })
        else:
            formatted_drinks = [drink.long() for drink in select_drinks ]
            return jsonify({
                'success':True,
                'drinks':formatted_drinks
            })
     except Exception as e:
         print("get drinks-details exception",e)

'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks',methods=["POST"])
@requires_auth('post:drink')
def add_new_drink(payload):
    body = request.get_json()
    new_title = body.get('title')
    new_recipe = body.get('recipe')

    print("Body:", body)
    print(new_title, new_recipe)

    # Check for valid title and recipe
    if new_title is None or new_recipe is None:
        return jsonify({
            'success': False,
            'message': "Title and recipe are required"
        })

    # Check to make sure title is unique
    if Drink.query.filter(Drink.title == new_title).one_or_none() is not None:
        return jsonify({
            'success': False,
            'message': "Drink is already in the database"
        })
    # Ensure `new_recipe` is in list format as expected by the model
    try:
        # Wrap `new_recipe` in a list if it isn't already
        if not isinstance(new_recipe, list):
            new_recipe = [new_recipe]

        # Convert new_recipe to JSON string for storage
        drinks = Drink(title=new_title, recipe=json.dumps(new_recipe))
        drinks.insert()

        return jsonify({
            'success': True,
            'drinks': [drinks.long()]
        })
    except Exception as e:
        print("Post exception:", e)
        abort(422)

'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:id>',methods=["PATCH"])
@requires_auth('patch:drinks')
def update_drinks(payload,id):
    body = request.get_json()
    # if body is None abort with error 403
    if body is None:
        abort(403)
    print("Body:",body)
    new_tile = body.get('title')
    new_recipe =  body.get('recipe')
    drinks = Drink.query.filter(Drink.id==str(id)).all()
    print("Drinks:",drinks)
    try:
        if not drinks:
            abort(404)
        else:
            drinks = drinks[0]
            drinks.title=new_tile
            drinks.update() 
            return jsonify({
                'success':True,
                'drinks':[drinks.long()]
            })
    except Exception as e:
        print("Patch exception",e)


'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:id>',methods=["DELETE"])
@requires_auth('delete:drinks')
def delete_drinks(payload,id):
    try:
        drinks = Drink.query.get(id)
        if drinks is None:
            abort(404)
        else:
            drinks.delete()

        return jsonify({
                'success':True,
                'delete':drinks.id
            })
    except Exception as e:
        print("Delete Exception:",e)
        abort(422)

# Error Handling
'''
Example error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


'''
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''

'''
@TODO implement error handler for 404
    error handler should conform to general task above
'''
@app.errorhandler(404)
def not_found(error):
    return jsonify ({'success': False, 'error': 404,'message': 'Data not found'
                     }),404
    
@app.errorhandler(422)
def unprocessed(error):
    return jsonify({'success': False, 'error': 404,'message': 'The request can not be processed'
                    }),422

'''
@TODO implement error handler for AuthError
    error handler should conform to general task above
'''
@app.errorhandler(AuthError)
def handle_auth_error(error):

    response = jsonify(error.error)
    response.status_code = error.status_code
    return response