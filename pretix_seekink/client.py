import hashlib
import re
import requests
from django.core.cache import cache


class SeekInkClient(object):
    def __init__(self, server, username, password):
        self.server = f"{server}/cloud/prod-api/api/v1"
        self.username = username
        self.password = password

    def refresh_token(self):
        req = requests.post(
            f"{self.server}/user/login",
            json={"username": self.username, "password": self.password},
        )

        data = req.json()
        if data["code"] == 200:
            cache_key_hash = hashlib.sha256(
                f"{self.server}{self.username}{self.password}".encode()
            ).hexdigest()
            cache.set(f"pretix_seekink_token_{cache_key_hash}", data["data"])
            return data["data"]

        return None

    def access_token(self):
        cache_key_hash = hashlib.sha256(
            f"{self.server}{self.username}{self.password}".encode()
        ).hexdigest()
        token = cache.get(f"pretix_seekink_token_{cache_key_hash}")

        if not token:
            token = self.refresh_token()

        return token

    def default_headers(self):
        access_token = self.access_token()
        if not access_token:
            raise PermissionError("No access token")

        return {"Authorization": f"Bearer {self.access_token()}"}

    def clean_mac(self, mac):
        mac = re.sub("[^a-fA-F0-9]", "", mac).upper()
        if len(mac) != 12:
            return False

        return mac

    def send_picture(self, mac, dithering_mode, image):
        mac = self.clean_mac(mac)

        if mac:
            req = requests.post(
                f"{self.server}/label/brushPic",
                headers=self.default_headers(),
                files={
                    "file": ("badge.png", image),
                    "labelMac": (None, mac),
                    "ditheringMode": (None, dithering_mode),
                },
            )

            return req.json()
