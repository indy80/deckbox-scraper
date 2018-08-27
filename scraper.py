import urllib2, json, os, unicodedata, sys
from collections import OrderedDict

save_folder = 'decks/'
maximum_tries = 10
ignore_sets = ['inventory', 'tradelist', 'wishlist']
valid_count = [58, 59, 60, 61, 62, 98, 99, 100, 101, 102]

get_sets = 'https://deckbox-api.herokuapp.com/api/users/%s/sets/'
get_sets_page = 'https://deckbox-api.herokuapp.com/api/users/%s/sets/?page=%d'
get_set = 'https://deckbox-api.herokuapp.com/api/users/%s/sets/%s'

if len(sys.argv) < 2:
    print 'Specify a user id.'
    quit()

user_id = sys.argv[1]

class Deck:
    def __init__(self, name, isCommander):
        self.Name = name
        self.IsCommander = isCommander
        self.Mainboard = OrderedDict()
        self.Sideboard = OrderedDict()

    def AddCard(self, count, name, isMainboard):
        if isinstance(name, unicode):
            name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore')
        if (isMainboard):
            if not name in self.Mainboard:
                self.Mainboard[name] = 0
            self.Mainboard[name] += count
        else:
            if not name in self.Sideboard:
                self.Sideboard[name] = 0
            self.Sideboard[name] += count
                
    def Save(self, folder):
        if self.IsCommander:
            folder = folder + '/commander'
        if not os.path.exists(folder):
            os.mkdir(folder)
        f = open(folder + '/' + self.Name + '.txt', 'w+')
        for c in self.Mainboard:
            f.write('%s %s\n' % (self.Mainboard[c], c))
        if len(self.Sideboard) > 0:
            f.write('\nSideboard:\n\n')
            for c in self.Sideboard:
                f.write('%s %s\n' % (self.Sideboard[c], c))
        f.close()

def DebugLog(status, tries, deck_name, end):
    #print('\x1b[6;30;42m' + 'Success!' + '\x1b[0m')
    if tries > 0:
        sys.stdout.write('\r  [%10s] %30s (%d)  ' % (status, deck_name, tries + 1))
    else:
        sys.stdout.write('\r  [%10s] %30s       ' % (status, deck_name))
    sys.stdout.flush()
    if end:
        sys.stdout.write("\n")

def Run():
    set_result = urllib2.urlopen(get_sets % user_id).read()
    sets = json.loads(set_result)

    print 'found %d decks in %d pages ' % (sets['count'], sets['total_pages'])

    current_page = 0
    total_pages = sets['total_pages']
    skipped_decks = []
    downloaded_count = 0

    while not current_page == total_pages:

        set_result = urllib2.urlopen(get_sets_page % (user_id, current_page + 1)).read()
        sets = json.loads(set_result)

        print 'downloading page %d' % current_page

        for set in sets['items']:
            deck_name = set['name']
            if not deck_name in ignore_sets:
                success = False
                tries = 0
                while not success and tries < maximum_tries:
                    try:
                        DebugLog('checking', tries, deck_name, False)
                        deck_result = urllib2.urlopen(get_set % (user_id, set['id'])).read()
                        success = True
                        deck = json.loads(deck_result)
                        if 'mainboard' in deck:
                            card_count = deck['mainboard']['total']
                            if card_count in valid_count:
                                d = Deck(deck_name, card_count >= 90)
                                for card in deck['mainboard']['cards']:
                                    d.AddCard(card['count'], card['name'], True)
                                if 'sideboard' in deck:
                                    for card in deck['sideboard']['cards']:
                                        d.AddCard(card['count'], card['name'], False)
                                downloaded_count += 1
                                d.Save(save_folder)
                                DebugLog('done', tries, deck_name, True)
                            else:
                                skipped_decks.append(deck_name)
                                DebugLog('skipped', tries, deck_name, True)
                                
                    except urllib2.URLError:
                        tries += 1
                        pass

                if not success:
                    DebugLog('error', tries, deck_name, True)

        current_page += 1

    print 'skipped %d decks ' % len(skipped_decks)
    f = open(save_folder + '_skipped.txt', 'w+')
    for skipped_deck in skipped_decks:
        f.write(skipped_deck + '\n')
    f.close()

    print 'downloaded %d decks ' % downloaded_count 

Run()