# GÜDLFT Registration

This is a proof of concept (POC) project to show a light-weight version of our competition booking platform. The aim is the keep things as light as possible, and use feedback from the users to iterate. The main technology used here is Python with Flask.


## Installation

In order to use this project locally, you need to follow the steps below:

### First, 
let's duplicate the project github repository

```bash
>>> git clone https://github.com/Valkea/OC_P11.git
>>> cd OC_P11
```

### Secondly,
let's create a virtual environment and install the required Python libraries

(Linux or Mac)
```bash
>>> python3 -m venv venv
>>> source venv/bin/activate
>>> pip install -r requirements.txt
```

(Windows):
```bash
>>> py -m venv venv
>>> .\venv\Scripts\activate
>>> py -m pip install -r requirements.txt
```


## Running the project

Once installed, the only required command is the following one

```bash
>>> export FLASK_APP=server.py
>>> flask run
or
>>> python3 - m flask run
```

The app should respond with an address you should be able to go to using your browser.


## Using the project

visit the given addresse (usually *http://127.0.0.1:5000*) and use one of the demo credentials below:

* john@simplylift.co
* admin@irontemple.com
* kate@shelifts.co.uk

Note that, once all the places are booked or the points redeemed, the flask server needs to be restarted in order to reset all the data.


## Current Setup

The app is powered by:

* Python v3.x+
* [Flask](https://flask.palletsprojects.com/en/1.1.x/)
Whereas Django does a lot of things for us out of the box, Flask allows us to add only what we need.
* [JSON files](https://www.tutorialspoint.com/json/json_quick_guide.htm).
This is to get around having a DB until we actually need one. The main ones are:
     
	- *competitions.json* - list of competitions
	- *clubs.json* - list of clubs with relevant information.


## Tests

Unit-tests were written in order to test the route and functions.

You can run all the tests with the following command
```bash
>>> python -m pytest test_server.py -v
```


## Coverage

In order to see how weel we're testing, we decided to use a module called [coverage](https://coverage.readthedocs.io/en/coverage-5.1/).

First we need to run the tests **with the coverage** module using the following command line

```bash
>>> coverage run -m pytest test_server.py -v
```

Then we can produce an HTML report *(available in htmlcov)* with
```bash
>>> coverage html server.py
```

Or simply print the result in the Terminal using
```bash
>>> coverage report server.py
```


## Performance

Finally, in order to keep an eye on the performances of the application we decided to use the [Locust](https://www.locust.io/).

Start the Flask server as explained before, then run Locust
```bash
>>> locust
```
The app should respond with an address you should be able to go to using your browser.

Visit the given addresse (usually *http://127.0.0.1:8089*) and set it up swarm the system with some simultaneous users.

* *Number of total users to simulate*: 6
* *Spawn rate (users spawned/second)*: 1
* *Host*: (the address provided when runing flask server > usually http://127.0.0.1:5000)

### Failures

At some point, Locust will report *Failures* for the */puchasePlaces*, but this is an expected behavior. Once all the places are booked, the users continue to try booking places, but they are returned a 400 BAD REQUEST HTTP status code along with an error message (and the rest of the page), and Locust log these status code as failures.

Hance, you need to restart the Flask server to reset the data **before** each Locust performance test.
