import urllib2, json, os, unicodedata
from sys import stdout

user_id = 'indy'
save_folder = 'decks/'
maximum_tries = 10

get_sets = 'https://deckbox-api.herokuapp.com/api/users/%s/sets/'
get_sets_page = 'https://deckbox-api.herokuapp.com/api/users/%s/sets/?page=%d'
get_set = 'https://deckbox-api.herokuapp.com/api/users/%s/sets/%s'

ignore_sets = {'inventory', 'tradelist','wishlist'}
valid_count = {60, 100}

def debug_log(status, tries, deck_name, end):
    #print('\x1b[6;30;42m' + 'Success!' + '\x1b[0m')
    if tries > 0:
        stdout.write('\r  [%10s] %30s (%d)  ' % (status, deck_name, tries + 1))
    else:
        stdout.write('\r  [%10s] %30s       ' % (status, deck_name))
    stdout.flush()
    if end:
        stdout.write("\n")

if not os.path.exists(save_folder):
   os.mkdir(save_folder)
if not os.path.exists(save_folder + 'commander'):
   os.mkdir(save_folder + 'commander')

set_result = urllib2.urlopen(get_sets % user_id).read()
sets = json.loads(set_result)

print 'found %d decks in %d pages ' % (sets['count'], sets['total_pages'])

done = False
current_page = 0
total_pages = sets['total_pages']
download_count = 0
skipped_decks = []

while not done:

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
                    debug_log('checking', tries, deck_name, False)
                    deck_result = urllib2.urlopen(get_set % (user_id, set['id'])).read()
                    success = True
                    deck = json.loads(deck_result)
                    if 'mainboard' in deck:
                        card_count = deck['mainboard']['total']
                        if card_count in valid_count:
                            folder = save_folder if card_count < 100 else save_folder + 'commander/'
                            debug_log('downloading', tries, deck_name, False)
                            f = open(folder + deck_name + '.txt', 'w+')
                            for card in deck['mainboard']['cards']:
                                normalized_card_name = unicodedata.normalize('NFKD', card['name']).encode('ascii', 'ignore')
                                f.write('%s %s\n' % (card['count'], normalized_card_name))
                            f.close()
                            debug_log('done', tries, deck_name, True)
                            download_count = download_count + 1
                        else:
                            skipped_decks.append(deck_name)
                            debug_log('skipped', tries, deck_name, True)
                except urllib2.URLError:
                    tries += 1
                    pass
            if not success:
                debug_log('error', tries, deck_name, True)

    current_page += 1
    done = current_page == total_pages

print 'skipped %d decks ' % len(skipped_decks)
f = open(folder + '_skipped.txt', 'w+')
for skipped_deck in skipped_decks:
    f.write(skipped_deck)
f.close()

print 'downloaded %d decks ' % download_count 