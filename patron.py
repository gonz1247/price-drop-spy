from spy_item import SpyItem
from smtplib import SMTP
from dotenv import dotenv_values
from email.message import EmailMessage
import sqlite3


class Patron:

    def __init__(self, name, email, db_id, db_name):
        self.update_name(name)
        self.update_email(email)
        self.id = db_id
        self.db_name = db_name
        
    def update_name(self, name):
        if isinstance(name, str):
            self.name = name
        else:
            raise TypeError('Patron name must be entered as a string') 
        
    def update_email(self, email):
        if isinstance(email, str):
            if '@' in email:
                self.email = email
            else:
                raise ValueError('Invalid email address')
        else:
            raise TypeError('Patron email must be entered as a string') 
        
    def grab_items(self):
        con = sqlite3.connect(self.db_name)
        cur = con.cursor()
        # Grab all items associated with the patron
        # patron_id INTEGER, name TEXT, url TEXT, tag_type TEXT, target_price REAL
        res = cur.execute("SELECT rowid, name, url, tag_type, target_price FROM items WHERE patron_id=?", (self.id,))
        current_items = list()
        for item in res.fetchall():
            # Recreate a dictionary for use as the lookup logic when webscraping
            # item_id INTEGER, key TEXT, value TEXT
            [item_id, item_name, url, tag_type, target_price] = item
            res = cur.execute("SELECT key, value FROM logic WHERE item_id=?", (item_id,))
            tag_attrs = {logic[0]:logic[1] for logic in res.fetchall()}
            lookup_logic = (tag_type, tag_attrs)
            spy_item = SpyItem(url, lookup_logic, target_price, item_name)
            current_items.append(spy_item)
        return current_items
    
    def display_items(self, show_target=False):
        current_items = self.grab_items()
        for idx, spy_item in enumerate(current_items):
            display_text = f'{idx+1}) {spy_item.item_name} is currently ${spy_item.check_current_price():.2f}'
            if show_target: 
                display_text += f', target price is ${spy_item.target_price:.2f}'
            print(display_text)
    
    def notify_of_price_drop(self, spy_item):
        with SMTP('smtp.gmail.com', 587) as s:
            # Set up SMTP instance
            s.starttls()
            s.login(dotenv_values('.env')['admin_email'], dotenv_values('.env')['admin_email_pw'])
            # Generate notification email
            email = EmailMessage()
            email['Subject'] = f'Hey {self.name}! Your Spied On Item Has Hit The Price You Were Interested In!'
            email['From'] = 'Price Drop Spy <noreply@pricedrop.spy>' # gmail doesn't allow for alternative email to be displayed so noreply@pricedrop.spy will be overwritten
            email['To'] = self.email
            message = f'{spy_item.item_name} is currently available for ${spy_item.check_current_price():.2f}\n\n'
            message += f'Purchase your item at: {spy_item.url}'
            email.set_content(message)
            # Send email notification
            s.send_message(email)

if __name__ == '__main__':
    # Set Up Item 
    SCRAPE_URL = 'https://shop.lululemon.com/p/men-ss-tops/Organic-Cotton-Classic-Fit-T-Shirt/_/prod11680617?color=0002'
    current_price = '58'
    if SpyItem.valid_url(SCRAPE_URL):
        lookup_logic = SpyItem.get_tag_lookup_logic(SCRAPE_URL,current_price)
        item = SpyItem(SCRAPE_URL, lookup_logic, 40, 'Lulu Shirt')
        p = Patron('Gonzo', dotenv_values('.env')['admin_email'], db_id=-1, db_name='dummy')
        p.notify_of_price_drop(item)
        
    