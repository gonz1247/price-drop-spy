from bs4 import BeautifulSoup
import requests, sqlite3

class SpyItem:

    def __init__(self, SCRAPE_URL, lookup_logic, target_price, item_name, db_id, db_name):
        self.url = SCRAPE_URL
        self.logic = lookup_logic
        self.target_price = float(target_price)
        self.item_name = item_name
        self.id = db_id
        self.db_name = db_name

    def check_current_price(self):
        # Verify that URL is still valid before attemping to scrape it
        if SpyItem.valid_url(self.url):
            soup = BeautifulSoup(requests.get(self.url).text, 'lxml', multi_valued_attributes=None)
        else:
            raise ValueError(f'{self.url} no longer exists. This item may no longer be sold.')
        tag = soup.find_all(self.logic[0],**self.logic[1])[self.logic[2]]
        price = list()
        for char in tag.text:
            # only grab numbers and decimals from tag text (will strip out any extra decimals that may be leading or trailing the price)
            if char.isnumeric() or char == '.':
                price.append(char)
        current_price = ''.join(price).strip('.')
        return float(current_price)
           
    def update_target_price(self, target_price):
        # Update in local instance
        self.target_price = float(target_price)
        # update in database 
        con = sqlite3.connect(self.db_name)
        cur = con.cursor()
        # targets(patron_id INTEGER, name TEXT, target_price REAL, url_id INTEGER)
        cur.execute("UPDATE targets set target_price=? WHERE rowid=?", (self.target_price, self.id))
        con.commit()
        con.close()

    def stop_spying(self):
        # no need to update locally since this instance will just not be able to be recreated anymore
        # update in database 
        con = sqlite3.connect(self.db_name)
        cur = con.cursor()
        # targets(patron_id INTEGER, name TEXT, target_price REAL, url_id INTEGER)
        cur.execute("DELETE FROM targets WHERE rowid=?", (self.id,))
        con.commit()
        con.close()
        # note that removal of URL if no other patrons are spying on this item now is handled at the main program level

    @staticmethod
    def get_tag_lookup_logic(SCRAPE_URL, current_price):    
        # Verify that URL is valid before attemping to scrape it 
        if SpyItem.valid_url(SCRAPE_URL):
            soup = BeautifulSoup(requests.get(SCRAPE_URL).text, 'lxml', multi_valued_attributes=None)
        else:
            # In practice will check if URL is valid prior to calling this method  
            raise ValueError(f'{SCRAPE_URL} is not valid URL')
         
        # Strip trailing zeros on price (user may add this even if the website only has the whole dollar shown)
        if current_price.endswith('.00'):
            current_price = current_price[0:-3]

        # Find tag that is best representation of the price inputted
        tag_options = soup.body.find_all(lambda tag: current_price in tag.text)
        if tag_options:
            tag_shortest_text = tag_options[0]
            for tag in tag_options:
                # Assume that the price will be self contained and therefore short
                # # Want to grab the tag that simply has the price, not one that has a the story of why it's that price
                # # If tag has text of same length then likely a child of previos tag identified
                if len(tag.text) <= len(tag_shortest_text.text):
                    tag_shortest_text = tag

            # Tag may be used multiple times on page so check which instance of the tag has the info we want
            correct_tag_options = soup.find_all(tag_shortest_text.name,**tag_shortest_text.attrs)
            for idx, tag in enumerate(correct_tag_options):
                price = list()
                for char in tag.text:
                    # only grab numbers and decimals from tag text (will strip out any extra decimals that may be leading or trailing the price)
                    if char.isnumeric() or char == '.':
                        price.append(char)
                verified_price = ''.join(price).strip('.')
                # also strip out trailing zeros since current_price strip theirs earlier 
                if verified_price.endswith('.00'):
                    verified_price = verified_price[:-3]
                # Let user know if you were able to verify the price or not
                if current_price == verified_price:
                    return (tag.name, tag.attrs, idx)
        # Tag with price was not found or logic created was not reliable enough 
        # raise NotImplementedError('Current Web Scraping Logic Was Not Able To Reliably Scrape URL For The Item Price')
        # raise ValueError('Inputted Current Price Was Not Found On The Webpage Given')
        return None
    
    @staticmethod
    def valid_url(SCRAPE_URL):
        # Verify that can get a valid response from the URL
        try:
            html = requests.get(SCRAPE_URL)
            if html.ok:
                return True
            else:
                return False
        except:
            return False
    

if __name__ == '__main__':

    # Get Info For Web Scraping
    SCRAPE_URL = 'https://www.nintendo.com/us/retail-offers/#switch2-bundle'
    current_price = '499.99'
    # SCRAPE_URL = 'https://www.nike.com/t/killshot-2-leather-mens-shoes-1lEPvIbm/432997-070'
    # current_price = '90.00'

    if SpyItem.valid_url(SCRAPE_URL):
        lookup_logic = SpyItem.get_tag_lookup_logic(SCRAPE_URL,current_price)
        item = SpyItem(SCRAPE_URL, lookup_logic, 450, 'Switch 2', 'dummy', 'dummy')
        print(item.check_current_price())
        print(item.check_price_is_right())
    else:
        print('Was not able to access URL')