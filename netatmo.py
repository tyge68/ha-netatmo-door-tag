"""Netatmo Door Tag SDK"""
# import urllib library
from dataclasses import dataclass
from dataclasses_json import dataclass_json
import aiofiles
import requests
import functools
import time
import logging
from pprint import pformat

#
_LOGGER = logging.getLogger(__name__)


@dataclass_json
@dataclass
class AuthInfo:
    """Object representation for Authentication Purpose."""

    token: str
    refresh_token: str
    client_id: str
    client_secret: str
    created: float
    expires_in: float


class Authenticator:
    """Helper object to authenticate Netatmo API"""

    def __init__(self, hass, auth_file):
        self.info = AuthInfo("", "", "", "", 0, 0)
        self.hass = hass
        self._auth_file = auth_file

    async def init(self):
        """Initialize auth token"""
        await self.__reload_token()
        if self.__is_expired():
            _LOGGER.info("Refreshing token as it expired")
            await self.__refresh_token()

    def get_bearer_token(self):
        """return the Authentication string to be used by request"""
        return f"Bearer {self.info.token}"

    def __is_expired(self):
        """return true if the current info expired"""
        current_time = time.time()
        delta_time = current_time - self.info.created
        return delta_time > self.info.expires_in

    async def __persist_token(self):
        """persist the current info on local storage"""
        async with aiofiles.open(self._auth_file, "w", encoding="UTF-8") as outfile:
            await outfile.write(self.info.to_json())

    async def __reload_token(self):
        """read persisted info from local storage"""
        async with aiofiles.open(self._auth_file, "r", encoding="UTF-8") as infile:
            data = await infile.read()
            _LOGGER.info(data)
            self.info = AuthInfo.from_json(data)
            _LOGGER.info("Auth info reloaded")

    async def __refresh_token(self):
        """refresh the token using refresh_token info"""
        info = self.info
        # store the response of URL
        func = functools.partial(
            requests.post,
            "https://api.netatmo.com/oauth2/token",
            headers={
                "accept": "application/json",
            },
            data={
                "grant_type": "refresh_token",
                "refresh_token": info.refresh_token,
                "client_id": info.client_id,
                "client_secret": info.client_secret,
            },
        )
        response = await self.hass.async_add_executor_job(func)

        data_json = response.json()
        if response.status_code == 200:
            info.token = data_json["access_token"]
            info.refresh_token = data_json["refresh_token"]
            info.created = time.time()
            info.expires_in = data_json["expires_in"]
            _LOGGER.info("Token refreshed")
            await self.__persist_token()
        else:
            _LOGGER.error(
                "Cannot update token error %s: %s",
                {response.status_code},
                {response.reason},
            )


class HomesData:
    """Represent Netatmo Homes Data"""

    def __init__(self, authenticator, home_id) -> None:
        self.door_tags_map = {}
        self.home_id = home_id
        self.authenticator = authenticator
        self.hass = authenticator.hass

    def name(self, mod_id: str) -> str:
        """Return the name of a given module id"""
        return self.door_tags_map[mod_id]

    async def init(self) -> None:
        """Initialize the Home Data"""
        # store the URL in url as
        # parameter for urlopen
        func = functools.partial(
            requests.get,
            f"https://api.netatmo.com/api/homesdata?home_id={self.home_id}",
            headers={
                "accept": "application/json",
                "Authorization": self.authenticator.get_bearer_token(),
            },
        )
        response = await self.hass.async_add_executor_job(func)

        data_json = response.json()
        # print the json response
        if "body" in data_json:
            for mod in data_json["body"]["homes"][0]["modules"]:
                if mod["type"] == "NACamDoorTag":
                    mod_id = mod["id"]
                    self.door_tags_map[mod_id] = mod["name"]
        else:
            _LOGGER.error("Cannot find door tags due to %s", pformat(data_json))


class HomeStatus:
    """Represent Netatmo Home Status"""

    def __init__(self, authenticator, home_id, homes_data: HomesData) -> None:
        self.door_tags = []
        self.home_id = home_id
        self.authenticator = authenticator
        self.homes_data = homes_data
        self.hass = authenticator.hass

    async def init(self) -> None:
        """Initialize Home Status"""
        # store the URL in url as
        func = functools.partial(
            requests.get,
            f"https://api.netatmo.com/api/homestatus?home_id={self.home_id}",
            headers={
                "accept": "application/json",
                "Authorization": self.authenticator.get_bearer_token(),
            },
        )
        response = await self.hass.async_add_executor_job(func)
        data_json = response.json()
        # print the json response
        if data_json["body"]:
            for mod in data_json["body"]["home"]["modules"]:
                if mod["type"] == "NACamDoorTag":
                    mod_id = mod["id"]
                    name = self.homes_data.name(mod_id)
                    self.door_tags.append(
                        {
                            "id": mod_id,
                            "status": mod["status"],
                            "name": name,
                        }
                    )
