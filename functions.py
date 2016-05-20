"""Functions for project""" 
from pprint import pprint

from flask import Flask, render_template, redirect, request, flash, session
from flask_sqlalchemy import SQLAlchemy
import urllib2
import json    
import os

from model import connect_to_db, db, User, Trip, UserTrip, Option, Flight, Leg, Airport



################################################################################

## validating ##

################################################################################



def is_valid_login(user_email, user_password):
    """Validates input email and password against users in db and returns true 
    if match and false if not match"""

    # Check User db for email and password match
    if User.query.filter_by(email=user_email, password=user_password).first():
        flash("Yay you're back!!!!!")
        # If match, add to session to indicate logged in user
        logged_in_user = User.query.filter_by(email=user_email, password=user_password).first()
        session["user_id"] = logged_in_user.user_id
        return True
    # Else, prompt to try again
    else:
        flash("Forgot your password you idiot! Try again.")
        return False



def is_registered_email(user_email):
    """Validates input user_email against emails in db"""

    # Checks if user email is already registered
    if User.query.filter_by(email=user_email).first():
        # Flash message if email is already used by a registered user
        flash("This email is already taken; please log in.")
        return True
    else:
        return False



################################################################################

## add records to db ##

################################################################################



def add_user_to_db(user_info):
    """Takes dictionary of user information and adds them to user attributes. Then 
    add new user to db"""

    # Instantiates user object with info from input user_info 
    user = User(email=user_info["user_email"], 
                password=user_info["user_password"],
                user_name=user_info["user_name"],
                origin_airport_code=user_info["user_origin_airport_code"])

    # Add user to session
    db.session.add(user)
    # Commit session to db
    db.session.commit()

    # Flash message to confirm registration
    flash("Thank you for registering; please log in.")

    return user



def add_trip_to_db(trip_info):
    """Takes dictionary of trip information and adds them to trip attributes. Then 
    add new trip to db"""

    # Instantiates trip object with info from input user_info
    trip = Trip(trip_name=trip_info["trip_name"])

    # Add user to session
    db.session.add(trip)
    # Commit session to db
    db.session.commit()

    return trip



def add_usertrip_to_db(usertrip_info):
    """Takes dictionary of usertrip information and adds them to usertrip attributes.
    Then add new usertrip to db"""

    # Instantiates usertrip object with info from input usertrip_info
    usertrip = UserTrip(user_id=usertrip_info["user_id"], trip_id=usertrip_info["trip_id"])

    # Add usertrip to session
    db.session.add(usertrip)
    # Commit session to db
    db.session.commit()

    return usertrip



def add_option_to_db(option_info):
    """Takes dictionary of option information and adds them to option attributes. 
    Then add new option to db"""

    # Instantiates option object with info from input option_info
    option = Option(trip_id=option_info["trip_id"], 
                    destination_airport_code=option_info["destination"], 
                    depart_date=option_info["departure_date"], 
                    return_date=option_info["return_date"])

    # Add option to session
    db.session.add(option)
    # Commit session to db
    db.session.commit()

    return option



def add_flight_to_db(option, flight_info):
    """Takes a option object and dictionary of flight information and adds them to flight 
    attributes. Then add new flight to db"""

    # Instantiates flight object with info from inputs option object and flight_info
    flight = Flight(option_id=option.option_id, flight_price=flight_info["flight_price"])

    # Add flight to session
    db.session.add(flight)
    # Commit session to db
    db.session.commit()

    return flight



def add_leg_to_db(flight, leg_info):
    """Takes a flight object and dictionary of leg information and adds them to leg 
    attributes. Then add new leg to db"""

    # Instantiates leg object with info from inputs flight object and leg_info
    leg = Leg(flight_id=flight.flight_id, 
              origin_airport_code=leg_info["origin_airport_code"],
              departure_datetime=leg_info["departure_datetime"], 
              destination_airport_code=leg_info["destination_airport_code"], 
              arrival_datetime=leg_info["arrival_datetime"], 
              leg_airline=leg_info["airline_code"], 
              leg_flight_code=leg_info["flight_code"],
              leg_duration=leg_info["leg_duration"])

    # Add leg to session
    db.session.add(leg)
    # Commit session to db
    db.session.commit()

    return leg



################################################################################

## query from db ##

################################################################################



def trips_by_user(user):
    """Takes input user object, and returns all trip objects associated with user"""

    # Get all usertrips associated with user
    usertrips = UserTrip.query.filter_by(user_id=user.user_id).all()

    # Initialize empty trips
    trips = []

    # Get every trip for the usertrips in usertrip_list
    for usertrip in usertrips:
        trips.append(Trip.query.get(usertrip.trip_id))

    return trips



def origin_airport_codes_by_trip(trip):
    """Takes input trip object, and returns all origin_airport_codes of users on 
    this trip"""

    # Instantiates empty list to put in origin airport codes
    origin_airport_codes = []
    # Iterates over usertrip for input trip and adds user's origin airport codes to list
    for usertrip in trip.usertrips:
        origin_airport_codes.append(usertrip.user.origin_airport_code)

    return origin_airport_codes



################################################################################

## QPX Query ##

################################################################################



def get_params(origin_airport_codes, option_info):
    """Gets parameter variables for a QPX search from user origin_airport_codes 
    and option"""

    # Initializes empty params list
    params = []
    count = 0
    # Adds a dictionary to params of parameters for every origin airport code
    for origin_airport_code in origin_airport_codes:
        params.append({})
        params[count]["num_travelers"] = 1
        params[count]["flight_origin"] = origin_airport_code
        params[count]["flight_destination"] = option_info["destination"]
        params[count]["departure_date"] = option_info["departure_date"]
        params[count]["return_date"] = option_info["return_date"]
        params[count]["max_price"] = "USD10000"
        count += 1

    return params



def parameter_by_params(query):
    """Get parameter dictionary from params"""

    # Get inputs from params into parameters
    parameter = {
      "request": {
        "passengers": {
          "kind": "qpxexpress#passengerCounts",
          "adultCount": query["num_travelers"],
        },
        "slice": [
          {
            # "kind": "qpxexpress#sliceInput",
            "origin": query["flight_origin"],
            "destination": query["flight_destination"],
            "date": query["departure_date"],
            "maxStops": 1,
          },
          {
            "origin": query["flight_destination"],
            "destination": query["flight_origin"],
            "date": query["return_date"],
            "maxStops": 1,            
          }
        ],
        # Hard coding number of flight options
        # QPX API takes up to 500
        "solutions": 2,
        "maxPrice": query["max_price"],
      }
    }

    return parameter



def query_QPX(parameter):
    """Send query with parameter and url to QPX"""

    # Get key from environment
    API_KEY = os.environ['QPX_KEY']

    # Insert key into QPX API url
    url = "https://www.googleapis.com/qpxExpress/v1/trips/search?key=%s" %(API_KEY)

    # Turns parameters into JSON string
    json_param = json.dumps(parameter, encoding = 'utf-8')

    # Sends JSON string request to QPX and returns JSON 
    flight_request = urllib2.Request(url, json_param, {'Content-Type': 'application/json'})

    return flight_request



################################################################################

## QPX Results ##

################################################################################



def QPX_results(flight_request):
    """Read results from query to QPX into python and add to list"""

    # Opens JSON results
    results = urllib2.urlopen(flight_request)

    # Read results and turn it into Python
    python_result = json.load(results)
    # Closes JSON results
    results.close()

    return python_result



def parse_results(python_results, option):
    """Takes inputs python_results and option object and parses the python_results
    to be ready to display on search results page."""

    # Gets option_id from option object
    option_id = option.option_id

    # Initiates empty flights dictionary
    flights = {}
    # Parsing QPX results to add to flights table
    for i in range(len(python_results)):
        for j in range(len(python_results[i]["trips"]["tripOption"])):
            flight_info = {"flight_price":python_results[i]["trips"]["tripOption"][j]["saleTotal"]}
            # Calls function to add flight to db
            flight = add_flight_to_db(option, flight_info)
            # Adds a new list value at flight object key in flights dictionary
            flights[flight] = []
            # Parsing QPX results to add to legs table
            for flight_slice in python_results[i]["trips"]["tripOption"][j]["slice"]:
                for flight_segment in flight_slice["segment"]:
                    leg_info = {}
                    leg_info["airline_code"] = flight_segment["flight"]["carrier"]
                    leg_info["flight_code"] = flight_segment["flight"]["number"]
                    leg_info["origin_airport_code"] = flight_segment["leg"][0]["origin"]
                    leg_info["destination_airport_code"] = flight_segment["leg"][0]["destination"]
                    leg_info["departure_datetime"] = flight_segment["leg"][0]["departureTime"]
                    leg_info["arrival_datetime"] = flight_segment["leg"][0]["arrivalTime"]
                    leg_info["leg_duration"] = flight_segment["leg"][0]["duration"]
                    # Calls function to add leg to db
                    leg = add_leg_to_db(flight, leg_info)
                    # Adds each leg to the list value at flight key
                    flights[flight].append(leg)

    return flights



################################################################################

## Other ##

################################################################################



def logout():
    """Logsout user by deleting user_id from session and flash confirmation message"""

    # Deletes user_id from session
    del session["user_id"]

    # Flash logout confirmation message
    flash("Don't leave meeeee!!!! :( ")

    return