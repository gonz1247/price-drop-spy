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
            raise ValueError(f'{self.url} no longer exists. This item may not longer be sold.')
        tag = soup.find(self.logic[0],**self.logic[1])
        price = list()
        for char in tag.text:
            # only grab numbers and decimals from tag text (will strip out any extra decimals that may be leading or trailing the price)
            if char.isnumeric() or char == '.':
                price.append(char)
        current_price = ''.join(price).strip('.')
        return float(current_price)
    
    def check_price_is_right(self):
        if self.check_current_price() <= self.target_price:
            return True
        else:
            return False
        
    def update_target_price(self, target_price):
        # Update in local instance
        self.target_price = float(target_price)
        # update in database 
        con = sqlite3.connect(self.db_name)
        cur = con.cursor()
        # Grab all items associated with the patron
        # patron_id INTEGER, name TEXT, url TEXT, tag_type TEXT, target_price REAL
        cur.execute("UPDATE items set target_price=? WHERE rowid=?", (self.target_price, self.id))
        con.commit()
        con.close()

    def update_item_name(self, item_name):
        self.item_name = item_name

    @staticmethod
    def get_tag_lookup_logic(SCRAPE_URL, current_price):    
        # Verify that URL is valid before attemping to scrape it 
        if SpyItem.valid_url(SCRAPE_URL):
            soup = BeautifulSoup(requests.get(SCRAPE_URL).text, 'lxml', multi_valued_attributes=None)
        else:
            # In practice will check if URL is valid prior to calling this method  
            raise ValueError(f'{SCRAPE_URL} is not valid URL')

        # Find tag that is best representation of the price inputted
        tag_options = soup.body.find_all(lambda tag: current_price in tag.text)
        if tag_options:
            tag_shortest_text = tag_options[0]
            correct_tag_options = list()
            for tag in tag_options:
                # Assume that the price will be self contained and therefore short
                # # Want to grab the tag that simply has the price, not one that has a the story of why it's that price
                if len(tag.text) < len(tag_shortest_text.text):
                    tag_shortest_text = tag
                    correct_tag_options = [tag]
                elif len(tag.text) == len(tag_shortest_text.text):
                    # If tag has text of same length then likely a child of previos tag identified
                    # # Will check all tag to which one was reliably can get the price  
                    correct_tag_options.append(tag)

            # Verify that identifed tag(s) actually have the right price/can be used to reliably to get the price
            for tag in correct_tag_options:
                correct_tag = soup.find(tag.name,**tag.attrs)
                price = list()
                for char in correct_tag.text:
                    # only grab numbers and decimals from tag text (will strip out any extra decimals that may be leading or trailing the price)
                    if char.isnumeric() or char == '.':
                        price.append(char)
                verified_price = ''.join(price).strip('.')
                # Let user know if you were able to verify the price or not
                if current_price == verified_price:
                    return (tag.name, tag.attrs)
        # Tag with price was not found or logic created was not reliable enough 
        # raise NotImplementedError('Current Web Scraping Logic Was Not Able To Reliably Scrape URL For The Item Price')
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
    SCRAPE_URL = 'https://www.nike.com/t/killshot-2-leather-mens-shoes-1lEPvIbm/HM9431-001?nikemt=true&cp=54011862001_search_--g-21728772664-171403009167--c-1015651687-00197859044818&dplnk=member&gad_source=1&gad_campaignid=21728772664&gbraid=0AAAAADy86kOsh9txv0At5foYSBh1PKgh2&gclid=Cj0KCQjwmK_CBhCEARIsAMKwcD42_Q8_DvZjKSqoRPxGsbbizPOGjqJxcmOwd3WzISxWOaBes6b6OMQaAnWxEALw_wcB&gclsrc=aw.ds'
    current_price = '58.97'

    if SpyItem.valid_url(SCRAPE_URL):
        lookup_logic = SpyItem.get_tag_lookup_logic(SCRAPE_URL,current_price)
        item = SpyItem(SCRAPE_URL, lookup_logic, 40, 'Nike Shoes')
        print(item.check_current_price())
        print(item.check_price_is_right())