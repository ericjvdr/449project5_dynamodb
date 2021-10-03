from flask_dynamo import Dynamo
from boto3.dynamodb.conditions import Key, Attr
from flask import Flask, request, make_response, json, jsonify
from datetime import datetime

app = Flask(__name__)
app.config['DYNAMO_TABLES'] = [
    dict(
        TableName='Messages',
        KeySchema=[
            dict(AttributeName='messageId', KeyType='HASH'),
            dict(AttributeName='timestamp', KeyType='RANGE')
        ],
        AttributeDefinitions=[
            dict(AttributeName='messageId', AttributeType='S'),
            dict(AttributeName='timestamp', AttributeType='S'),
            dict(AttributeName='to', AttributeType='S'),
            dict(AttributeName='in-reply-to', AttributeType='S')
        ],
        GlobalSecondaryIndexes=[
            # index for getting all dms for a user
            dict(
                IndexName='to-index',
                KeySchema=[dict(AttributeName='to', KeyType= 'HASH')],
                Projection=dict(ProjectionType='ALL'),
                ProvisionedThroughput=dict(ReadCapacityUnits=1, WriteCapacityUnits=1)
            ),
            dict(
                IndexName='in-reply-to-index',
                KeySchema=[dict(AttributeName='in-reply-to', KeyType= 'HASH')],
                Projection=dict(ProjectionType='ALL'),
                ProvisionedThroughput=dict(ReadCapacityUnits=1, WriteCapacityUnits=1)
            )
        ],
        ProvisionedThroughput=dict(ReadCapacityUnits=5, WriteCapacityUnits=5)
    )        
]

dynamo = Dynamo(app)


#-----------------------------------------------------#
#------------------[ STATUS CODES ]-------------------#


# status - ok
def status_200(data):
	response = jsonify(data)
	response.status_code = 200
	response.mimetype = "application/json"
	return response

# status - resource created successfully
def status_201(data):
  response = jsonify(data)
  response.status_code = 201
  response.mimetype = "application/json"
  return response

# status - bad request
def status_400():
  err_message = {
    'status: ': 400,
    'message: ': 'Bad Request: ' + request.url
  }
  response = jsonify(err_message)
  response.status_code = 400
  response.mimetype = "application/json"
  return response

# status - password hashes don't match
def status_401():
  err_message = {
    'status: ': 401,
    'message: ': 'Unauthorized: ' + request.url
  }
  response = jsonify(err_message)
  response.status_code = 401
  response.mimetype = "application/jason"
  return response

# status - resource not found
def status_404():
  err_message = {
    'status: ': 404,
    'message: ': 'Not Found: ' + request.url
  }
  response = jsonify(err_message)
  response.status_code = 404
  response.mimetype = "application/json"
  return response

# status - record already exists
def status_409():
	err_message = { 
	'status: ': 409,
	'message: ': 'Conflict: ' + request.url,
	}
	response = jsonify(err_message)
	response.status_code = 409
	response.mimetype = "application/json"
	return response


#-----------------------------------------------------#
#-----------------[ CREATE DATABASE ]-----------------#


# cli - creates the database based on provided schema 
@app.cli.command('init')
def init_db():

    # remove all previous data
    dynamo.destroy_all() 

    with app.app_context():
        # creates all pre-defined dynamo tables
        dynamo.create_all()
    
    # insert some data into the database
    #now = datetime.utcnow()
    #print(now)
    #for table_name, table in dynamo.tables.items():
    #    print(table_name, table)

    # IF YOU ADD MORE ITEMS TO THIS DATA, MAKE SURE TO UPDATE THE COUNTER (Batch Item 0)
    # OTHERWISE YOU'LL BE WRITING IDS THAT ARE ALREADY IN USE
    with dynamo.tables['Messages'].batch_writer() as batch:
        # first item is basically the id incrementer
        batch.put_item(
            Item={
                'messageId': '0',
                'timestamp': str(datetime.utcnow()),
                'numRecords': '6'
            }
        )
        batch.put_item(
            Item={
                'messageId': '1',
                'typeId':'dm',
                'to': 'j-otterbox',
                'from':'jackie_chan',
                'message': 'hello j-otterbox! -jackie',
                'timestamp': str(datetime.utcnow()) 
            }
        )
        batch.put_item(
            Item={
                'messageId': '2',
                'typeId': 'dm',
                'to': 'j-otterbox',
                'from':'obama',
                'message': 'hello j-otterbox! -obama',
                'timestamp': str(datetime.utcnow()) 
            }
        )
        batch.put_item(
            Item={
                'messageId': '3',
                'typeId': 'rep',
                'in-reply-to': '1',
                'to': 'jackie_chan',
                'from':'j-otterbox',
                'message': 'hello jackie! replying to your earlier msg',
                'timestamp': str(datetime.utcnow()) 
            }
        )
        batch.put_item(
            Item={
                'messageId': '4',
                'typeId': 'rep',
                'in-reply-to': '2',
                'to': 'obama',
                'from':'j-otterbox',
                'message': 'hello obama! -j-otterbox',
                'timestamp': str(datetime.utcnow()) 
            }
        )
        batch.put_item(
            Item={
                'messageId': '5',
                'typeId': 'rep',
                'in-reply-to': '2',
                'to': 'obama',
                'from':'j-otterbox',
                'message': 'really? you gonna leave me on read?',
                'timestamp': str(datetime.utcnow()) 
            }
        )
        batch.put_item(
            Item={
                'messageId': '6',
                'typeId': 'rep',
                'in-reply-to': '2',
                'to': 'obama',
                'from': 'j-otterbox',
                'message': 'testing message',
                'timestamp': str(datetime.utcnow())
            }
        )

    # insert new dm
    #response = dynamo.tables['Messages'].put_item(Item={
    #   'messageId': str(id_tracker),
    #   'timestamp': str(datetime.utcnow()),
    #})

    # #item = response['Items']
    # print(id_tracker)

    # show counter is at zero to start
    response = dynamo.tables['Messages'].query(
        KeyConditionExpression=Key('messageId').eq('0')
    )
    items = response['Items']
    
    # get num records as string
    print(items[0])

    # convert it to int and add 1
    numRecords = int(items[0]['numRecords']) + 1
    timestamp = items[0]['timestamp']

    #print(timestamp)
  
    # update record 0 (aka: the counter)
    response = dynamo.tables['Messages'].update_item(
        Key={
            'messageId':'0',
            'timestamp': timestamp
        },
        UpdateExpression='SET numRecords = :newNumRecs',
        ExpressionAttributeValues={
            ':newNumRecs': str(numRecords)
        }
    )

    # check that counter was updated
    # response = dynamo.tables['Messages'].query(
    #     KeyConditionExpression=Key('messageId').eq('0')
    # )
    # items = response['Items']
    # print(items)

#----------------------------------------------#
#------------------[ ROUTES ]------------------#

@app.route('/')
def hello_world():
    return '<h1>Project 5 API</h1>'

@app.route('/users/<username>/dms', methods=['GET', 'POST'])
def routeDmsRequest(username):
    # send a dm to user by username
    if request.method == 'POST':
        
        req_data = request.get_json()
        # get data from request body
        fr0m = req_data.get('from')
        quickReplies= req_data.get('quickReplies')
        message = req_data.get('message')

        # if the user gave parameters, but the keys are incorrect
        if not fr0m or not message:
            return status_400()

        # query item 0
        response = dynamo.tables['Messages'].query(
        KeyConditionExpression=Key('messageId').eq('0')
        )
        items = response['Items']

        # get numRecords and add 1 for new messageId
        numRecords = int(items[0]['numRecords']) + 1
        timestamp = items[0]['timestamp']

        # insert new dm w/ quick replies
        if quickReplies != None:
            response = dynamo.tables['Messages'].put_item(Item={
                'messageId': str(numRecords),
                'typeId': 'dm',
                'to': username,
                'from': fr0m,
                'message': message,
                'timestamp': str(datetime.utcnow()),
                'quickReplies': quickReplies
            })
        # insert new dm w/o quickReplies
        else:
            response = dynamo.tables['Messages'].put_item(Item={
                'messageId': str(numRecords),
                'typeId': 'dm',
                'to': username,
                'from': fr0m,
                'message': message,
                'timestamp': str(datetime.utcnow()),
            })

        # update record 0 (aka: the counter)
        updateCounter = dynamo.tables['Messages'].update_item(
            Key={
                'messageId':'0',
                'timestamp': timestamp
            },
            UpdateExpression='SET numRecords = :newNumRecs',
            ExpressionAttributeValues={
                ':newNumRecs': str(numRecords)
            }
        )

        # create response msg
        response = {
            #"location": request.url + "/api/accounts",
            "message": "Created: " + request.url,
            "status": 201,
        }
        # resource created successfully
        return status_201(response)
       
        #return f'sending a new DM to {username}, from {fr0m}, that says: {message}'

    # list dms for user by username
    else:
        response = dynamo.tables['Messages'].query(
            IndexName='to-index',
            KeyConditionExpression=Key('to').eq(username),
            FilterExpression=Attr('typeId').eq('dm')
        )
        items = response['Items']
        print(items)     

        jsonify(items)

        # if dms or username do not exist
        if items == []:
            return status_404()
        # if they do exist
        else: return status_200(items)
        #return f'getting dms for user: {username}'


@app.route('/dms/<id>/replies', methods=['GET','POST'])
def routeRepliesRequest(id):
    # reply to dm by id
    if request.method == 'POST':
       
        req_data = request.get_json()
        # get data from request body
        reply = req_data.get('reply')

        # if the user gave parameters, but the keys are incorrect
        if not reply:
            return status_400()

        # query db for item being replied to
        response = dynamo.tables['Messages'].query(
            KeyConditionExpression=Key('messageId').eq(id)
        )
        item = response['Items']

        # check if the item has a key named quickReplies
        if 'quickReplies' in item[0].keys():

            # look for a matching key based on given reply
            for option in item[0]['quickReplies']:

                # if there's a match, get the value of the key and exit the loop
                if reply == option:
                    reply = item[0]['quickReplies'][option]
                    continue

        # print(f"reply going into DB = {reply}")

        # query item 0
        response = dynamo.tables['Messages'].query(
            KeyConditionExpression=Key('messageId').eq('0')
        )
        items = response['Items']

        # get numRecords and add 1 for new messageId
        numRecords = int(items[0]['numRecords']) + 1
        timestamp = items[0]['timestamp']

        # query messageId
        response = dynamo.tables['Messages'].query(
            KeyConditionExpression=Key('messageId').eq(id)
        )
        items = response['Items']
        to = items[0]['from']
        fr0m = items[0]['to']

        # insert new reply
        response = dynamo.tables['Messages'].put_item(Item={
            'messageId': str(numRecords),
            'typeId': 'rep',
            'in-reply-to': id,
            'to': to,
            'from': fr0m,
            'message': reply,
            'timestamp': str(datetime.utcnow()),
        })

        # update record 0 (aka: the counter)
        updateCounter = dynamo.tables['Messages'].update_item(
            Key={
                'messageId':'0',
                'timestamp': timestamp
            },
            UpdateExpression='SET numRecords = :newNumRecs',
            ExpressionAttributeValues={
                ':newNumRecs': str(numRecords)
            }
        )

        # # create response msg
        response = {
            "location": request.url + "/api/accounts",
            "message": "Created: " + request.url,
            "status": 201,
        }
        # resource created successfully
        return status_201(response)
        # return f'new reply to dm #{id} with reply: {reply}'
    # list replies to dm by id
    else:
        response = dynamo.tables['Messages'].query(
            IndexName='in-reply-to-index',
            KeyConditionExpression=Key('in-reply-to').eq(id)
        )
        items = response['Items']
        #print(items)  

        jsonify(items)

        # if messageId does not exist
        if items == []:
            return status_404()
        # if messageId does exist
        else: return status_200(items)
        #return f'getting replies to dm #{id}'

@app.errorhandler(404)	
def route_not_found(error = None):
	message = { 
	'status: ': 404,
	'message: ': 'Route Not Found: ' + request.url
	}
	response = jsonify(message)
	response.status_code = 404
	response.mimetype = "application/json"
	return response 



