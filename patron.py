from spy_item import SpyItem
from smtplib import SMTP
from dotenv import dotenv_values
from email.message import EmailMessage


class Patron:

    spy_items = list()
    _spy_items_urls = set()

    def __init__(self, name, email, db_id):
        self.update_name(name)
        self.update_email(email)
        self.id = db_id
        
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
        
    def add_spy_item(self, spy_item):
        if isinstance(spy_item, SpyItem):
            if spy_item.url not in self._spy_items_urls:
                self.spy_items.append(spy_item)
                self._spy_items_urls.add(spy_item.url)
            else:
                raise ValueError('This Item Is Already Being Spied On')
    
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
            message = f'{spy_item.item_name} is currently available for ${spy_item.check_current_price()}\n\n'
            message += f'Purchase your item at: {spy_item.url}'
            email.set_content(message)
            # Send email notification
            s.send_message(email)

if __name__ == '__main__':
    # Set Up Item 
    SCRAPE_URL = 'https://www.nike.com/t/killshot-2-leather-mens-shoes-1lEPvIbm/HM9431-001?nikemt=true&cp=54011862001_search_--g-21728772664-171403009167--c-1015651687-00197859044818&dplnk=member&gad_source=1&gad_campaignid=21728772664&gbraid=0AAAAADy86kOsh9txv0At5foYSBh1PKgh2&gclid=Cj0KCQjwmK_CBhCEARIsAMKwcD42_Q8_DvZjKSqoRPxGsbbizPOGjqJxcmOwd3WzISxWOaBes6b6OMQaAnWxEALw_wcB&gclsrc=aw.ds'
    current_price = '58.97'
    from spy_item import get_tag_lookup_logic
    lookup_logic = get_tag_lookup_logic(SCRAPE_URL,current_price)
    item = SpyItem(SCRAPE_URL, lookup_logic, 40, 'Nike Shoes')
    p = Patron('Gonzo', dotenv_values('.env')['admin_email'])
    p.notify_of_price_drop(item)
        
    