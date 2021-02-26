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
    """ save club's booking to competitions in a dictionnay """

    if club not in booking:
        booking[club] = {}

    if competition not in booking[club]:
        booking[club][competition] = 0

    booking[club][competition] += places


def getBooking(club, competition):
    """ return the current club's booking number for a given competition """

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
    pass


class PlaceValueError(Exception):
    pass


class EventDateError(Exception):
    pass


# ----- ROUTES -----


@app.route("/")
def index():
    return render_template("index.html", clubs=clubs)


@app.route("/showSummary", methods=["POST"])
def showSummary():
    try:
        club = [club for club in clubs if club["email"] == request.form["email"]][0]
        return showSummaryDisplay(club)
    except IndexError:
        flash("The provided email is invalid")
        return render_template("index.html", clubs=clubs), 404


def showSummaryDisplay(club, status_code=200):

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

    return showSummaryDisplay(foundClub, status_code)


@app.route("/purchasePlaces", methods=["POST"])
def purchasePlaces():

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


# TODO: Add route for points display


@app.route("/logout")
def logout():
    return redirect(url_for("index"))
