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

        for club in self.clubs:
            for competition in self.competitions:
                rv = self.app.get(f"/book/{competition['name']}/{club['name']}")
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
        booked = 1
        for competition in self.competitions:
            places = int(competition["numberOfPlaces"])
            rv = self.app.post(
                "/purchasePlaces",
                data={
                    "places": booked,
                    "club": self.clubs[0]["name"],
                    "competition": competition["name"],
                },
            )

            assert rv.status_code in [200]
            assert str.encode(f"Number of Places: {places-booked}") in rv.data
            assert str.encode(f"Points available: {points-booked}") in rv.data

    def test_happy_purchasePlaces_all_club_points(self):
        """ Use all points of a club """

        points = int(self.clubs[0]["points"])
        slots = int(self.competitions[0]["numberOfPlaces"])
        booked = 0

        for i in range(points):
            rv = self.app.post(
                "/purchasePlaces",
                data={
                    "places": 1,
                    "club": self.clubs[0]["name"],
                    "competition": self.competitions[0]["name"],
                },
            )

            booked += 1

            if i < points:
                assert rv.status_code in [200]
                assert str.encode(f"Number of Places: {slots-booked}") in rv.data
                assert str.encode(f"Points available: {points-booked}") in rv.data

        assert rv.status_code in [400]
        assert b"You don't have enough points available" in rv.data

    def test_happy_purchasePlaces_all_compet_places(self):
        """ Book all places of a competition """

        slots = int(self.competitions[0]["numberOfPlaces"])  # 25
        booked = 0

        for club in self.clubs:
            if int(club["points"]) <= 0:
                continue

            points = int(club["points"])

            rv = self.app.post(
                "/purchasePlaces",
                data={
                    "places": points,
                    "club": club["name"],
                    "competition": self.competitions[0]["name"],
                },
            )

            booked += points

            if booked <= slots:
                assert rv.status_code in [200]
                assert str.encode(f"Number of Places: {slots-booked}") in rv.data
                assert str.encode(f"Points available: {points-booked}") in rv.data

        assert rv.status_code in [400]
        assert b"You don't have enough points available" in rv.data

    def test_sad_purchasePlaces_more_than_compet(self):
        """ Book more places than available in the competition """

        for competition in self.competitions:
            num_booked = int(competition["numberOfPlaces"]) + 1
            rv = self.app.post(
                "/purchasePlaces",
                data={
                    "places": num_booked,
                    "club": self.clubs[0]["name"],
                    "competition": competition["name"],
                },
            )

            assert rv.status_code in [400]
            assert b"You can't book more places than available" in rv.data

    def test_sad_purchasePlaces_more_than_club(self):
        """ Book more places than the number of points available in th club """

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
                assert b"You don't have enough points available" in rv.data

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
