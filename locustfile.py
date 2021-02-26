import random

from locust import HttpUser, between, task


class WebsiteUser(HttpUser):
    wait_time = between(3, 10)

    def on_start(self):

        self.club = "Simply Lift"
        self.competitions = ["Spring Festival 2050", "Fall Classic 2050"]

        # Visit Home page
        self.client.get("/")

        # Login
        self.client.post("/showSummary", {"email": "john@simplylift.co"})

    def on_stop(self):
        self.client.get("/logout")

    @task(2)
    def book(self):
        for competition in self.competitions:
            self.client.get(f"/book/{competition}/{self.club}", name="/book")

    @task(1)
    def purchasePlaces(self):
        competition = random.choices(self.competitions)
        # for competition in self.competitions:
        self.client.post(
            "/purchasePlaces",
            {"places": 1, "club": self.club, "competition": competition},
            name="/purchasePlaces",
        )
