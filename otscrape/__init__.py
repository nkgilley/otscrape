import time
import calendar
import requests

headers = {
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
  "Accept": "application/json",
  "Content-Type": "application/json"
}


def make_ordinal(n):
    '''
    Convert an integer into its ordinal representation::

        make_ordinal(0)   => '0th'
        make_ordinal(3)   => '3rd'
        make_ordinal(122) => '122nd'
        make_ordinal(213) => '213th'
    '''
    try:
        n = int(n)
    except:
        return n.upper()
    suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    return str(n) + suffix

def events2games(events):
    games = []
    for event in events:
        game = {}
        home_id = 0
        away_id = 0
        home_score = 0
        away_score = 0
        game['epoch'] = event['dt'] / 1000
        game['status'] = event['es']
        for participant in event['participants']:
            if participant['ih']:
                home_id = participant['source']['tmid']
                game['home_team'] = participant['source']['nam']
                game['home_team_abbr'] = participant['source']['abbr']
                game['home_team_rank'] = participant['tr']
            else:
                away_id = participant['source']['tmid']
                game['away_team'] = participant['source']['nam']
                game['away_team_abbr'] = participant['source']['abbr']
                game['away_team_rank'] = participant['tr']
        if 'home_team' not in game or 'away_team' not in game:
            continue 
        if event.get('currentLines'):
            for line in event['currentLines']:
                if line['paid'] == 10: # pinnacle
                    if line['mtid'] == 401: # spread
                        if line['partid'] == home_id:
                            game['home_spread'] = line['adj']
                            game['home_spread_odds'] = line['ap']
                        elif line['partid'] == away_id:
                            game['away_spread'] = line['adj']
                            game['away_spread_odds'] = line['ap']
                    elif line['mtid'] == 402 or line['mtid'] == 412: # over/under
                        if line['partid'] == 15144: # under
                            game['under_odds'] = line['ap']
                            game['under'] = line['adj']
                        if line['partid'] == 15143: # over
                            game['over_odds'] = line['ap']
                            game['over'] = line['adj']
                        game['total'] = line['adj']
                        game['total_odds'] = line['ap']
                    elif line['mtid'] == 83 or line['mtid'] == 125: # moneyline
                        if line['partid'] == home_id:
                            game['home_ml'] = line['ap']
                        elif line['partid'] == away_id:
                            game['away_ml'] = line['ap']
        for score in event['scores']:
            if score['partid'] == home_id:
                home_score += int(score['val'])
            elif score['partid'] == away_id:
                away_score += int(score['val'])
        game['home_score'] = home_score
        game['away_score'] = away_score
        for stat in event['statistics']:
            if stat['nam'] == "gamestate-minutes":
                game['minutes'] = stat['val']
            elif stat['nam'] == "gamestate-seconds":
                game['seconds'] = stat['val']
            elif stat['nam'] == "gamestate-quarter":
                game['quarter'] = stat['val']
            elif stat['nam'] == "gamestate-period":
                game['period'] = stat['val']
            elif stat['nam'] == "gamestate-inning":
                game['inning'] = stat['val']
        time = qtr = ""
        if event['es'] == 'in-progress':
            for play in event['plays']:
                if time == "" and (play['nam'] == "event_clock" or play['nam'] == "event-clock"):
                    time = play['val']
                if qtr == "" and (play['nam'] == "last-play-half" or play['nam'] == 'last-play-period' or play['nam'] == 'last-play-quarter'):
                    qtr = make_ordinal(play['val'])
            if time != "" and qtr != "":
                game['status'] = qtr + ' ' + time
        games.append(game)
    return games

def scrapeNFL(date=""):

    if date == "":
        date = int((calendar.timegm(time.gmtime()) - 86400) * 1000)

    # to get this url, inspect the page and change the market type
    url = 'https://www.oddstrader.com/odds-v2/odds-v2-service?query=%7B+eventsByDate(+mtid:+[401,+402,+83],+showEmptyEvents:+true,+marketTypeLayout:+%22PARTICIPANTS%22,+lid:+16,+spid:+4,+ic:+false,+startDate:+' + str(date) + ',+timezoneOffset:+-4,+nof:+true,+hl:+true,+sort:+%7Bby:+[%22lid%22,+%22dt%22,+%22des%22],+order:+ASC%7D+)+%7B+events+%7B+eid+lid+spid+des+dt+es+rid+ic+ven+tvs+cit+cou+st+sta+hl+seid+consensus+%7B+eid+mtid+bb+boid+partid+sbid+paid+lineid+wag+perc+vol+tvol+wb+}+plays(pgid:+2,+limitLastSeq:+3)+%7B+eid+sqid+siid+gid+nam+val+tim+%7D+scores+%7B+partid+val+eid+pn+sequence+%7D+participants+%7B+eid+partid+psid+ih+rot+tr+sppil+startingPitcher+%7B+fn+lnam+}+source+%7B+...+on+Player+%7B+pid+fn+lnam+}+...+on+Team+%7B+tmid+lid+nam+nn+sn+abbr+cit+}+...+on+ParticipantGroup+%7B+partgid+nam+lid+participants+%7B+eid+partid+psid+ih+rot+source+%7B+...+on+Player+%7B+pid+fn+lnam+}+...+on+Team+%7B+tmid+lid+nam+nn+sn+abbr+cit+}+}+}+}+}+}+marketTypes+%7B+mtid+spid+nam+des+settings+%7B+sitid+did+alias+layout+format+template+sort+url+}+}+bettingOptions+%7B+boid+nam+mtid+spid+partid+}+currentLines(paid:+[20,3,10,8,9,44,29,38,16,65,92,28,83,84,82,15,35,45,54,22,18,5,36,78])+openingLines+eventGroup+%7B+egid+nam+}+statistics(sgid:+3)+{+val+eid+nam+partid+pid+typ+siid+sequence+}+league+%7B+lid+nam+rid+spid+sn+settings+%7B+alias+rotation+ord+shortnamebreakpoint+}+}+}+maxSequences+%7B+events:+eventsMaxSequence+scores:+scoresMaxSequence+currentLines:+linesMaxSequence+statistics:+statisticsMaxSequence+plays:+playsMaxSequence+}+}+%7D'
    r=requests.get(url, headers=headers)
    events = r.json()['data']['eventsByDate']['events']
    return events2games(events)


def scrapeNBA(date=""):

    if date == "":
        date = int((calendar.timegm(time.gmtime()) - 86400) * 1000)

    # to get this url, inspect the page and change the market type
    url = 'https://www.oddstrader.com/odds-v2/odds-v2-service?query={+eventsByDateByLeagueGroup(+leagueGroups:+[{+mtid:+[401,+402,83],+lid:+5,+spid:+5+}],+showEmptyEvents:+true,+marketTypeLayout:+"PARTICIPANTS",+ic:+false,+startDate:+' + str(date) + ',+timezoneOffset:+-4,+nof:+true,+hl:+true,+sort:+{by:+["lid",+"dt",+"des"],+order:+ASC}+)+{+events+{+eid+lid+spid+des+dt+es+rid+ic+ven+tvs+cit+cou+st+sta+hl+seid+consensus+{+eid+mtid+bb+boid+partid+sbid+paid+lineid+wag+perc+vol+tvol+wb+}+plays(pgid:+2,+limitLastSeq:+3)+{+eid+sqid+siid+gid+nam+val+tim+}+scores+{+partid+val+eid+pn+sequence+}+participants+{+eid+partid+psid+ih+rot+tr+sppil+startingPitcher+{+fn+lnam+}+source+{+...+on+Player+{+pid+fn+lnam+}+...+on+Team+{+tmid+lid+nam+nn+sn+abbr+cit+}+...+on+ParticipantGroup+{+partgid+nam+lid+participants+{+eid+partid+psid+ih+rot+source+{+...+on+Player+{+pid+fn+lnam+}+...+on+Team+{+tmid+lid+nam+nn+sn+abbr+cit+}+}+}+}+}+}+marketTypes+{+mtid+spid+nam+des+settings+{+sitid+did+alias+layout+format+template+sort+url+}+}+bettingOptions+{+boid+nam+mtid+spid+partid+}+currentLines(paid:+[20,3,10,8,9,44,29,38,16,65,92,28,83,84,82,15,35,45,54,22,18,5,36,78])+openingLines+eventGroup+{+egid+nam+}+statistics(sgid:+3)+{+val+eid+nam+partid+pid+typ+siid+sequence+}+league+{+lid+nam+rid+spid+sn+settings+{+alias+rotation+ord+shortnamebreakpoint+}+}+}+maxSequences+{+events:+eventsMaxSequence+scores:+scoresMaxSequence+currentLines:+linesMaxSequence+statistics:+statisticsMaxSequence+plays:+playsMaxSequence+}+}+}'
    r=requests.get(url, headers=headers)
    events = r.json()['data']['eventsByDateByLeagueGroup']['events']
    return events2games(events)

def scrapeMLB(date=""):

    if date == "":
        date = int((calendar.timegm(time.gmtime()) - 86400) * 1000)

    # to get this url, inspect the page and change the market type
    url = 'https://www.oddstrader.com/odds-v2/odds-v2-service?query={+eventsByDateByLeagueGroup(+leagueGroups:+[{+mtid:+[83,401,402],+lid:+3,+spid:+3+}],+showEmptyEvents:+true,+marketTypeLayout:+"PARTICIPANTS",+ic:+false,+startDate:+' + str(date) + ',+timezoneOffset:+-4,+nof:+true,+hl:+true,+sort:+{by:+["lid",+"dt",+"des"],+order:+ASC}+)+{+events+{+eid+lid+spid+des+dt+es+rid+ic+ven+tvs+cit+cou+st+sta+hl+seid+consensus+{+eid+mtid+bb+boid+partid+sbid+paid+lineid+wag+perc+vol+tvol+wb+}+plays(pgid:+2,+limitLastSeq:+3)+{+eid+sqid+siid+gid+nam+val+tim+}+scores+{+partid+val+eid+pn+sequence+}+participants+{+eid+partid+psid+ih+rot+tr+sppil+startingPitcher+{+fn+lnam+}+source+{+...+on+Player+{+pid+fn+lnam+}+...+on+Team+{+tmid+lid+nam+nn+sn+abbr+cit+}+...+on+ParticipantGroup+{+partgid+nam+lid+participants+{+eid+partid+psid+ih+rot+source+{+...+on+Player+{+pid+fn+lnam+}+...+on+Team+{+tmid+lid+nam+nn+sn+abbr+cit+}+}+}+}+}+}+marketTypes+{+mtid+spid+nam+des+settings+{+sitid+did+alias+layout+format+template+sort+url+}+}+bettingOptions+{+boid+nam+mtid+spid+partid+}+currentLines(paid:+[20,3,10,8,9,44,29,38,16,65,92,28,83,84,82,15,35,45,54,22,18,5,36,78])+openingLines+eventGroup+{+egid+nam+}+statistics(sgid:+3)+{+val+eid+nam+partid+pid+typ+siid+sequence+}+league+{+lid+nam+rid+spid+sn+settings+{+alias+rotation+ord+shortnamebreakpoint+}+}+}+maxSequences+{+events:+eventsMaxSequence+scores:+scoresMaxSequence+currentLines:+linesMaxSequence+statistics:+statisticsMaxSequence+plays:+playsMaxSequence+}+}+}'
    r=requests.get(url, headers=headers)
    events = r.json()['data']['eventsByDateByLeagueGroup']['events']
    return events2games(events)

def scrapeNHL(date=""):

    if date == "":
        date = int((calendar.timegm(time.gmtime()) - 86400) * 1000)

    # to get this url, inspect the page and change the market type
    url = 'https://www.oddstrader.com/odds-v2/odds-v2-service?query={+eventsByDateByLeagueGroup(+leagueGroups:+[{+mtid:+[125,401,412],+lid:+7,+spid:+6+}],+showEmptyEvents:+true,+marketTypeLayout:+"PARTICIPANTS",+ic:+false,+startDate:+' + str(date) + ',+timezoneOffset:+-4,+nof:+true,+hl:+true,+sort:+{by:+["lid",+"dt",+"des"],+order:+ASC}+)+{+events+{+eid+lid+spid+des+dt+es+rid+ic+ven+tvs+cit+cou+st+sta+hl+seid+consensus+{+eid+mtid+bb+boid+partid+sbid+paid+lineid+wag+perc+vol+tvol+wb+}+plays(pgid:+2,+limitLastSeq:+3)+{+eid+sqid+siid+gid+nam+val+tim+}+scores+{+partid+val+eid+pn+sequence+}+participants+{+eid+partid+psid+ih+rot+tr+sppil+startingPitcher+{+fn+lnam+}+source+{+...+on+Player+{+pid+fn+lnam+}+...+on+Team+{+tmid+lid+nam+nn+sn+abbr+cit+}+...+on+ParticipantGroup+{+partgid+nam+lid+participants+{+eid+partid+psid+ih+rot+source+{+...+on+Player+{+pid+fn+lnam+}+...+on+Team+{+tmid+lid+nam+nn+sn+abbr+cit+}+}+}+}+}+}+marketTypes+{+mtid+spid+nam+des+settings+{+sitid+did+alias+layout+format+template+sort+url+}+}+bettingOptions+{+boid+nam+mtid+spid+partid+}+currentLines(paid:+[20,3,10,8,9,44,29,38,16,65,92,28,83,84,82,15,35,45,54,22,18,5,36,78])+openingLines+eventGroup+{+egid+nam+}+statistics(sgid:+3)+{+val+eid+nam+partid+pid+typ+siid+sequence+}+league+{+lid+nam+rid+spid+sn+settings+{+alias+rotation+ord+shortnamebreakpoint+}+}+}+maxSequences+{+events:+eventsMaxSequence+scores:+scoresMaxSequence+currentLines:+linesMaxSequence+statistics:+statisticsMaxSequence+plays:+playsMaxSequence+}+}+}'
    r=requests.get(url, headers=headers)
    events = r.json()['data']['eventsByDateByLeagueGroup']['events']
    return events2games(events)

def scrapeNCAAB(date=""):

    if date == "":
        date = int((calendar.timegm(time.gmtime()) - 86400) * 1000)

    url = 'https://www.oddstrader.com/odds-v2/odds-v2-service?query=%7B+eventsByDateByLeagueGroup(+leagueGroups:+[%7B+mtid:+[401,+402,83],+lid:+14,+spid:+5+%7D],+showEmptyEvents:+true,+marketTypeLayout:+%22PARTICIPANTS%22,+ic:+false,+startDate:+' + str(date) + ',+timezoneOffset:+-5,+nof:+true,+hl:+true,+sort:+%7Bby:+[%22lid%22,+%22dt%22,+%22des%22],+order:+ASC%7D+)+%7B+events+%7B+eid+lid+spid+des+dt+es+rid+ic+ven+tvs+cit+cou+st+sta+hl+seid+writeingame+consensus+%7B+eid+mtid+bb+boid+partid+sbid+paid+lineid+wag+perc+vol+tvol+wb+sequence+%7D+plays(pgid:+2,+limitLastSeq:+3,+pgidWhenFinished:+-1)+%7B+eid+sqid+siid+gid+nam+val+tim+%7D+scores+%7B+partid+val+eid+pn+sequence+%7D+participants+%7B+eid+partid+psid+ih+rot+tr+sppil+startingPitcher+%7B+fn+lnam+%7D+source+%7B+...+on+Player+%7B+pid+fn+lnam+%7D+...+on+Team+%7B+tmid+lid+nam+nn+sn+abbr+cit+%7D+...+on+ParticipantGroup+%7B+partgid+nam+lid+participants+%7B+eid+partid+psid+ih+rot+source+%7B+...+on+Player+%7B+pid+fn+lnam+%7D+...+on+Team+%7B+tmid+lid+nam+nn+sn+abbr+cit+%7D+%7D+%7D+%7D+%7D+%7D+marketTypes+%7B+mtid+spid+nam+des+settings+%7B+sitid+did+alias+layout+format+template+sort+url+%7D+%7D+currentLines(paid:+[20,3,10,8,9,44,29,38,16,65,92,28,83,84,82,15,35,45,54,22,18,5,36,78])+openingLines+eventGroup+%7B+egid+nam+%7D+statistics(sgid:+3,+sgidWhenFinished:+4)+%7B+val+eid+nam+partid+pid+typ+siid+sequence+%7D+league+%7B+lid+nam+rid+spid+sn+settings+%7B+alias+rotation+ord+shortnamebreakpoint+%7D+%7D+%7D+maxSequences+%7B+events:+eventsMaxSequence+scores:+scoresMaxSequence+currentLines:+linesMaxSequence+statistics:+statisticsMaxSequence+plays:+playsMaxSequence+consensus:+consensusMaxSequence+%7D+%7D+%7D'
    r=requests.get(url, headers=headers)
    events = r.json()['data']['eventsByDateByLeagueGroup']['events']
    return events2games(events)


class Scoreboard:
    def __init__(self, sport='NBA', date=""):
        try:
            if sport == 'NBA':
                self.games = scrapeNBA(date)
            elif sport == 'NCAAB':
                self.games = scrapeNCAAB(date)
            elif sport == 'NHL':
                self.games = scrapeNHL(date)
            elif sport == 'MLB':
                self.games = scrapeMLB(date)
            elif sport == 'NFL':
                self.games = scrapeNFL(date)
        except Exception as e:
            print("An error occurred: {}".format(e))
            return
