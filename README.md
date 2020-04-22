[![Donate](https://www.paypalobjects.com/en_US/i/btn/btn_donate_LG.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=babylonstudio%40gmail%2ecom&lc=CA&item_name=coryo%20Plex%20Channels&no_note=0&currency_code=USD&bn=PP%2dDonationsBF%3abtn_donate_LG%2egif%3aNonHostedGuest) btc: 1JJD5i4jL5qmbMKCy1sNVGgQzx1Jh37rFH

Installation
============

Put `TwitchMod.bundle` into `Plex Media Server/Plug-ins`

Preferences
===========

General Preferences
-------------------

 * **Username:** The username to get followed channels for. This channel does not need your password since Twitch lets you pull this data without authenticating.
 * **Order Following By:** The ordering of the followed channels page. Ordering by views will put all online channels first.
 * **Favourite Games:** A comma separated list of games titles. Use this if you like viewing games with small amounts of viewers. Game titles dont have to be exact matches. ex: `diablo, starcraft`.
 * **Title Layout:** What info is shown in the stream title. If you don't like any of the options, please suggest some.
 * **Title Layout (game lists):** A separate title layout for lists where you know the game title going in.
 * **Hide Offline Channels:** Hide offline channels in the 'followed channels' menu.
 * **Access Token (optional):** OAuth token to allow watching subscriber-only VODs.

Quality Prefrences
------------------

If you have issues getting streams to load on a particular Plex client, try the various options here.
 * **Stream Quality**, **VOD Quality**
   * *Automatic* - The client gets the master playlist. If the client supports adaptive streaming, it can make its own decisions.
   * *Manual* - For clients that allow users to select video quality (PHT).
   * *Source/High/Medium/Low/Mobile* - Explicitly use the selected quality. If the chosen quality does not exist on the chose stream, it will get the closest match.

If none of these options work, then it is likely that your client does not currently support HLS streams.


Getting an Access Token
=======================

1. At the bottom of the main menu in the channel, there will be an `Authorize` option.
2. It will give you a url to go to in a web browser. (using a url shortener http://shoutkey.com url is valid for 5 min. The URL is always https://id.twitch.tv/oauth2/authorize?scope=user%3Aread%3Aemail&redirect_uri=http%3A%2F%2Flocalhost&response_type=token&client_id=r797t9e3qhgxayiisuqdxxkh5tj7mlz)
3. that redirects you to a Twitch page to authorize the channel to use your account.
4. When you authorize it redirects your browser to `http://localhost/#access_token=<access_token>&scope=user_read` which is a dead page.
5. copy the `<access_token>` string out of that url and put it in the TwitchMod channel preferences using the web interface.
