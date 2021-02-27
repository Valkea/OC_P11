# -*- coding: utf-8 -*-

import datetime
import json

from flask import Flask, render_template, request, redirect, flash, url_for

# ----- INIT APPLICATION -----

app = Flask(__name__)
app.secret_key = "something_special"


# ----- HELPER FUNCTIONS -----


def formatDate(date_str):
    """ Return a datetime object from a Y-M-d H:M:S date string """
    return datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")


# ----- DATA HANDLING -----

COST_PER_PLACE = 3
MAX_PLACES_PER_CLUB = 12

# -- load jsons


def loadClubs():
    with open("clubs.json") as c:
        listOfClubs = json.load(c)["clubs"]
        return listOfClubs


def loadCompetitions():
    with open("competitions.json") as comps:
        listOfCompetitions = json.load(comps)["competitions"]
        return listOfCompetitions


# -- save bookings in dict


def addBooking(club, competition, places):
    """Save club's booking to competitions in a dictionnay

    Parameters
    ----------
    club : str
        The name of the club booking the places
    competition : str
        The name of the competition for which places are booked
    places : int
        The number of places to book
    """

    if club not in booking:
        booking[club] = {}

    if competition not in booking[club]:
        booking[club][competition] = 0

    booking[club][competition] += places


def getBooking(club, competition):
    """Return the current club's booking number for a given competition

    Parameters
    ----------
    club : str
        The name of the club
    competition : str
        The name of the competition
    """

    if club not in booking:
        return 0
    if competition not in booking[club]:
        return 0

    return booking[club][competition]


# -- define globals

competitions = loadCompetitions()
clubs = loadClubs()
booking = {}


# ----- EXCEPTIONS -----


class PointValueError(Exception):
    """ Returned when there is a problem with the clubs' points """

    pass


class PlaceValueError(Exception):
    """ Returned when there is a problem with the competitions' places """

    pass


class EventDateError(Exception):
    """ Returned when there is an error with competition dates """

    pass


# ----- ROUTES -----


@app.route("/")
def index():
    """This route displays the landing page with the authentificatio form """

    return render_template("index.html", clubs=clubs)


@app.route("/showSummary", methods=["POST"])
def showSummary():
    """This route validates the provided authentification information.

    POST Parameters
    ----------
    email : str
        The email to search in the club 'DB'
    """
    try:
        club = [club for club in clubs if club["email"] == request.form["email"]][0]
        return showSummaryDisplay(club)
    except IndexError:
        flash("The provided email is invalid")
        return render_template("index.html", clubs=clubs), 404


def showSummaryDisplay(club, status_code=200):
    """Gather informations for the main page (welcome.html) and render it.

        This main page is called from various route with various HTTP status_code.
        ( showSummaryDisplay with HTTP 200 )
        ( book/<compet>/<club> with HTTP 200 / 400 / 404 )
        ( purchasePlaces with HTTP 200 / 400 / 404 )

        This function will collect past & incoming competion informations along
        with the current club informations and all the other clubs.


    Parameters
    ----------
    club : dict
        The currently 'authentified' club
    status_code : int
        The HTTP status_code to return with the body html
    """

    now = datetime.datetime.now()

    past_competitions = [
        compet for compet in competitions if formatDate(compet["date"]) <= now
    ]

    next_competitions = [
        compet for compet in competitions if formatDate(compet["date"]) > now
    ]

    return (
        render_template(
            "welcome.html",
            club=club,
            past_competitions=past_competitions,
            next_competitions=next_competitions,
            clubs=clubs,
        ),
        status_code,
    )


@app.route("/book/<competition>/<club>")
def book(competition, club):
    """This route displays the given competition informations along with a purchase form.

    It will display the main page (showSummaryDisplay) instead, if something goes wrong.

    Parameters
    ----------
    club : str
        The name of the currently 'authentified' club
        # NOTE don't put the name of the identified club in the URL !
    competition : str
        The name of the competition to display
    """

    # Is the provided club valid ?
    try:
        foundClub = [c for c in clubs if c["name"] == club][0]
    except IndexError:
        flash("The provided club is invalid")
        return render_template("index.html", clubs=clubs), 404

    # Is the provided competition valid ?
    # Is the competition date valid ?
    try:
        foundCompetition = [c for c in competitions if c["name"] == competition][0]

        now = datetime.datetime.now()

        if formatDate(foundCompetition["date"]) > now:

            booked = getBooking(foundClub["name"], foundCompetition["name"])

            return (
                render_template(
                    "booking.html",
                    club=foundClub,
                    competition=foundCompetition,
                    booked=booked,
                    maxplaces=min(
                        int(foundClub["points"]) // COST_PER_PLACE,
                        MAX_PLACES_PER_CLUB - booked,
                    ),
                ),
                200,
            )
        else:
            raise EventDateError("The booking page for a past competition is closed")

    except IndexError:
        flash("The provided competition is invalid")
        status_code = 404

    except EventDateError as error_msg:
        flash(error_msg)
        status_code = 400

    # return redirect(url_for("showSummary"), status_code)
    return showSummaryDisplay(foundClub, status_code)


@app.route("/purchasePlaces", methods=["POST"])
def purchasePlaces():
    """This route validates the purchase made from the competition booking page.

    Once done, it will display the main page (showSummaryDisplay) again.

    POST Parameters
    ----------
    club : str (hidden)
        The name of the currently 'authentified' club
    competition : str (hidden)
        The name of the competition on which to book places
    places : int
        The number of places to book for the given club in the given competition
        if all the validation steps are validated.
    """

    # Is the provided club valid ?
    try:
        club = [c for c in clubs if c["name"] == request.form["club"]][0]
    except IndexError:
        flash("The provided club is invalid")
        return render_template("index.html", clubs=clubs), 404

    # Is the provided competition valid ?
    # Also check the various possible input errors
    try:
        competition = [
            c for c in competitions if c["name"] == request.form["competition"]
        ][0]

        placesRequired = int(request.form["places"])
        club_points = int(club["points"])
        competition_places = int(competition["numberOfPlaces"])

        if placesRequired < 1:

            raise PointValueError("Something went wrong-please try again")

        elif club_points < placesRequired * COST_PER_PLACE:

            raise PointValueError("You don't have enough points available")

        elif competition_places < placesRequired:

            raise PlaceValueError("You can't book more places than available")

        elif (
            placesRequired + getBooking(club["name"], competition["name"])
            > MAX_PLACES_PER_CLUB
        ):

            raise PlaceValueError(
                f"You can't book more than {MAX_PLACES_PER_CLUB} places per competition"
            )

        else:

            club["points"] = club_points - (placesRequired * COST_PER_PLACE)
            competition["numberOfPlaces"] = competition_places - placesRequired

            addBooking(club["name"], competition["name"], placesRequired)

            flash("Great-booking complete!")
            status_code = 200

    except IndexError:
        flash("The provided competition is invalid")
        status_code = 404

    except (PointValueError, PlaceValueError) as error_msg:
        flash(error_msg)
        status_code = 400

    return showSummaryDisplay(club, status_code)
    # return redirect(url_for("showSummary"), status_code)


@app.route("/logout")
def logout():
    """This route redirect to the landing page

    # NOTE : this page should actually logout users...
    """
    return redirect(url_for("index"))
