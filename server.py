"""Server for project"""

from jinja2 import StrictUndefined
from flask import Flask, render_template, redirect, request, flash, session, jsonify
# from flask_debugtoolbar import DebugToolbarExtension
from flask_sqlalchemy import SQLAlchemy
from pprint import pprint
import json

# File that holds my db classes and tables
from model import connect_to_db, db, User, Trip, UserTrip, Option, Flight, Leg, Airport

# File that holds my functionalities
import functions



app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# Undefined variable in Jinja2 raises an error
app.jinja_env.undefined = StrictUndefined


################################################################################

## default pages routes ##

################################################################################



@app.route('/')
def index():
    """Homepage"""

    if session.get("user_id"):
        return redirect("/profile")
    else:
        return render_template("homepage.html")



@app.route('/profile')
def profile():
    """User profile page"""

    # Get logged in user
    user = User.query.get(session['user_id'])
    # Get list of trips for user
    trips = functions.trips_by_user(user)

    images_list = ["/static/images/ny.jpg", "/static/images/ny.jpg", "/static/images/ny.jpg", "/static/images/ny.jpg", "/static/images/ny.jpg", "/static/images/ny.jpg", "/static/images/ny.jpg", "/static/images/ny.jpg", "/static/images/ny.jpg", "/static/images/ny.jpg", "/static/images/ny.jpg", "/static/images/ny.jpg", "/static/images/ny.jpg", "/static/images/ny.jpg", "/static/images/ny.jpg", "/static/images/ny.jpg", "/static/images/ny.jpg", "/static/images/ny.jpg", "/static/images/ny.jpg", "/static/images/ny.jpg", "/static/images/ny.jpg", "/static/images/ny.jpg", "/static/images/ny.jpg", "/static/images/ny.jpg", "/static/images/ny.jpg", "/static/images/ny.jpg", "/static/images/ny.jpg", "/static/images/ny.jpg", "/static/images/ny.jpg", "/static/images/ny.jpg","/static/images/ny.jpg", "/static/images/ny.jpg", "/static/images/ny.jpg", "/static/images/ny.jpg", "/static/images/ny.jpg", "/static/images/shanghai.jpg", "/static/images/london.jpg", "/static/images/rome.jpg", "/static/images/kyoto.jpg", "/static/images/rome.jpg", "/static/images/peru.jpg", "/static/css/IMG_6526.jpg", "/static/images/IMG_6526.jpg", "/static/images/IMG_6526.jpg", "/static/css/IMG_6526.jpg"]

    return render_template("profile.html", user=user, trips=trips, images_list=images_list)



@app.route('/settings')
def settings():
    """User settings page"""

    return render_template("settings.html")



################################################################################

## login/logout routes ##

################################################################################



@app.route('/login', methods=["POST"])
def user_login():
    """Checks if email and password match in db
       and logs in user if match"""

    # Get email and password from the user login
    user_email = request.form.get('email')
    user_password = request.form.get('user-password')

    # Validate user_email and login and redirects depending on validity
    if functions.is_valid_login(user_email, user_password):
        return redirect('/profile')
    else:
        return redirect('/')



@app.route('/logout')
def user_logout():
    """Logs out user"""

    # Logs out user
    functions.logout()

    return redirect('/')



################################################################################

## user registration routes ##

################################################################################

# @app.route('/user', methods=['POST', 'GET'])
# def user():
#     if method == 'POST':
#         return do_post()  # register the user
#     elif method == 'GET':
#         return do_get()  # get the user registration form

# @app.route('/user-reg-form')
# def user_reg_form():
#     """Takes user to user registration form"""

#     # Takes user directly to user registration page without any checks
#     return render_template('user_registration.html')



@app.route('/user-registration', methods=["POST"])
def user_registration():
    """Check if user in db, if not, add"""

    # Initialize empty dictionary for user info
    user_info = {}

    # Get inputs from user registration form
    user_info["user_email"] = request.form.get('user-email')
    user_info["user_password"] = request.form.get('user-password')
    user_info["user_name"] = request.form.get('username')
    # jQuery UI autocomplete added, so limit first 3 characters to add to db
    user_info["user_origin_airport_code"] = ((request.form.get('origin_airport_code')).upper())[:3]

    # Checks if email is in the db already
    if functions.is_registered_email(user_info["user_email"]) == False:
        # Add user in db if email is not already in db
        functions.add_user_to_db(user_info)

    return redirect('/')



################################################################################

## trip add/delete routes ##

################################################################################



# /profile/trip/{id}  # DELETE
@app.route('/profile/trip-delete', methods=["POST"])  # DELETE
def trip_delete():
    """Delete trip and all option, flight, and leg data associated with that trip
    in db, ajax call"""

    # Get trip to delete
    trip_id = request.form.get("trip-id-delete")
    trip = Trip.query.get(trip_id)

    # Get all options for the trip
    options = functions.options_by_trip(trip)
    for option in options:
        # Get all flights for the options
        flights = functions.flights_by_option(option)
        for flight in flights:
            # Get all legs for the flights
            legs = functions.legs_by_flight(flight)
            # Delete legs
            functions.delete_legs(legs)
            db.session.commit()
        # Delete flights
        functions.delete_flights(flights)
    # Delete options
    functions.delete_options(options)

    # Get all userstrips and delete
    userstrips = functions.userstrips_by_trip(trip)
    functions.delete_userstrips(userstrips)

    # Delete trip
    db.session.delete(trip)
    db.session.commit()

    return redirect('/profile')



@app.route('/trip/create-new', methods=["POST"])
def trip_add():
    """Trip details page"""

    # Initialize empty dictionary to add trip info to
    trip_info = {}
    # Get trip name from form and add trip to db
    trip_info["trip_name"] = request.form.get("trip_name")
    # Add trip object to db and assign trip to variable
    trip = functions.add_trip_to_db(trip_info)

    # Initialize empty dictionary to add usertrip info to
    usertrip_info = {}
    # Get user_id from session
    usertrip_info["user_id"] = session["user_id"]
    # Get trip_id from trip
    usertrip_info["trip_id"] = trip.trip_id
    # Add usertrip object to db
    functions.add_usertrip_to_db(usertrip_info)

    # Initialize empty list for user emails
    emails = []
    # Add user emails from form to user_emails list
    for x in range(5):
        if request.form.get("trip_user%s" %(x)):
            emails.append(request.form.get("trip_user%s" %(x)))

    # For all emails entered in input
    for email in emails:
        # Validates if email in db
        if functions.is_registered_email(email):
            # Get user from registered email
            user = User.query.filter_by(email=email).first()
            # Get usertrip_info
            usertrip_info = {"user_id":user.user_id, "trip_id":trip.trip_id}
            # Add usertrip to db
            functions.add_usertrip_to_db(usertrip_info)
        # Else flash user not in db
        else:
            flash("User not in db: " + email)

    return redirect("/profile")



################################################################################

## trip details, search/result, and share routes ##

################################################################################



@app.route('/trip/<int:trip_id>')
def trip_detail(trip_id):
    """Display trip details page"""

    # Get trip from trip_id
    trip = Trip.query.get(trip_id)
    # Get all options for a trip
    options = trip.options

    userstrips = functions.userstrips_by_trip(trip)
    travelers = functions.travelers_by_userstrips(userstrips)

    # Get user that's logged in
    user = User.query.get(session["user_id"])

    flight_prices = {}
    for option in options:
        flights = functions.flights_by_option(option)
        for flight in flights: 
            flight_prices[option.destination_airport_code] = flight.flight_price
    
    return render_template("trip_detail.html", trip=trip, options=options, user=user, travelers=travelers, flight_prices=flight_prices)

@app.route('/chart1.json', methods=["POST"])
def chart1():
    """Grab all flight options and prices data to populate Chart 1, ajax call"""

    # Get trip_id
    trip_id = request.form.get("trip_id")
    # Get trip
    trip = Trip.query.get(trip_id)

    labels_chart = []
    # Get options as columns
    for option in trip.options:
        labels_chart.append(option.option_id)

    chart_data = []
    # Get flight prices for each option
    i = 0
    for option in trip.options:
        chart_data.append(0)
        for flight in option.flights:
            chart_data[i] += float(flight.flight_price[3:])
        i += 1
    # Parameters of the chart
    datasets_chart = [
            {
                "label": "Options by Prices",
                "borderColor": "rgba(2,29,66,1)",
                "borderWidth": 1,
                "hoverBackgroundColor": "rgba(2,29,66,0.4)",
                "hoverBorderColor": "rgba(2,29,66,1)",
                "data": chart_data,
            }
        ]
    # Data to populate the Chart.js.chart
    data = {
        "labels": labels_chart,
        "datasets": datasets_chart
    }

    return jsonify(data)



@app.route('/chart2.json', methods=["POST"])
def chart2():
    """Grab all flight options and vote tally data to populate Chart 2, ajax call"""

    # Get trip_id
    trip_id = request.form.get("trip_id")
    # Get trip
    trip = Trip.query.get(trip_id)

    labels_chart = []
    # Get options as columns
    for option in trip.options:
        labels_chart.append(option.option_id)

    chart_data = []
    # Get vote tallies for each option
    i = 0
    for option in trip.options:
        chart_data.append(0)
        for usertrip in trip.usertrips:
            if usertrip.option_vote == option.option_id: 
                chart_data[i] += 1   
        i += 1
    # Parameters of the chart
    datasets_chart = [
            {
                "label": "Options by Vote",
                "borderColor": "rgba(2,29,66,1)",
                "borderWidth": 1,
                "hoverBackgroundColor": "rgba(2,29,66,0.4)",
                "hoverBorderColor": "rgba(2,29,66,1)",
                "data": chart_data,
            }
        ]
    # Data to populate the Chart.js.chart
    data = {
        "labels": labels_chart,
        "datasets": datasets_chart
    }

    return jsonify(data)



@app.route('/trip/<int:trip_id>/search')
def trip_search(trip_id):
    """Search flights"""

    trip = Trip.query.get(trip_id)

    origin_airport_codes = functions.origin_airport_codes_by_trip(trip)

    return render_template("trip_search.html", 
                           trip=trip, 
                           origin_airport_codes=origin_airport_codes,
                           option=None)



@app.route('/get-airports-to-autocomplete', methods=["GET"])
def get_airports_autocomplete():
    """Grab all airports and lat and long data to populate the autocomplete 
    drop down, ajax call"""

    # Grabs info from helper function
    airports_autocomplete_list = functions.make_airports_autocomplete()
    # import pdb
    # pdb.set_trace()

    return jsonify({"airports": airports_autocomplete_list})


@app.route('/trip/<int:trip_id>/option-delete', methods=["POST"])
def option_delete(trip_id):
    """Delete an option from the db ajax call"""

    # Get option id from from
    option_id = int(request.form.get("option-id-delete"))
    # import pdb
    # pdb.set_trace()
    # Get option by option id
    option = Option.query.get(option_id)

    # Get flights by option
    flights = functions.flights_by_option(option)

    # Get legs by flight
    for flight in flights:
        legs = functions.legs_by_flight(flight)
        # Delete all legs from db
        functions.delete_legs(legs)
    # Delte all flights from db
    functions.delete_flights(flights)

    # Delete option
    db.session.delete(option)
    db.session.commit()

    # Store message to flash confirmation of deletion
    flash("Option: " + str(option_id) + " deleted!")

    # Return back to trip details page
    return redirect('/trip/{}'.format(int(trip_id)))



@app.route('/trip/<int:trip_id>/option-update', methods=["POST"])
def option_update(trip_id):
    """Update results for an option by deleting all flights/legs associated and 
    redirecting to search page with original search parameters prepopulated"""

    trip = Trip.query.get(trip_id)
    origin_airport_codes = functions.origin_airport_codes_by_trip(trip)

    # Get option id from ajax
    option_id = int(request.form.get("option-id-update"))
    # import pdb
    # pdb.set_trace()
    # Get option by option id
    option = Option.query.get(option_id)

    # Get flights by option
    flights = functions.flights_by_option(option)

    # Get legs by flight
    for flight in flights:
        legs = functions.legs_by_flight(flight)
        # Delete all legs from db
        functions.delete_legs(legs)
    # Delte all flights from db
    functions.delete_flights(flights)

    # Return back to trip details page
    return render_template("trip_search.html", 
                       trip=trip, 
                       origin_airport_codes=origin_airport_codes,
                       option=option,
                       )



@app.route('/trip/<int:trip_id>/option-vote.json', methods=["POST"])
def option_vote(trip_id):
    """Save user's option vote for trip to db"""
    # import pdb

    # Get unicode of option id to be voted for
    option_vote_unicode = request.form.get("voted-option-id")
    # pdb.set_trace()
    print option_vote_unicode

    # Get usertrip that vote will be attached to by user and trip
    usertrip = UserTrip.query.filter_by(user_id=session["user_id"], trip_id=trip_id).first()

    # Set variable to integer of the voted for option id
    option_vote_int = int(option_vote_unicode)
    # Change option_vote for usertrip in db to the voted for option
    usertrip.option_vote = option_vote_int
    # Commit session
    db.session.commit()

    # voting_option = Option.query.get(option_vote_int)
    # pdb.set_trace()
    return json.dumps(option_vote_int)



# @app.route('/trip/<int:trip_id>/share')
# def trip_share(trip_id):
#     """Share trip with other users"""

#     return render_template("trip_share.html", trip_id=trip_id)



################################################################################

## QPX query AJAX routes ##

################################################################################    



@app.route('/trip/<int:trip_id>/search.json', methods=["POST"])
def trip_option_info(trip_id):
    """Get Option info and save to db, ajax call"""

    # Initializes empty dictionary to add option info to
    option_info = {}
    # Get destination, departure_date, return_date from form and add to option_info
    option_info["destination"] = ((request.form.get("destination")).upper())[:3]
    option_info["depart_date"] = request.form.get("depart-date")
    option_info["return_date"] = request.form.get("return-date")
    # Add trip_id to option_info
    option_info["trip_id"] = trip_id

    # Add option to db and return option object
    option = functions.add_option_to_db(option_info)

    option_id_to_use = {"option_id": option.option_id}

    # option = option.to_dict()

    return jsonify(option_id_to_use)



@app.route('/trip/<int:trip_id>/results.json', methods=["POST"])
def trip_results(trip_id):
    """Search flights results, ajax call"""

    # Get trip from trip_id
    trip = Trip.query.get(trip_id)

    # Initializes empty dictionary to add option info to
    option_info = {}
    # Get destination, departure_date, return_date from form and add to option_info
    option_info["destination"] = ((request.form.get("destination")).upper())[:3]
    option_info["depart_date"] = request.form.get("depart-date")
    option_info["return_date"] = request.form.get("return-date")
    # Add trip_id to option_info
    option_info["trip_id"] = trip_id

    # Get origin airport codes for trip
    origin_airport_code = (request.form.get("origin-airport-code")).upper()

    # Initialize empty results list to add QPX query restuls to
    # python_results = []

    # Get parameter variables for QPX search from input option and origin_airport_codes
    params = functions.get_params(origin_airport_code, option_info)
    # Get the parameter string from the parameter variables
    parameter = functions.parameter_by_params(params)
    # Make request to QPX
    flight_request = functions.query_QPX(parameter)
    # import pdb
    # pdb.set_trace()
    # Read results from QPX into python
    python_result = functions.QPX_results(flight_request)
    #add python_result to python_results
    # python_results.append(python_result)

    # change this later to get by option_info!!!!
    option_id = request.form.get("option-id")
    option = Option.query.get(option_id)

    # Parse python results to add flights and legs to db and to get data to render on 
    # results page
    flights = functions.parse_results(python_result, option)

    result = {"flights" : flights}
    # import pdb
    # pdb.set_trace()
    # Trip results page with all the data necessary for tables
    return jsonify(result)



@app.route('/origins-for-map')
def origins_for_map():
    """Grab all origin airport lat longs to put markers on the Google Map"""

    # Get trip name
    trip_name = request.args.get("trip")
    # Get trip
    trip = Trip.query.filter_by(trip_name=trip_name).first()
    users = []

    # import pdb
    # pdb.set_trace()
    userstrips = trip.usertrips
    for usertrip in userstrips:
        user_id = (usertrip.user_id)
        user = User.query.get(user_id)
        users.append(user)

    # Get lat long lists for each marker
    latlongs = []
    for user in users:
        origin_airport = user.origin_airport
        latlongs.append((origin_airport.airport_lat, origin_airport.airport_long))



    return jsonify({"latlongs": latlongs})



@app.route('/destinations-for-map')
def destinations_for_map():
    """Grab all origin airport lat longs to put markers on the Google Map"""

    # Get trip name
    trip_name = request.args.get("trip")
    trip = Trip.query.filter_by(trip_name=trip_name).first()

    # Get lat long lists for each marker
    latlongs = []
    options = trip.options
    for option in options:
        latlongs.append((option.destination_airport.airport_lat, option.destination_airport.airport_long))

    return jsonify({"latlongs": latlongs})



# @app.route('/untitled')
# def get_untitled():

#     return render_template("untitled.html")



################################################################################

## End routes ##

################################################################################



if __name__ == "__main__":
    # Debug to be turned off for production
    app.debug = True

    connect_to_db(app)

    # Use DebugToolbar
    # DebugToolbarExtension(app)

    # Runs app
    app.run()
