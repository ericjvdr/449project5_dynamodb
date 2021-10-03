CPSC 449-02 Fall '20

========================
|   ==: Project 5 :==   |
========================

Contributors:
-------------
Jason Otter
Eric Van Der Roest
Jordan Wermuth


Starting the Service:
---------------------
In order to start the service, one needs to make sure that DynamoDB Local has been configured and running per the instructions in the provided project documentation. 

Also, make sure the required python packages have been installed:
1) boto3
2) flask-dynamo
3) dotenv -

**NOTE**: .env file is very important, make sure this package is installed.

Once this has been done, starting the service requires the DB and test data to be created with the command:

> flask init 

from the cli in the project directory.

Once this has been completed, start the server like a normal flask application:

> flask run

the .env file should take care of everything, as it has all the environment variables required for use in the project.

at this point, the local server should be started and one can interact with the API with instructions provided in the API documentation.


