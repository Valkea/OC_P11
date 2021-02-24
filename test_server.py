# coding : utf-8

import datetime

import server


class TestServer:
    @classmethod
    def setup_class(cls):
        cls.app = server.app.test_client()

        cls.competitions = server.competitions
        cls.clubs = server.clubs

        # cls.ref_clubs = [
        #     {"name": "Simply Lift", "email": "john@simplylift.co", "points": "13"},
        #     {"name": "Iron Temple", "email": "admin@irontemple.com", "points": "4"},
        #     {"name": "She Lifts", "email": "kate@shelifts.co.uk", "points": "12"},
        # ]
        # cls.ref_competitions = [
        #     {
        #         "name": "Spring Festival",
        #         "date": "2020-03-27 10:00:00",
        #         "numberOfPlaces": "25",
        #     },
        #     {
        #         "name": "Fall Classic",
        #         "date": "2020-10-22 13:30:00",
        #         "numberOfPlaces": "13",
        #     },
        # ]

    def setup_method(self, method):
        print("RESET")
        server.competitions = server.loadCompetitions()
        server.clubs = server.loadClubs()
        server.booking = {}

    # --- HELPERS --- #

    def login(self, email):
        return self.app.post("/showSummary", data=dict(email=email))

    def logout(self):
        return self.app.get("/logout", follow_redirects=True)

    # --- TESTS LOGIN / LOGOUT --- #

    def test_happy_login_logout(self):
        """ Check if right email login + login is correctly handled """

        rv = self.login("john@simplylift.co")
        assert rv.status_code in [200]
        assert b"Logout" in rv.data

        rv = self.logout()
        assert rv.status_code in [200]
        assert b"Please enter your secretary email to continue" in rv.data

    def test_sad_login_wrong_email(self):
        """ Check if wrong email is correctly handled """

        rv = self.login("wrong@email.com")
        assert rv.status_code in [404]
        assert b"The provided email is invalid" in rv.data

    def test_sad_login_empty_email(self):
        """ Check if an empty email field is correctly handled """

        rv = self.login("")
        assert rv.status_code in [404]
        assert b"The provided email is invalid" in rv.data

    # --- TESTS BOOKING --- #

    def test_happy_booking(self):
        """ Display the booking page for an existing competition with an existing club """

        now = datetime.datetime.now()

        for club in self.clubs:
            for competition in self.competitions:
                rv = self.app.get(f"/book/{competition['name']}/{club['name']}")

                print(rv.data, rv.status_code, "\n")

                if server.formatDate(competition["date"]) <= now:
                    continue

                assert rv.status_code in [200]
                assert (
                    str.encode(f"Places available: {competition['numberOfPlaces']}")
                    in rv.data
                )

    def test_sad_booking_wrong_compet(self):
        """ Display the booking page for an existing club with a non existing competition """

        for competition in self.competitions:
            rv = self.app.get(f"/book/wrong_compet_name/{self.clubs[0]['name']}")

            assert rv.status_code in [404]
            assert b"Something went wrong-please try again" in rv.data

    def test_sad_booking_wrong_club(self):
        """ Display the booking page for an existing competition with a non existing club """

        for competition in self.competitions:
            rv = self.app.get(f"/book/{competition['name']}/wrong_club_name")

            assert rv.status_code in [404]
            assert b"Something went wrong-please try again" in rv.data

    # --- TESTS PURCHASE PLACES --- #

    def test_happy_purchasePlaces_once(self):
        """ Book less places than club points or competitions available places """

        points = int(self.clubs[0]["points"])
        booked = 0
        num_places = 1
        for competition in self.competitions:
            places = int(competition["numberOfPlaces"])
            rv = self.app.post(
                "/purchasePlaces",
                data={
                    "places": num_places,
                    "club": self.clubs[0]["name"],
                    "competition": competition["name"],
                },
            )

            booked += num_places

            print(rv.data, rv.status_code)

            assert rv.status_code in [200]
            assert str.encode(f"Number of Places: {places-num_places}") in rv.data
            assert str.encode(f"Points available: {points-booked}") in rv.data

    def test_sad_purchasePlaces_negative(self):
        """ Book a negative number of places """

        num_places = -1
        for competition in self.competitions:
            rv = self.app.post(
                "/purchasePlaces",
                data={
                    "places": num_places,
                    "club": self.clubs[0]["name"],
                    "competition": competition["name"],
                },
            )

            assert rv.status_code in [400]
            assert b"Something went wrong-please try again" in rv.data

    def test_sad_purchasePlaces_zero(self):
        """ Book a negative number of places """

        num_places = 0
        for competition in self.competitions:
            rv = self.app.post(
                "/purchasePlaces",
                data={
                    "places": num_places,
                    "club": self.clubs[0]["name"],
                    "competition": competition["name"],
                },
            )

            assert rv.status_code in [400]
            assert b"Something went wrong-please try again" in rv.data

    def test_sad_purchasePlaces_12_places_max__all_in_one(self):
        """ Book more than 12 places > forbidden """

        print("INIT:", self.competitions, self.clubs)

        points = int(self.clubs[0]["points"])
        slots = int(self.competitions[0]["numberOfPlaces"])

        rv = self.app.post(
            "/purchasePlaces",
            data={
                "places": 13,
                "club": self.clubs[0]["name"],
                "competition": self.competitions[0]["name"],
            },
        )

        print(rv.data, rv.status_code)

        assert rv.status_code in [400]
        assert str.encode(f"Number of Places: {slots}") in rv.data
        assert str.encode(f"Points available: {points}") in rv.data
        assert b"You can&#39;t book more than 12 places per competition" in rv.data

    def test_sad_purchasePlaces_12_places_max__step_by_step(self):
        """ Book more than 12 places > forbidden """

        print("INIT:", self.competitions, self.clubs)

        points = int(self.clubs[0]["points"])
        slots = int(self.competitions[0]["numberOfPlaces"])
        booked = 0

        num_actions = 12 + 1

        for i in range(1, num_actions + 1):
            rv = self.app.post(
                "/purchasePlaces",
                data={
                    "places": 1,
                    "club": self.clubs[0]["name"],
                    "competition": self.competitions[0]["name"],
                },
            )

            booked += 1
            print(i, "\n", rv.data, rv.status_code, "\n", server.booking)

            if i < num_actions - 1:
                assert rv.status_code in [200]
                assert str.encode(f"Number of Places: {slots-booked}") in rv.data
                assert str.encode(f"Points available: {points-booked}") in rv.data

        assert rv.status_code in [400]
        assert b"You can&#39;t book more than 12 places per competition" in rv.data

    def test_happy_purchasePlaces_all_club_points(self):
        """ Use all points of a club """

        points = int(self.clubs[1]["points"])
        slots = int(self.competitions[0]["numberOfPlaces"])
        booked = 0

        for i in range(points + 1):
            rv = self.app.post(
                "/purchasePlaces",
                data={
                    "places": 1,
                    "club": self.clubs[1]["name"],
                    "competition": self.competitions[0]["name"],
                },
            )

            booked += 1

            print(rv.data, rv.status_code)

            if i < points:
                assert rv.status_code in [200]
                assert str.encode(f"Number of Places: {slots-booked}") in rv.data
                assert str.encode(f"Points available: {points-booked}") in rv.data

        assert rv.status_code in [400]
        assert b"Points available: 0" in rv.data
        assert b"You don&#39;t have enough points available" in rv.data

    def test_happy_purchasePlaces_all_compet_places(self):
        """ Book all places of a competition """

        test_name = "test compet"
        test_num = 15

        server.competitions.append(
            {
                "name": test_name,
                "date": "2020-10-22 13:30:00",
                "numberOfPlaces": test_num,
            }
        )
        self.competitions = server.competitions

        print("INIT:", self.competitions, self.clubs, server.booking)

        slots = test_num
        booked = 0

        for club in self.clubs:
            if int(club["points"]) <= 0:
                continue

            points = min(int(club["points"]), 12)

            rv = self.app.post(
                "/purchasePlaces",
                data={
                    "places": points,
                    "club": club["name"],
                    "competition": test_name,
                },
            )

            booked += points

            print(rv.data, rv.status_code, "\n", server.booking)

            if booked <= slots:
                assert rv.status_code in [200]
                assert str.encode(f"Number of Places: {slots-booked}") in rv.data

        assert rv.status_code in [400]
        assert b"You can&#39;t book more places than available" in rv.data

    def test_sad_purchasePlaces_more_than_compet(self):
        """ Book more places than available in the competition """

        test_name = "test compet"
        test_num = 5

        server.competitions.append(
            {
                "name": test_name,
                "date": "2020-10-22 13:30:00",
                "numberOfPlaces": test_num,
            }
        )
        self.competitions = server.competitions

        print("INIT:", self.competitions, self.clubs)

        num_booked = 5 + 1
        rv = self.app.post(
            "/purchasePlaces",
            data={
                "places": num_booked,
                "club": self.clubs[0]["name"],
                "competition": test_name,
            },
        )

        print(rv.data, rv.status_code)

        assert rv.status_code in [400]
        assert b"You can&#39;t book more places than available" in rv.data

    def test_sad_purchasePlaces_more_than_club(self):
        """ Book more places than the number of points available in the club """

        for club in self.clubs:
            for competition in self.competitions:
                num_booked = int(club["points"]) + 1
                rv = self.app.post(
                    "/purchasePlaces",
                    data={
                        "places": num_booked,
                        "club": club["name"],
                        "competition": competition["name"],
                    },
                )

                assert rv.status_code in [400]
                assert b"You don&#39;t have enough points available" in rv.data

    def test_sad_purchasePlaces_wrong_compet(self):
        """ Book places with an existing club and a non existing competition """

        rv = self.app.post(
            "/purchasePlaces",
            data={
                "places": 1,
                "club": self.clubs[0]["name"],
                "competition": "fake_competition_name",
            },
        )

        assert rv.status_code in [404]
        assert b"Something went wrong-please try again" in rv.data

    def test_sad_purchasePlaces_wrong_club(self):
        """ Book places with an existing competition and a non existing club """

        rv = self.app.post(
            "/purchasePlaces",
            data={
                "places": 1,
                "club": "fake_club_name",
                "competition": self.competitions[0]["name"],
            },
        )

        assert rv.status_code in [404]
        assert b"Something went wrong-please try again" in rv.data

    # --- TESTS PAST COMPETITIONS --- #

    def test_happy_showSummary_with_future_events(self):
        """ Show summary with both past & incoming events """

        # incoming_date = datetime.datetime.now() + datetime.timedelta(days=20, hours=3)
        # test_incoming_date = incoming_date.strftime("%Y-%m-%d %H:%M:%S")
        # test_name = "test compet"
        # test_num = 5

        # server.competitions.append(
        #     {
        #         "name": test_name,
        #         "date": test_incoming_date,
        #         "numberOfPlaces": test_num,
        #     }
        # )
        # self.competitions = server.competitions

        # NOTE replaced the above code with 2 new incoming events in the json file

        rv = self.login("john@simplylift.co")
        print(rv.data, rv.status_code)

        assert rv.status_code in [200]
        assert b"Book Places" in rv.data
        assert rv.data.count(b"Finished") == 2
        assert rv.data.count(b"Book Places") == 2

    def test_sad_booking_past_compet(self):
        """ Must redirect to summary if someone directly write the booking url of a past competition """

        rv = self.app.get(
            f"/book/{self.competitions[0]['name']}/{self.clubs[0]['name']}"
        )
        assert rv.status_code in [400]
        assert b"Something went wrong-please try again" in rv.data
        assert b"Welcome" in rv.data
