import hashlib
import re
import requests
from django.core.cache import cache


class OpenEPaperLinkClient(object):
    def __init__(self, server):
        self.server = server

    def clean_mac(self, mac):
        mac = re.sub("[^a-fA-F0-9]", "", mac).upper()
        if len(mac) != 12 and len(mac) != 16:
            return False

        return mac

    def send_picture(self, mac, dithering_mode, image):
        mac = self.clean_mac(mac)

        if mac:
            req = requests.post(
                f"{self.server}/imgupload",
                data={
                    "mac": mac,
                    "dither": dithering_mode,
                },
                files={
                    "file": ("badge.jpg", image),
                },
            )

            return req.json()
