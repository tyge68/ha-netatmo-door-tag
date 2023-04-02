# USAGE
Copy the files in your config/custom_components/netatmo_door_tag.

# GENERATE TOKEN

Create an app on your Netatmo [developer](https://dev.netatmo.com/apps/) portal, then create an app token with 
permissions to read camera etc.. you can [test](https://dev.netatmo.com/apidocumentation/control#homesdata) your token in the portal to see if it has enough permissions to find the Netatmo Door Tags.


Store the token and refresh token in the file `config/.storage/netatmo_auth.json` of your home assistant.

File should look like this:

```
{
    "token": "<generated access token>",
    "refresh_token": "<generated refresh token>",
    "client_id": "<client id of your app>",
    "client_secret": "<client secret of your app>",
    "created": 1680416436.495623,
    "expires_in": 10800
}
```

# CONFIGURATION

Add the following lines to your configuration yaml

```
netatmo_door_tag:
binary_sensor:
- platform: netatmo_door_tag
  auth_file: ".storage/netatmo_auth.json"
  home_id: <your home id which you can find in Netatmo Developer Portal>
```

NOTE: There are probably better ways to implement it, feel free to try it.
