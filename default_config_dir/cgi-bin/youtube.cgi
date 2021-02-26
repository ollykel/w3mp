#!/usr/bin/env python

import sys
import os
import re
import requests
import json
from urllib import parse as urlparse
from os import path as fpath

from bs4 import BeautifulSoup
import firefox_jar

def extract_data(data, *keys, default=None):
    curr = data
    key_stack = list()
    for key in keys:
        key_stack.append(key)
        if isinstance(curr, list) and key >= len(curr) or isinstance(curr, dict) and key not in curr:
            if default is None:
                raise Exception('Could not find {}; curr item: {}'.format('.'.join(['{}'.format(k) for k in key_stack]), str(curr)))
            else:
                return default
        else:
            curr = curr[key]
    return curr
    #-- end extract_data

def collect_data_by_keys(data, *keynames):
    collection = list()
    iter_data = enumerate(data) if isinstance(data, list) else data.items()
    for k, v in iter_data:
        if k in keynames:
            collection.append(v)
        if isinstance(v, dict) or isinstance(v, list):
            collection += collect_data_by_keys(v, *keynames)
        #-- end for k, v
    return collection
    #-- end collect_data_by_keys

HTTP_VIDEO_FMT = '''HTTP/2 200
Content-Type: text/html; charset=utf-8

<!DOCTYPE html>
<html>
    <head>
        <meta charset="utf-8" />
        <meta lang="en" />
        <title>{title} | Youtube</title>
    </head>
    <body>
        <h1><a href="https://www.youtube.com/watch?v={video_id}">{title}</a></h1>
        <a href="https://youtu.be/{video_id}"><img src="{thumbnail}" alt="[Watch Video]" /></a>
        <p>by <a href="https://www.youtube.com/channel/{channel_id}">{channel_name}</a></p>
        <h2>Uploaded <date>{date}</date></h2>
        <div>
            <span><strong>{views}</strong></span><br />
            <span><strong>{likes} likes</strong></span><br />
        </div>
        <p>{description}</p>
    </body>
</html>
'''

def handle_watch(url, data):
    contents = collect_data_by_keys(data, 'videoPrimaryInfoRenderer')[0]
    title = extract_data(contents, 'title', 'runs', 0, 'text')
    date = extract_data(contents, 'dateText', 'simpleText')
    views = extract_data(contents, 'viewCount', 'videoViewCountRenderer', 'shortViewCount', 'simpleText')
    likes = extract_data(contents, 'videoActions', 'menuRenderer', 'topLevelButtons', 0, 'toggleButtonRenderer', 'defaultText', 'simpleText')
    # raise Exception('oh hai debugger!')
    contents_b = collect_data_by_keys(data, 'videoSecondaryInfoRenderer')[0]
    desc_elems = extract_data(contents_b, 'description', 'runs', default=[{'text': 'No description available'}])
    def parse_desc_elem(elem):
        elem_txt = elem['text'] if 'text' in elem else ''
        elem_urls = collect_data_by_keys(elem, 'url')
        if len(elem_urls) > 0:
            elem_url_parsed = urlparse.urlsplit(elem_urls[0])
            elem_url = \
                urlparse.urlunsplit(('https', 'www.youtube.com') + elem_url_parsed[2:]) if elem_url_parsed.path == '/results' \
                else urlparse.parse_qs(elem_url_parsed.query)['q'][0] if elem_url_parsed.netloc == '' and elem_url_parsed.path == '/redirect' \
                else elem_urls[0]
            return '<a href="{url}">{text}</a>'.format(url=elem_url, text=elem_txt)
        return elem_txt
        #-- end parse_desc_elem
    description = ''.join([parse_desc_elem(e) for e in desc_elems]).replace('\n', '<br />')
    video_owner = collect_data_by_keys(contents_b, 'videoOwnerRenderer')[0]
    channel_id = extract_data(video_owner, 'title', 'runs', 0, 'navigationEndpoint', 'browseEndpoint', 'browseId', default='')
    channel_name = extract_data(contents_b, 'owner', 'videoOwnerRenderer', 'title', 'runs', 0, 'text', default='[Channel Name N/A]')
    video_id = urlparse.parse_qs(url.query)['v'][0]
    thumbnail = 'https://i.ytimg.com/vi/{}/hqdefault.jpg'.format(video_id)
    print(HTTP_VIDEO_FMT.format(title=title, date=date, views=views, likes=likes, description=description, channel_id=channel_id, channel_name=channel_name,
        video_id=video_id, thumbnail=thumbnail))
    #-- end handle_watch

HTTP_CHANNEL_FMT = '''HTTP/2 200
Content-Type: text/html; charset=utf-8

<!DOCTYPE html>
<html>
    <head>
        <meta charset="utf-8" />
        <meta lang="en" />
        <title>Channel: {channel_name} | Youtube</title>
    </head>
    <body>
        <h1><a href="https://www.youtube.com/channel/{channel_id}">Channel: {channel_name}</a></h1>
        <img src="{thumbnail}" alt="[Profile Picture]" />
        <p>{description}</p>
        <p><a href="https://www.youtube.com/channel/{channel_id}/videos">Videos</a> | <a href="https://www.youtube.com/channel/{channel_id}/playlists">Playlists</a></p>
        <form action="https://www.youtube.com/channel/{channel_id}/search" method="GET">
            <input name="query" value="{search_query}" type="text" required />
            <button type="submit">[Search channel]</button>
        </form>
        <hr />
        <h2>Videos</h2>
        <ol>
            {video_displays}
        </ol>
        <h2>Playlists</h2>
        <ol>
            {playlist_displays}
        </ol>
    </body>
</html>
'''

def handle_channel(url, data):
    metadata = extract_data(data, 'metadata', 'channelMetadataRenderer')
    channel_id = extract_data(metadata, 'externalId')
    channel_name = extract_data(metadata, 'title')
    thumbnail = extract_data(metadata, 'avatar', 'thumbnails', -1, 'url')
    description = extract_data(metadata, 'description').replace('\n', '<br />')
    query_data = urlparse.parse_qs(url.query)
    search_query = query_data['query'][0] if 'query' in query_data else ''
    video_data = collect_data_by_keys(data, 'videoRenderer', 'gridVideoRenderer')
    video_fmt = '<li><a href="https://www.youtube.com/watch?v={video_id}"><img src="{thumbnail}" alt="[Preview]" /> {title} | {date}</a></li>'
    def render_video(vd):
        vd_id = extract_data(vd, 'videoId', default='')
        vd_tnail = extract_data(vd, 'thumbnail', 'thumbnails', -1, 'url', default='')
        vd_title = collect_data_by_keys(extract_data(vd, 'title', default={'text': '[Title N/A]'}), 'text', 'simpleText')[0]
        vd_date = extract_data(vd, 'publishedTimeText', 'simpleText', default='[Date N/A]')
        return video_fmt.format(video_id=vd_id, thumbnail=vd_tnail, title=vd_title,
            date=vd_date)
        #-- end render_video
    video_displays = '\n'.join([render_video(v) for v in video_data])
    playlist_data = collect_data_by_keys(data, 'playlistRenderer', 'gridPlaylistRenderer')
    playlist_fmt = '<li><a href="{url}">{title}</a></li>'
    def render_playlist(pl):
        pl_data = extract_data(pl, 'title', 'runs', 0, default=dict())
        pl_title = extract_data(pl_data, 'text', default='[Title N/A]')
        pl_id = (lambda arr: arr[0] if len(arr) > 0 else '[N/A]')(collect_data_by_keys(pl, 'playlistId'))
        pl_url = 'https://www.youtube.com/playlist?list={}'.format(pl_id)
        return playlist_fmt.format(url=pl_url, title=pl_title)
        #-- end render_playlist
    playlist_displays = '\n'.join([render_playlist(p) for p in playlist_data])
    print(HTTP_CHANNEL_FMT.format(channel_id=channel_id, channel_name=channel_name,
        thumbnail=thumbnail, description=description, search_query=search_query,
        video_displays=video_displays, playlist_displays=playlist_displays))
    #-- end handle_channel

HTTP_SEARCH_RESULTS_FMT = '''HTTP/2 200
Content-Type: text/html; charset=utf-8

<!DOCTYPE html>
<html>
    <head>
        <meta charset="utf-8" />
        <meta lang="en" />
        <title>Search Results for "{query}" | Youtube</title>
    </head>
    <body>
        <h1><a href="{url}">Search Results for "{query}"</a></h1>
        <form action="https://www.youtube.com/results" method="GET">
            <input name="search_query" value="{query}" type="text" required />
            <button type="submit">[Search]</button>
        </form>
        <hr />
        <h2>Filter by:</h2>
        <p>
            {filter_displays}
        </p>
        <h2>Channels</h2>
        <ol>
            {channel_displays}
        </ol>
        <h2>Playlists</h2>
        <ol>
            {playlist_displays}
        </ol>
        <h2>Videos</h2>
        <ol>
            {video_displays}
        </ol>
    </body>
</html>
'''

def handle_search_results(url, data):
    parsed_url = urlparse.urlunsplit(url)
    query = urlparse.parse_qs(url.query)['search_query'][0]
    # query = extract_data(data, 'contents', 'twoColumnSearchResultsRenderer', 'primaryContents', 'sectionListRenderer', 'contents', 0, 'itemSectionRenderer', 'contents', 0, 'showingResultsForRenderer', 'correctedQueryEndpoint', 'searchEndpoint', 'query')
    filter_items = collect_data_by_keys(data, 'searchFilterRenderer')
    def render_filter(fi):
        fi_name = extract_data(fi, 'label', 'simpleText', default='[Filter Name N/A]')
        fi_url = 'https://www.youtube.com{}'.format(extract_data(fi, 'navigationEndpoint',
            'commandMetadata', 'webCommandMetadata', 'url', default=''))
        return '<span><a href="{url}">{name}</a></span>'.format(name=fi_name, url=fi_url)
        #-- end render_filter
    filter_displays = ' | '.join(render_filter(f) for f in filter_items)
    channel_items = collect_data_by_keys(data, 'channelRenderer')
    def render_channel(ch):
        ch_id = extract_data(ch, 'channelId', default='')
        ch_url = 'https://www.youtube.com/channel/{}'.format(ch_id)
        ch_name = extract_data(ch, 'title', 'simpleText', default='[Channel Name N/A]')
        return '<li><a href="{url}">{name}</a></li>'.format(url=ch_url, name=ch_name)
        #-- end render_channel
    channel_displays = '\n'.join([render_channel(c) for c in channel_items]) \
        if len(channel_items) > 0 else '<p><em>No channels</em></p>'
    playlist_items = collect_data_by_keys(data, 'playlistRenderer')
    def render_playlist(pl):
        pl_id = extract_data(pl, 'playlistId', default='')
        pl_url = 'https://www.youtube.com/playlist?list={}'.format(pl_id)
        pl_name = extract_data(pl, 'title', 'simpleText', default='[Playlist Name N/A]')
        return '<li><a href="{url}">{name}</a></li>'.format(url=pl_url, name=pl_name)
        #-- end render_channel
    playlist_displays = '\n'.join([render_playlist(p) for p in playlist_items]) \
        if len(playlist_items) > 0 else '<p><em>No playlists</em></p>'
    video_items = collect_data_by_keys(data, 'videoRenderer')
    def render_video(vd):
        vd_id = extract_data(vd, 'videoId')
        vd_tnail = extract_data(vd, 'thumbnail', 'thumbnails', -1, 'url')
        vd_title = extract_data(vd, 'title', 'runs', 0, 'text', default='[Title N/A]')
        vd_date = extract_data(vd, 'publishedTimeText', 'simpleText', default='[Date N/A]')
        vd_views_txt = extract_data(vd, 'viewCountText', 'simpleText', default='[Views N/A]')
        vd_channel_name = extract_data(vd, 'ownerText', 'runs', 0, 'text', default='[Channel Name N/A]')
        vd_channel_id = collect_data_by_keys(vd, 'browseId')[0]
        return '<li><a href="https://www.youtube.com/watch?v={video_id}"><img src="{thumbnail}" alt="[Preview]" /> {title}</a> | <a href="https://www.youtube.com/channel/{channel_id}">{channel_name}</a> | {views} | {date}</li>'.format(
            video_id=vd_id, thumbnail=vd_tnail, title=vd_title,
            channel_name=vd_channel_name, channel_id=vd_channel_id,
            views=vd_views_txt, date=vd_date)
        #-- end render_video
    video_displays = '\n'.join([render_video(v) for v in video_items]) \
        if len(video_items) > 0 else '<p><em>No videos</em></p>'
    print(HTTP_SEARCH_RESULTS_FMT.format(url=parsed_url, query=query,
        filter_displays=filter_displays, channel_displays=channel_displays,
        playlist_displays=playlist_displays, video_displays=video_displays))
    #-- end handle_search_results

HTTP_PLAYLIST_FMT = '''HTTP/2 200
Content-Type: text/html; charset=utf-8

<!DOCTYPE html>
<html>
    <head>
        <meta charset="utf-8" />
        <meta lang="en" />
        <title>Playlist: {title} | Youtube</title>
    </head>
    <body>
        <h1><a href="{url}">Playlist: {title}</a></h1>
        <img src="{thumbnail}" alt="[Thumbnail]" />
        <p>Created by <a href="{creator_url}">{creator_name}</a></p>
        <p>{desc}</p>
        <h2>Videos</h2>
        <ol>
            {video_displays}
        </ol>
    </body>
</html>
'''

def handle_playlist(url, data):
    # raise Exception('Playlist handler not implemented yet')
    data_renderer = collect_data_by_keys(data, 'microformatDataRenderer')[0]
    playlist_id = collect_data_by_keys(data, 'playlistId')[0]
    playlist_url = 'https://www.youtube.com/playlist?list={}'.format(playlist_id)
    title = extract_data(data_renderer, 'title', default='Title N/A')
    desc = extract_data(data_renderer, 'description', default='Description N/A')
    thumbnail = extract_data(data_renderer, 'thumbnail', 'thumbnails', -1, 'url',
        default='')
    owner_renderer = collect_data_by_keys(data, 'videoOwnerRenderer')[0]
    creator_name = extract_data(owner_renderer, 'title', 'runs', 0, 'text',
        default='[Channel Name N/A]')
    creator_url = extract_data(owner_renderer, 'navigationEndpoint',
        'browseEndpoint', 'canonicalBaseUrl', default='')
    videos = collect_data_by_keys(data, 'playlistVideoRenderer')
    video_fmt = '<li><a href="{url}"><img src="{thumbnail}" alt="[Preview]" /> {title}</a> | <a href="{channel_url}">{channel_name}</a></li>'
    def render_video(vid):
        vid_url = 'https://www.youtube.com/watch?v={id}'.format(id=vid['videoId'])
        vid_tnail = extract_data(vid, 'thumbnail', 'thumbnails', -1, 'url', default='')
        vid_title = extract_data(vid, 'title', 'runs', 0, 'text', default='[Title N/A]')
        vid_channel_data = extract_data(vid, 'shortBylineText', 'runs', 0,
            default=dict())
        vid_channel_url = extract_data(vid_channel_data, 'navigationEndpoint',
            'browseEndpoint', 'canonicalBaseUrl', default='')
        vid_channel_name = extract_data(vid_channel_data, 'text',
            default='[Channel Name N/A]')
        return video_fmt.format(url=vid_url, thumbnail=vid_tnail, title=vid_title,
            channel_url=vid_channel_url, channel_name=vid_channel_name)
        #-- end render_video
    video_displays = '\n'.join([render_video(vid) for vid in videos])
    print(HTTP_PLAYLIST_FMT.format(url=playlist_url, title=title, thumbnail=thumbnail,
        desc=desc, creator_url=creator_url, creator_name=creator_name,
        video_displays=video_displays))
    #-- end handle_playlist

HTTP_CAPTCHA_FMT = '''HTTP/2 200
Content-Type: text/html; charset=utf-8

<!DOCTYPE html>
<html>
    <head>
        <meta charset="utf-8" />
        <meta lang="en" />
        <title>You got a Captcha! | Youtube</title>
    </head>
    <body>
        <h1>You got a Captcha! | Youtube</h1>
        <p>Open this page in Firefox (default profile) to solve the Captcha and refresh the cookie: <a href="{url}">{url}</a></p>
    </body>
</html>
'''

def handle_captcha(url, data):
    print(HTTP_CAPTCHA_FMT.format(url=urlparse.urlunsplit(url)))
    #-- end handle_captcha

HTTP_ERR_FMT = '''HTTP/2 404
Content-Type: text/html; charset=utf-8

<!DOCTYPE html>
<html>
    <head>
        <meta charset="utf-8" />
        <meta lang="en" />
        <title>Error: {err_msg} | Youtube</title>
    </head>
    <body>
        <h1>Error | Youtube</h1>
        <p>{err_msg}</p>
        <p>See logs at file://{log_file}</p>
    </body>
</html>
'''

if __name__ == "__main__":
    raw_data = ''
    try:
        # get user agent
        user_agent = None
        with open(fpath.join(os.getenv('W3M_CONFIG_HOME', ''), 'user-agents.txt'), 'r') as user_agent_file:
            user_agents = user_agent_file.readline()
            user_agent_idx = int(os.getenv('W3M_USER_AGENT', '1')) - 1
            user_agent = user_agents[user_agent_idx] if user_agent_idx < len(user_agents) and user_agent_idx >= 0 else user_agents[0] if len(user_agents) > 0 else None
            #-- end with user_agent file
        req_headers = {'User-Agent': user_agent} if user_agent is not None else dict()
        query_str = os.getenv('QUERY_STRING')
        uri_pattern = re.compile('.*://?')
        path = uri_pattern.sub('', query_str)
        url = 'https://www.youtube.com/{path}'.format(path=path)
        # fetch firefox cookies
        firefox_profile = os.getenv('W3M_FIREFOX_PROFILE', 'default')
        cookies = firefox_jar.firefox_jar(profile_name=firefox_profile)
        cookie_fname = fpath.join(os.getenv('W3M_CONFIG_HOME', ''), 'cookies.txt')
        cookies.save(filename=cookie_fname)
        conn = requests.get(url=url, headers=req_headers, cookies=cookies)
        raw_data = conn.text
        parsed_url = urlparse.urlsplit(conn.url)
        url_path = parsed_url.path.strip('/').split('/')
        handlers = {
            "watch": handle_watch,
            "channel": handle_channel,
            "user": handle_channel,
            "results": handle_search_results,
            "playlist": handle_playlist,
            "das_captcha": handle_captcha,
        }
        key_path = url_path[0]
        if key_path not in handlers or conn.status_code != 200:
            print('HTTP/2 {status_code}\nContent-Type: text/html; charset=utf-8\n\n{document}'.format(status_code=conn.status_code, document=conn.text))
            exit(0)
        soup = BeautifulSoup(conn.text, 'html.parser')
        yt_data_pattern = re.compile(r'ytInitialData')
        yt_data_script = soup.find('script', text=yt_data_pattern)
        if yt_data_script is None:
            logFname = fpath.join(os.getenv('W3M_TEMP', fpath.expanduser('~')), 'youtube.log.html')
            with open(logFname, 'w') as logFile:
                logFile.write(conn.text)
                #-- end with logFile
            raise Exception('Could not find ytInitialData; See raw data at {fname}.'.format(fname=logFname))
            # end if yt_data_script is None
        lines = conn.text.splitlines()
        yt_data = yt_data_script.string[yt_data_script.string.find('{'):yt_data_script.string.find('};') + 1]
        if len(yt_data) < 1:
            logFname = fpath.join(os.getenv('W3M_TEMP', fpath.expanduser('~')), 'youtube.log.html')
            with open(logFname, 'w') as logFile:
                logFile.write(conn.text)
                #-- end with logFile
            raise Exception('Could not find ytInitialData; See raw data at {fname}.'.format(fname=logFname))
        data = json.loads(yt_data)
        handler = handlers[key_path]
        handler(parsed_url, data)
    except Exception as err:
        logFname = fpath.join(os.getenv('W3M_TEMP', fpath.expanduser('~')), 'youtube.log.html')
        with open(logFname, 'w') as logFile:
            logFile.write(raw_data)
            #-- end with logFile
        print(HTTP_ERR_FMT.format(err_msg=err, log_file=logFname))
        exit(0)
    #-- end main


