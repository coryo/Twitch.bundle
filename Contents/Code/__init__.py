# TwitchMod by Cory <babylonstudio@gmail.com>
from sys import maxint as MAXINT
import re
from urllib import urlencode
from updater import Updater
from DumbTools import DumbKeyboard, DumbPrefs
TWITCH_API_BASE = 'https://api.twitch.tv/kraken'
TWITCH_API_NEW_BASE = 'https://id.twitch.tv'
TWITCH_API_MIME_TYPE = "application/vnd.twitchtv.v{version}+json".format(version=3)
TWITCH_CLIENT_ID = 'r797t9e3qhgxayiisuqdxxkh5tj7mlz'
PAGE_LIMIT = 20
NAME = 'TwitchMod'
PREFIX = '/video/twitchmod'
ICON = 'icon-default.png'
ART = 'art-default.png'
ICONS = {'search':    R('ic_search_c.png'),
         'following': R('ic_following_c.png'),
         'games':     R('ic_games_c.png'),
         'videos':    R('ic_videos_c.png'),
         'channels':  R('ic_channels_c.png'),
         'more':      R('ic_more_c.png'),
         'settings':  R('ic_settings_c.png'),
         'authorize': R('ic_settings_c.png')}


def Start():
    ObjectContainer.title1 = NAME
    ObjectContainer.art = R(ART)
    HTTP.Headers['Accept'] = TWITCH_API_MIME_TYPE
    HTTP.CacheTime = CACHE_1MINUTE
    if 'last_update' not in Dict:
        Dict['last_update'] = 0
        Dict.Save()


@handler(PREFIX, NAME, ICON, ART)
def MainMenu(**kwargs):
    oc = ObjectContainer(no_cache=True)
    Updater(PREFIX + '/updater', oc)
    main_layout = Prefs['main_layout'].split(',')
    for item in main_layout:
        if item == 'featured':
            oc.add(DirectoryObject(key=Callback(FeaturedStreamsList),
                                   title=unicode(L('featured_streams')), thumb=ICONS['channels']))
        elif item == 'top':
            oc.add(DirectoryObject(key=Callback(TopStreamsList),
                                   title=unicode(L('top_streams')), thumb=ICONS['channels']))
        elif item == 'games':
            oc.add(DirectoryObject(key=Callback(TopGamesList),
                                   title=unicode(L('games')), thumb=ICONS['games'],
                                   summary=unicode(L('browse_summary'))))
        elif item == 'search':
            oc.add(DirectoryObject(key=Callback(SearchMenu),
                                   title=unicode(L('search')), thumb=ICONS['search'],
                                   summary=unicode(L('search_prompt'))))
        elif item == 'followed':
            oc.add(DirectoryObject(key=Callback(FollowedChannelsList),
                                   title=unicode((L('followed_channels'))), thumb=ICONS['following']))
        elif item == 'favorite_games' and Prefs['favourite_games']:
            oc.add(DirectoryObject(key=Callback(FavGames),
                                   title=unicode((L('favourite_games'))), thumb=ICONS['following']))
    if Client.Product in DumbPrefs.clients:
        DumbPrefs(PREFIX, oc, title=unicode(L('Preferences')), thumb=ICONS['settings'])
    else:
        oc.add(PrefsObject(title=unicode(L('Preferences')), thumb=ICONS['settings']))

    if not Prefs['access_token']:
        oc.add(DirectoryObject(key=Callback(Authorize),
                               title=unicode(L('authorize')),
                               thumb=ICONS['authorize']))

    return oc


class APIError(Exception):
    pass


def api_request(endpoint, method='GET', params=None, cache_time=HTTP.CacheTime):
    """``endpoint`` is either the full url (provided by the api) or just the endpoint."""
    url = add_params(TWITCH_API_BASE + endpoint if endpoint.startswith('/') else endpoint,
                     params=params)
    try:
        data = JSON.ObjectFromURL(url, cacheTime=cache_time, headers={'Client-ID': TWITCH_CLIENT_ID})
    except Exception as e:
        Log.Error("TWITCH: API request failed. {} - {}".format(e.message, e.args))
        raise APIError(str(e))
    else:
        return data


def add_params(url, params=None):
    return url if params is None else '{}?{}'.format(url, urlencode(params))


def time_since(dt_utc, pretty=False):
    """Returns a string of the time since the utc datetime ``dt`` """
    delta = Datetime.UTCNow() - dt_utc.replace(tzinfo=None)
    seconds = delta.total_seconds()
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if not pretty:
        return "{}:{:02f}:{:02f}".format(h, m, s)
    d, h = divmod(h, 24)
    if d > 0:
        return "{:.0f} {} ago".format(d, "days" if d > 1 else "day")
    elif h > 0:
        return "{:.0f} {} ago".format(h, "hours" if h > 1 else "hour")
    elif m > 0:
        return "{:.0f} {} ago".format(m, "minutes" if m > 1 else "minute")
    else:
        return "now"


def error_message(error, message):
    Log.Error("TWITCH: {} - {}".format(error, message))
    return MessageContainer(header=unicode(error), message=unicode(message))


def xstr(s):
    return '' if s is None else str(s)


def get_preview_image(url, cache_time=120):
    """Returns url with a timestamp appended to it.
    If the URL to the image for a thumb is different, it will reload it.
    The timestamp will change if 2 minutes have passed since the last time.
    """
    now = Datetime.TimestampFromDatetime(Datetime.Now())
    if now - Dict['last_update'] > cache_time:
        Dict['last_update'] = now
    return "{}?t={:.0f}".format(url, Dict['last_update'])


def get_streams(channels, cache_time=0):
    """Returns the streamObjects for the given list of channel names
    returns a dict, key is stream name, value is the 'stream object' json string
    """
    try:
        res = api_request('/streams', params={'channel': ','.join(channels)}, cache_time=cache_time)
    except APIError:
        return {}
    return {so['channel']['name']: so for so in res['streams']}


def stream_strings(stream, title_layout=None):
    """Returns a title and summary string for a twitch stream object."""
    title_layout = title_layout if title_layout is not None else Prefs['title_layout']
    status = xstr(stream['channel'].get('status', '?'))
    start_time = Datetime.ParseDate(stream['created_at'])
    quality = "{}p{:.0f}".format(stream['video_height'], stream['average_fps'])
    viewers_string = "{:,} {}".format(int(stream['viewers']), L('viewers'))
    title_elements = {'name': stream['channel']['display_name'],
                      'views': viewers_string,
                      'status': status,
                      'game': xstr(stream['channel'].get('game', '?')),
                      'time': time_since(start_time),
                      'quality': quality}
    return (title_str(title_layout).format(**title_elements),
            "{}\nStarted {}\n{}\n\n{}".format(viewers_string, time_since(start_time, pretty=True),
                                              quality, status))


def title_str(csv, separator='-', padding=1):
    """Returns a string to be formatted. (csv='{a},{b}', separator='-', padding=1)->'{a} - {b}'"""
    return '{:^{p}}'.format(separator, p=len(separator) + padding * 2).join(csv.split(','))


def stream_dir(stream, title_layout=None):
    """Returns a DirectoryObject with a callback to ChannelMenu, from a twitch stream object"""
    title, summary = stream_strings(stream, title_layout)
    return DirectoryObject(
        key=Callback(ChannelMenu, channel_name=stream['channel']['name'],
                     stream=stream),
        title=unicode(title), summary=unicode(summary),
        tagline=unicode('{},{}'.format(stream['channel']['display_name'], stream['viewers'])),
        thumb=Resource.ContentsOfURLWithFallback(
            get_preview_image(stream['preview']['medium']), fallback=ICONS['videos']))


def stream_vid(stream, title_layout=None):
    """Returnss a VideoClipObject from a twitch stream object"""
    title, summary = stream_strings(stream, title_layout)
    return VideoClipObject(
        url=SharedCodeService.shared.service_url(stream['channel']['url'], Prefs['access_token']),
        title=unicode(title), summary=unicode(summary),
        thumb=Resource.ContentsOfURLWithFallback(
            get_preview_image(stream['preview']['medium']), fallback=ICONS['videos']))


def channel_dir(channel, offline=False):
    """Returns a DirectoryObject with a callback to ChannelMenu, from a twitch channel object"""
    name = channel['name']
    display_name = channel['display_name']
    status = channel.get('status', '?')
    logo_img = channel['logo']
    title = "{} - {}".format(display_name, L('offline')) if offline else display_name
    return DirectoryObject(
        key=Callback(ChannelMenu, channel_name=name, stream=None),
        title=unicode(title), summary=unicode(status),
        tagline=unicode('{},{}'.format(display_name, 0)),
        thumb=Resource.ContentsOfURLWithFallback(logo_img, fallback=ICONS['videos']))

####################################################################################################
# ROUTES
####################################################################################################
@route(PREFIX + '/favourite/games')
def FavGames(**kwargs):
    oc = ObjectContainer(title2=unicode(L('favourite_games')))
    try:
        games = Prefs['favourite_games'].split(',')
    except Exception:
        return error_message(oc.title2, L('favourite_games_error'))
    for game in games:
        oc.add(DirectoryObject(key=Callback(SearchStreams, query=game.strip(),
                                            title_layout=Prefs['title_layout2']),
                               title=unicode(game), thumb=ICONS['games']))
    return oc


@route(PREFIX + '/channel/{channel_name}/menu', stream=dict)
def ChannelMenu(channel_name, stream=None, **kwargs):
    oc = ObjectContainer(title2=unicode(channel_name))
    if stream is not None:
        oc.add(stream_vid(stream))  # Watch Live
    # Highlights
    oc.add(DirectoryObject(key=Callback(ChannelVodsList, name=channel_name, broadcasts=False),
                           title=unicode(L('highlights')), thumb=ICONS['videos']))
    # Past Broadcasts
    oc.add(DirectoryObject(key=Callback(ChannelVodsList, name=channel_name, broadcasts=True),
                           title=unicode(L('past_broadcasts')), thumb=ICONS['videos']))
    return oc


@route(PREFIX + '/following', limit=int)
def FollowedChannelsList(apiurl=None, limit=100, **kwargs):
    """Returns a list of followed channels. Two requests are made in this route:
    1. get 'follow' objects, which contains the information for the channels
    2. get 'stream' objects, which contains info about the stream if its live
    """
    oc = ObjectContainer(title2=L('followed_channels'))
    try:
        following = (api_request(apiurl) if apiurl is not None else
                     api_request('/users/{}/follows/channels'.format(Prefs['username']),
                                 params={'limit': limit, 'sortby': 'last_broadcast',
                                         'direction': 'desc'}))
    except APIError:
        return error_message(oc.title2, L('followed_streams_list_error'))
    followed_channels = [channel['channel']['name'] for channel in following['follows']]
    # get a list of stream objects for followed streams so we can add Live status to the title
    streams = get_streams(followed_channels)
    for item in following['follows']:  # listing all the followed channels, both live and offline
        channel, name = item['channel'], item['channel']['name']
        if name in streams:
            oc.add(stream_dir(streams[name]))  # live
        else:
            if not Prefs['hide_offline']:
                oc.add(channel_dir(channel, offline=True))  # not live
    # Sort the items
    if Prefs['following_order'] == 'view_count':  # viewers desc
        oc.objects.sort(key=lambda obj: int(obj.tagline.split(',')[-1]), reverse=True)
    else:  # name asc
        oc.objects.sort(key=lambda obj: obj.tagline.split(',')[0])
    if len(oc) >= limit:
        oc.add(NextPageObject(key=Callback(FollowedChannelsList,
                                           apiurl=following['_links']['next'], limit=limit),
                              title=unicode(L('more')), thumb=ICONS['more']))
    return oc


@route(PREFIX + '/channel/vods', broadcasts=bool, limit=int)
def ChannelVodsList(name=None, apiurl=None, broadcasts=True, limit=PAGE_LIMIT, **kwargs):
    """Returns videoClipObjects for ``channel``. ignore vods that aren't v type."""
    oc = ObjectContainer(title2=L('past_broadcasts') if broadcasts else L('highlights'))
    try:
        videos = (api_request(apiurl) if apiurl is not None else
                  api_request('/channels/{}/videos'.format(name),
                              params={'limit': limit, 'broadcasts': str(broadcasts).lower()}))
    except APIError:
        return error_message(oc.title2, "Error")
    ignored = 0
    for video in videos['videos']:
        url = video['url']
        vod_date = Datetime.ParseDate(video['recorded_at'])
        vod_title = video['title'] if video['title'] else L('untitled_broadcast')
        title = "{} - {}".format(vod_date.strftime('%a %b %d, %Y'), vod_title)
        oc.add(VideoClipObject(url=SharedCodeService.shared.service_url(url, Prefs['access_token']),
                               title=unicode(title),
                               summary=unicode(video['description']),
                               duration=min(int(video['length']) * 1000, MAXINT),
                               thumb=Resource.ContentsOfURLWithFallback(video['preview'],
                                                                        fallback=ICONS['videos'])))
    if len(oc) + ignored >= limit:
        oc.add(NextPageObject(key=Callback(ChannelVodsList, apiurl=videos['_links']['next'],
                                           broadcasts=broadcasts, limit=limit),
                              title=unicode(L('more')), thumb=ICONS['more']))
    return oc


@route(PREFIX + '/topstreams', limit=int)
def TopStreamsList(apiurl=None, limit=PAGE_LIMIT, **kwargs):
    oc = ObjectContainer(title2=L('top_streams'), no_cache=True)
    try:
        top = (api_request(apiurl) if apiurl is not None else
               api_request('/streams', params={'limit': limit}))
    except APIError:
        return error_message(oc.title2, "Error")
    for stream in top['streams']:
        oc.add(stream_dir(stream))
    if len(oc) >= limit:
        oc.add(NextPageObject(key=Callback(TopStreamsList, apiurl=top['_links']['next']),
                              title=unicode(L('more')), thumb=ICONS['more']))
    return oc


@route(PREFIX + '/featured', limit=int)
def FeaturedStreamsList(apiurl=None, limit=PAGE_LIMIT, **kwargs):
    oc = ObjectContainer(title2=L('featured_streams'), no_cache=True)
    featured = (api_request(apiurl) if apiurl is not None else
                api_request('/streams/featured', params={'limit': limit}))
    if featured is None:
        return error_message(oc.title2, "Error")
    for featured_stream in featured['featured']:
        oc.add(stream_dir(featured_stream['stream']))
    if len(oc) >= limit:
        oc.add(NextPageObject(key=Callback(FeaturedStreamsList, apiurl=featured['_links']['next']),
                              title=unicode(L('more')), thumb=ICONS['more']))
    return oc


@route(PREFIX + '/games', limit=int)
def TopGamesList(apiurl=None, limit=PAGE_LIMIT,  **kwargs):
    oc = ObjectContainer(title2=L('top_games'), no_cache=True)
    try:
        games = (api_request(apiurl) if apiurl is not None else
                 api_request('/games/top', params={'limit': limit}))
    except APIError:
        return error_message(oc.title2, "Error")
    for game in games['top']:
        game_summary = "{} {}\n{} {}".format(game['channels'], L('channels'),
                                             game['viewers'], L('viewers'))
        oc.add(DirectoryObject(key=Callback(ChannelsForGameList, game=game['game']['name']),
                               title=unicode(game['game']['name']),
                               summary=unicode(game_summary),
                               thumb=Resource.ContentsOfURLWithFallback(
                                   game['game']['box']['medium'], fallback=ICONS['videos'])))
    if len(oc) >= limit:
        oc.add(NextPageObject(key=Callback(TopGamesList, apiurl=games['_links']['next']),
                              title=unicode(L('more')), thumb=ICONS['more']))
    return oc


@route(PREFIX + '/channel', limit=int)
def ChannelsForGameList(game, apiurl=None, limit=PAGE_LIMIT,  **kwargs):
    oc = ObjectContainer(title2=unicode(game), no_cache=True)
    try:
        streams = (api_request(apiurl) if apiurl is not None else
                   api_request('/streams', params={'limit': limit, 'game': game}))
    except APIError:
        return error_message(oc.title2, "Error")
    for stream in streams['streams']:
        oc.add(stream_dir(stream, title_layout=Prefs['title_layout2']))
    if len(oc) >= limit:
        oc.add(NextPageObject(key=Callback(ChannelsForGameList, game=game,
                                           apiurl=streams['_links']['next'], limit=limit),
                              title=unicode(L('more')), thumb=ICONS['more']))
    return oc


@route(PREFIX + '/search')
def SearchMenu(**kwargs):
    """Returns a list of the different search methods"""
    search_routes = {'streams': SearchStreams, 'channels': SearchChannels, 'games': SearchGames}
    oc = ObjectContainer(title2=L('search'))
    for search_type, route in search_routes.iteritems():
        title = '{} {}'.format(L('search'), L(search_type))
        prompt = '{} {}'.format(L('search_prompt'), L(search_type))
        if Client.Product in DumbKeyboard.clients:
            DumbKeyboard(PREFIX, oc, route, dktitle=unicode(title), dkthumb=ICONS['search'])
        else:
            oc.add(InputDirectoryObject(key=Callback(route), title=unicode(title),
                                        thumb=ICONS['search'], prompt=unicode(prompt)))
    return oc


@route(PREFIX + '/search/streams', limit=int)
def SearchStreams(query, apiurl=None, limit=PAGE_LIMIT, title_layout=None, **kwargs):
    oc = ObjectContainer(title2=L('search'), no_cache=True)
    try:
        results = (api_request(apiurl) if apiurl is not None else
                   api_request('/search/streams', params={'query': query, 'limit': limit}))
    except APIError:
        return error_message(oc.title2, "Error")
    if not results['streams']:
        return error_message(L('search'), L('search_error'))
    for stream in results['streams']:
        oc.add(stream_dir(stream, title_layout=title_layout))
    if len(oc) >= limit:
        oc.add(NextPageObject(key=Callback(SearchStreams, query=query, limit=limit,
                                           apiurl=results['_links']['next'],
                                           title_layout=title_layout),
                              title=unicode(L('more')), thumb=ICONS['more']))
    return oc


@route(PREFIX + '/search/channels', limit=int)
def SearchChannels(query, apiurl=None, limit=PAGE_LIMIT, **kwargs):
    oc = ObjectContainer(title2=L('search'), no_cache=True)
    try:
        results = (api_request(apiurl) if apiurl is not None else
                   api_request('/search/channels', params={'query': query, 'limit': limit}))
    except APIError:
        return error_message(oc.title2, "Error")
    if not results['channels']:
        return error_message(L('search'), L('search_error'))
    for channel in results['channels']:
        oc.add(channel_dir(channel))
    if len(oc) >= limit:
        oc.add(NextPageObject(key=Callback(SearchChannels, query=query,
                                           apiurl=results['_links']['next'], limit=limit),
                              title=unicode(L('more')), thumb=ICONS['more']))
    return oc


@route(PREFIX + '/search/games')
def SearchGames(query, apiurl=None, **kwargs):
    """Returns a list of results from ``query``. This API endpoint has no paging"""
    oc = ObjectContainer(title2=L('search'), no_cache=True)
    try:
        results = (api_request(apiurl) if apiurl is not None else
                   api_request('/search/games', params={'query': query, 'type': 'suggest',
                                                        'live': 'true'}))
    except APIError:
        return error_message(oc.title2, "Error")
    if not results['games']:
        return error_message(L('search'), L('search_error'))
    for game in results['games']:
        oc.add(DirectoryObject(key=Callback(ChannelsForGameList, game=game['name']),
                               title=unicode(game['name']),
                               thumb=Resource.ContentsOfURLWithFallback(
                                   game['box']['medium'], fallback=ICONS['videos'])))
    return oc


@route(PREFIX + '/authorize')
def Authorize(**kwargs):
    """Auth involves sending the user to a twitch URL where they go through the auth process,
    which results in a token string. It doesn't seem reasonable to do this entire process in a plex
    client. So we give the user an address to go to in a web browser
    to complete the process, then enter the token they receive into the channels preferences."""
    scopes = ['user:read:email']
    url = add_params(TWITCH_API_NEW_BASE + '/oauth2/authorize', {
        'client_id': TWITCH_CLIENT_ID,
        'response_type': 'token',
        'redirect_uri': 'http://localhost',
        'scope': '+'.join(scopes),
    })
    Log.Debug('TWITCH: auth url: {}'.format(url))
    return ObjectContainer(message=url)
