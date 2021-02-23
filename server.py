# -*- coding: utf-8 -*-

import json
from flask import Flask, render_template, request, redirect, flash, url_for


def loadClubs():
    with open("clubs.json") as c:
        listOfClubs = json.load(c)["clubs"]
        return listOfClubs


def loadCompetitions():
    with open("competitions.json") as comps:
        listOfCompetitions = json.load(comps)["competitions"]
        return listOfCompetitions


app = Flask(__name__)
app.secret_key = "something_special"

competitions = loadCompetitions()
clubs = loadClubs()
booking = {}


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


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/showSummary", methods=["POST"])
def showSummary():
    try:
        club = [club for club in clubs if club["email"] == request.form["email"]][0]
        return render_template("welcome.html", club=club, competitions=competitions)
    except IndexError:
        flash("The provided email is invalid")
        return render_template("index.html"), 404


@app.route("/book/<competition>/<club>")
def book(competition, club):
    foundClub = [c for c in clubs if c["name"] == club][0]
    foundCompetition = [c for c in competitions if c["name"] == competition][0]
    if foundClub and foundCompetition:
        return render_template(
            "booking.html", club=foundClub, competition=foundCompetition
        )
    else:
        flash("Something went wrong-please try again")
        return render_template("welcome.html", club=club, competitions=competitions)


@app.route("/purchasePlaces", methods=["POST"])
def purchasePlaces():
    competition = [c for c in competitions if c["name"] == request.form["competition"]][
        0
    ]
    club = [c for c in clubs if c["name"] == request.form["club"]][0]

    placesRequired = int(request.form["places"])
    club_points = int(club["points"])
    competition_places = int(competition["numberOfPlaces"])
    place_cost = 1

    if placesRequired < 1:

        flash("Something went wrong-please try again")
        status_code = 400

    elif club_points < placesRequired * place_cost:

        flash("You don't have enough points available")
        status_code = 400

    elif competition_places < placesRequired:

        flash("You can't book more places than available")
        status_code = 400

    elif placesRequired + getBooking(club["name"], competition["name"]) > 12:

        flash("You can't book more than 12 places per competition")
        status_code = 400

    else:

        club["points"] = club_points - (placesRequired * place_cost)
        competition["numberOfPlaces"] = competition_places - placesRequired

        addBooking(club["name"], competition["name"], placesRequired)

        flash("Great-booking complete!")
        status_code = 200

    return (
        render_template("welcome.html", club=club, competitions=competitions),
        status_code,
    )


# TODO: Add route for points display


@app.route("/logout")
def logout():
    return redirect(url_for("index"))
