from spy_item import SpyItem
import sqlite3


class Patron:

    def __init__(self, name, email, db_id, db_name):
        self.name = name
        self.email = email
        self.id = db_id
        self.db_name = db_name
        
    def update_name(self, name):
        # update locally
        self.name = name
        # update in database 
        con = sqlite3.connect(self.db_name)
        cur = con.cursor()
        # patrons(name TEXT, email TEXT UNIQUE)
        cur.execute("UPDATE patrons set name=? WHERE rowid=?", (self.name, self.id))
        con.commit()
        con.close()
        
    def update_email(self, email):
        # update locally
        self.email = email
        # update in database 
        con = sqlite3.connect(self.db_name)
        cur = con.cursor()
        # patrons(name TEXT, email TEXT UNIQUE)
        cur.execute("UPDATE patrons set email=? WHERE rowid=?", (self.email, self.id))
        con.commit()
        con.close()
        
        
    def grab_items(self):
        con = sqlite3.connect(self.db_name)
        cur = con.cursor()
        # Grab all items associated with the patron
        # targets(patron_id INTEGER, name TEXT, target_price REAL, url_id INTEGER)
        res = cur.execute("SELECT rowid, name, target_price, url_id FROM targets WHERE patron_id=?", (self.id,))
        current_items = list()
        for item in res.fetchall():
            # Unpack database query
            [item_id, item_name, target_price, url_id] = item
            # Grab URL associated with this item
            # spy_urls(url TEXT, tag_type TEXT, tag_idx INTEGER)
            res = cur.execute("SELECT url, tag_type, tag_idx FROM spy_urls WHERE rowid=?", (url_id,))
            [url, tag_type, tag_idx] = res.fetchone()
            # Recreate a dictionary for use as the lookup logic when webscraping
            # tag_attrs(url_id INTEGER, key TEXT, value TEXT)
            res = cur.execute("SELECT key, value FROM tag_attrs WHERE url_id=?", (url_id,))
            tag_attrs = {logic[0]:logic[1] for logic in res.fetchall()}
            lookup_logic = (tag_type, tag_attrs, tag_idx)
            spy_item = SpyItem(url, lookup_logic, target_price, item_name, item_id, self.db_name)
            current_items.append(spy_item)
        con.close()
        return current_items
    
    def display_items(self, show_target=False, item_list=None):
        if not item_list:
            item_list = self.grab_items()
        for idx, spy_item in enumerate(item_list):
            display_text = f'{idx+1}) {spy_item.item_name} is currently ${spy_item.check_current_price():.2f}'
            if show_target: 
                display_text += f', target price is ${spy_item.target_price:.2f}'
            print(display_text)
    
if __name__ == '__main__':
    # Set Up Item 
    SCRAPE_URL = 'https://shop.lululemon.com/p/men-ss-tops/Organic-Cotton-Classic-Fit-T-Shirt/_/prod11680617?color=0002'
    current_price = '58'
    if SpyItem.valid_url(SCRAPE_URL):
        lookup_logic = SpyItem.get_tag_lookup_logic(SCRAPE_URL,current_price)
        item = SpyItem(SCRAPE_URL, lookup_logic, 40, 'Lulu Shirt', db_id=-1, db_name='dummy')
        print(item.check_current_price())