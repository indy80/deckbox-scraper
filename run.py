import os
import requests
import argparse
from bs4 import BeautifulSoup

parser = argparse.ArgumentParser(description="Srap deckbox.org all decks")
parser.add_argument("username", help="deckbox username")
parser.add_argument("--output", help="output dir", default="./decks")
args = parser.parse_args()

request = requests.get("https://deckbox.org/users/%s" % args.username) 
soup = BeautifulSoup(request.content, "html.parser")
decks = soup.find_all("li", class_="submenu_entry deck")
if not os.path.isdir(args.output):
    os.mkdir(args.output)
print("Found %d decks" % len(decks))
for deck in decks:
    id = deck.get("id")
    id = id.replace("deck_", "")    
    name = deck.find("a", class_="simple")
    name = name.get("data-title")
    
    request = requests.get("https://deckbox.org/sets/%s/export" % id) 
    soup = BeautifulSoup(request.content, "html.parser")
    body = soup.find("body")
    decklist = body.get_text("\n", strip=True)
    with open("%s/%s.txt" % (args.output, name), 'w') as f:
        print("Saving %s" % name)
        f.write(decklist)
if len(decks) > 1:
    print("Saved %d decks to to '%s'" % (len(decks), args.output))
