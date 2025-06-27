from patron import Patron
from spy_item import SpyItem
from display_styles import error_msg, success_msg, warning_msg, menu_display, prompt_msg
import os, sqlite3, time, pynput, datetime
from colorama import Fore
from smtplib import SMTP
from dotenv import dotenv_values
from email.message import EmailMessage

class MainProgam():

    active_patron = None

    def __init__(self, db_name):
        self.db_name = db_name
        

    def start_program(self):
        # Start Connection To Database
        if os.path.exists(self.db_name):
            # database already exist so just set up connection and cursor
            self.db_con = sqlite3.connect(self.db_name)
            self.db_cur = self.db_con.cursor()
        else:
            # database does not exist yet so need to set up tables in addition to connection and cursor
            self.db_con = sqlite3.connect(self.db_name)
            self.db_cur = self.db_con.cursor()
            # Set up tables 
            self.db_cur.execute('CREATE TABLE patrons(name TEXT, email TEXT UNIQUE)') # adding unique on email may be overbearing and could be accomplished elsewhere
            self.db_cur.execute('CREATE TABLE targets(patron_id INTEGER, name TEXT, target_price REAL, url_id INTEGER)')
            self.db_cur.execute('CREATE TABLE spy_urls(url TEXT, tag_type TEXT, tag_idx INTEGER)')
            # Need a another table to save the dictionary that stores the logic for scraping a website for a price change
            self.db_cur.execute('CREATE TABLE tag_attrs(url_id INTEGER, key TEXT, value TEXT)')
            self.db_con.commit()
        # Run Program
        self.main_menu()
        # End Program 
        self.end_program()

    def end_program(self):
        self.db_con.close()

    def main_menu(self):
        print('Welcome The Price Drop Spy Program')
        stop_program = False
        # present main menu to see which side or program to run
        while not stop_program:
            menu_display('\nMain Menu: Select what you\'d like to do')
            menu_display('-----------------------------')
            menu_display('1) Start Spying On Items')
            menu_display('2) Use User Interface')
            menu_display('3) End Program')
            selection = self.user_input()
            if selection.strip() == '1':
                self.start_spy_session()
            elif selection.strip() == '2':
                self.run_ui()
            elif selection.strip() == '3':
                stop_program = True
                print('Stopping Price Drop Spy Program, Goodbye')
            else:
                error_msg('Invalid selection, please try again\n')

    def start_spy_session(self):
        # Used for setting up esc key to allow controlled stoping of spy session
        def exit_check(key, injected):
            if key == pynput.keyboard.Key.esc:
                global searching
                searching = False 
                # Stop listener
                return False
        # Run spy session
        with pynput.keyboard.Listener(on_press=exit_check, on_release=None) as listener:
            global searching
            searching = True
            print('Begginning Spying Session')
            search_intervals = 60*60*12 # seconds
            end_search_delay = 10 # seconds
            end_search_delay = min(end_search_delay,search_intervals)
            while searching:
                # Grab all items that are in the database
                items = self.check_current_prices()
                # for each item check if price is right for any patrons spying on the item
                for item in items:
                    [url_id, url, current_price] = item
                    # get list of patron's that are happy to pay the current price
                    patrons_items = self.find_price_is_right_items(url_id, current_price) # (rowid, patron_id, name, target_price)
                    if patrons_items:
                        # Notify each patron that their item is available for the price they want via email 
                        for item_id, patron_id, item_name, _ in patrons_items:
                            self.notify_patron_of_price_drop(patron_id, url, item_name, current_price)
                            print('Sent Email')
                            # Intialize dummy spy item to stop spying on this item for the patron 
                            spy_item = SpyItem(SCRAPE_URL=None, lookup_logic=None, target_price=0, item_name=None, db_id=item_id, db_name=self.db_name)
                            spy_item.stop_spying()
                    # check to see if item still needs to tracked, remove from database if not (remove URL and tag atrributes entirely, not just from a particular patron)
                    res = self.db_cur.execute('SELECT * FROM targets WHERE url_id=?',(url_id,))
                    if not res.fetchone():
                        # no patron is tracking this item anymore, remove it from the database
                        # delete tag attributes 
                        self.db_cur.execute("DELETE FROM tag_attrs WHERE url_id=?", (url_id,))
                        # delete url 
                        self.db_cur.execute("DELETE FROM spy_urls WHERE rowid=?", (url_id,))
                        self.db_con.commit()
                # Wait till next spy interval to check prices
                print(f'Finished search interval at {datetime.datetime.now()}')
                print(f'Next search interval will start at {datetime.datetime.fromtimestamp(time.time()+search_intervals)}')
                print(f'Press "esc" To End Session (up to a {end_search_delay} second delay)\n')
                # break up sleep time into shorter chunks so can have a reasonable delay on the end search input
                finished_interval = time.time()
                while (time.time() - finished_interval) < search_intervals:
                    if not searching:
                        break 
                    time.sleep(end_search_delay)
            listener.join()
            warning_msg('Stopping Spying Session, Returning To Main Menu')

    def check_current_prices(self):
        items = list()
        # Grab URL associated with this item
        # spy_urls(url TEXT, tag_type TEXT, tag_idx INTEGER)
        res = self.db_cur.execute("SELECT rowid, url, tag_type, tag_idx FROM spy_urls")
        for url_id, url, tag_type, tag_idx in res.fetchall():
            # Recreate a dictionary for use as the lookup logic when webscraping
            # tag_attrs(url_id INTEGER, key TEXT, value TEXT)
            res = self.db_cur.execute("SELECT key, value FROM tag_attrs WHERE url_id=?", (url_id,))
            tag_attrs = {logic[0]:logic[1] for logic in res.fetchall()}
            lookup_logic = (tag_type, tag_attrs, tag_idx)
            # create spy_item with dummy arguments so that check the current price
            spy_item = SpyItem(url, lookup_logic, target_price=0, item_name='dummy', db_id=0, db_name='dummy')
            try: 
                current_price = spy_item.check_current_price()
                items.append((url_id, url, current_price))
            except ValueError:
                # item URL is not longer valid, remove from database and notify patrons
                pass 
        return items        

    def find_price_is_right_items(self, url_id, current_price):
        # find which patron's have a target price lower or equal to the current price for this item (url)
        # targets(patron_id INTEGER, name TEXT, target_price REAL, url_id INTEGER)
        patron_items = self.db_cur.execute("SELECT rowid, patron_id, name, target_price FROM targets WHERE url_id=? ORDER BY target_price ASC",(url_id,)).fetchall()
        low = 0 
        high = len(patron_items) - 1
        right_price_idx = None
        # binary search to find the patron's who have a target price lower than the current price
        while low <= high:
            middle = (high + low) // 2
            if patron_items[middle][3] >= current_price:
                right_price_idx = middle
                high = middle - 1
                # continue searching to the left to see if there are more patron's who have their target met
            else:
                # search right to patron's who have their target met
                low = middle + 1
        # return list of items for patrons who's target price has been met
        if right_price_idx != None: 
            return patron_items[right_price_idx:]
        else:
            return None
        
    def notify_patron_of_price_drop(self,patron_id, url, item_name, current_price):
        [patron_name, patron_email] = self.db_cur.execute('SELECT name, email FROM patrons WHERE rowid=?',(patron_id,)).fetchone()
        with SMTP('smtp.gmail.com', 587) as s:
            # Set up SMTP instance
            s.starttls()
            s.login(dotenv_values('.env')['admin_email'], dotenv_values('.env')['admin_email_pw'])
            # Generate notification email
            email = EmailMessage()
            email['Subject'] = f'Hey {patron_name}! Your Spied On Item Has Hit The Price You Were Interested In!'
            email['From'] = 'Price Drop Spy <noreply@pricedrop.spy>' # gmail doesn't allow for alternative email to be displayed so noreply@pricedrop.spy will be overwritten
            email['To'] = patron_email
            message = f'{item_name} is currently available for ${current_price:.2f}\n\n'
            message += f'Purchase your item at: {url}\n\n'
            message += 'This item will no longer be spied on'
            email.set_content(message)
            # Send email notification
            s.send_message(email)

    def run_ui(self):
        stop_ui = False
        # Sign in or create an account
        while not self.active_patron and not stop_ui:
            menu_display('\nLogin Menu: Select what you\'d like to do')
            menu_display('-----------------------------')
            menu_display('1) Sign In')
            menu_display('2) Create Account')
            menu_display('3) Exit To Program Main Menu')
            selection = self.user_input()
            # Sign Into Existing Account
            if selection == '1':
                while not self.active_patron:
                    prompt_msg('Please enter the email associated with your account')
                    patron_email = self.user_input().lower()
                    if not patron_email: break # empty input returns to previous menu
                    res = self.db_cur.execute("SELECT name, email, rowid FROM patrons WHERE email=?", (patron_email,))
                    account_info = res.fetchone()
                    if account_info:
                        patron = Patron(*account_info, self.db_name)
                        self.active_patron = patron
                        success_msg(f'Welcome back {self.active_patron.name}, successfully logged in')  
                    else:
                        error_msg(f'There is no patron account associated with {patron_email}')
                        menu_display('Would you like to try a different email or return to the login menu?')
                        menu_display('1) Different Email')
                        menu_display('2) Login Menu')
                        selection = self.user_input()
                        if selection == '2':
                            break
            # Create A New Account 
            elif selection == '2':
                prompt_msg('Please enter your name')
                patron_name = self.user_input()
                if not patron_name: continue # empty input returns to previous menu
                while not self.active_patron:
                    prompt_msg('Please enter your email')
                    patron_email = self.user_input()
                    if '@' in patron_email:
                        # check to see if email is already asssociated with anther patron account 
                        res = self.db_cur.execute("SELECT email FROM patrons WHERE email=?", (patron_email,))
                        if not res.fetchone():
                            self.db_cur.execute("INSERT INTO patrons VALUES (?, ?)", (patron_name, patron_email))
                            self.db_con.commit()
                            patron = Patron(patron_name, patron_email, self.db_cur.lastrowid, self.db_name)
                            self.active_patron = patron
                            success_msg(f'Welcome {self.active_patron.name}, successfully created account with email {self.active_patron.email}')
                            print('Name And Email On Your Account Can Be Updated On The Patron Menu If Needed')
                        else:
                            error_msg(f'Already a patron account associated with {patron_email}')
                            print('Returning To Login Menu')
                            break
                    else:
                        error_msg('Invalid email, please try again')
            elif selection == '3':
                stop_ui = True
            else:
                error_msg('Invalid selection, please try again\n')
        # Display User Interface Menu
        while not stop_ui:
            menu_display('\nPatron Menu: Select what you\'d like to do')
            menu_display('-----------------------------')
            menu_display('1) Add Item To Spy On')
            menu_display('2) See Current Price Of Items')
            menu_display('3) Update Target Price Of Items')
            menu_display('4) Remove Item That Is Being Spied On')
            menu_display('5) Update Account Info')
            menu_display('6) Exit To Program Main Menu')
            selection = self.user_input()
            # Add Item To Patron Account To Spy On
            if selection == '1':
                prompt_msg('Enter URL for item that you want to spy on')
                url = self.user_input()
                if not url: continue # empty input returns to previous menu
                if SpyItem.valid_url(url):
                    prompt_msg('Enter Name Of Item (This Is What You Refer To The Item As)')
                    item_name = self.user_input()
                    prompt_msg('Enter Current Price Of The Item')
                    current_price = self.user_input().strip('$')
                    prompt_msg('Enter Maximum Price That You Want To Pay')
                    target_price = self.user_input().strip('$')
                    # Check if this URL already exist in the database
                    # spy_urls(url TEXT, tag_type TEXT, tag_idx INTEGER)
                    url_id = self.db_cur.execute("SELECT rowid FROM spy_urls WHERE url=?", (url,)).fetchone()
                    if not url_id:
                        lookup_logic = SpyItem.get_tag_lookup_logic(url, current_price) 
                        if lookup_logic:      
                            # spy_urls(url TEXT, tag_type TEXT, tag_idx INTEGER)
                            self.db_cur.execute("INSERT INTO spy_urls VALUES (?, ?, ?)", (url, lookup_logic[0], lookup_logic[2]))
                            url_id = self.db_cur.lastrowid
                            # tag_attrs(url_id INTEGER, key TEXT, value TEXT)
                            logic_entries = [(url_id, attr, value) for attr, value in lookup_logic[1].items()]
                            self.db_cur.executemany("INSERT INTO tag_attrs VALUES (?, ?, ?)", logic_entries)
                            # targets(patron_id INTEGER, name TEXT, target_price REAL, url_id INTEGER)
                            self.db_cur.execute("INSERT INTO targets VALUES (?, ?, ?, ?)", (self.active_patron.id, item_name, float(target_price), url_id))
                            self.db_con.commit()
                            success_msg(f'{item_name} Has Successfully Been Added To Your Account For Price Spying')
                        else:
                            warning_msg('Inputted Current Price Was Not Found On The Webpage Given')
                            warning_msg(f'Are you sure that the current price of the {item_name} is ${current_price}?')
                            print('Returning To Patron Menu')
                    else: 
                        # targets(patron_id INTEGER, name TEXT, target_price REAL, url_id INTEGER)
                        if self.db_cur.execute("SELECT * FROM targets WHERE url_id=?", url_id).fetchone():
                            warning_msg('You Are Already Spying On This Item, Use Option 3 On Patron Menu To Update Target Price')
                        else:
                            # targets(patron_id INTEGER, name TEXT, target_price REAL, url_id INTEGER)
                            self.db_cur.execute("INSERT INTO targets VALUES (?, ?, ?, ?)", (self.active_patron.id, item_name, float(target_price), url_id[0]))
                            self.db_con.commit()
                            success_msg(f'{item_name} Has Successfully Been Added To Your Account For Price Spying')
                else:
                    if 'https://' in url:
                        domain_name = url.split('/')[2]
                        warning_msg(f'{domain_name.upper()} Does Not Allow Price Spying On Their Website')
                    else:
                        error_msg('Invalid URL, Returning To Patron Menu')
            # Display Current Items Being Tracked And Their Current Price
            elif selection == '2':
                print('Current Price Of Items Being Spied On')
                print('-------------------------------------')
                self.active_patron.display_items()
            # Display Items For Patron To Select To Update Target Price On
            elif selection == '3':
                current_items = self.active_patron.grab_items()               
                if current_items:
                    print('Current Items Being Spied On')
                    print('----------------------------------------------------')
                    self.active_patron.display_items(show_target=True, item_list=current_items)
                    prompt_msg('\nSelect Item That You Want To Update Target Price For')
                    item_selection = self.user_input()
                    if not item_selection: continue # empty input returns to previous menu
                    if item_selection.isnumeric():
                        item_selection = int(item_selection)
                        if item_selection > 0 and item_selection <= len(current_items):
                            item = current_items[item_selection-1]
                            print(f'Update Target Price For {item.item_name}')
                            print('----------------------------------------------------')
                            print(f'Current Target Price is ${item.target_price}')
                            prompt_msg('Input New Target Price')
                            new_price = '-'
                            while not new_price.isnumeric():
                                new_price = self.user_input().strip('$')
                            item.update_target_price(new_price)
                            success_msg('Updated Target Price On Item')
                        else:
                            error_msg('Invalid Input, Returning To Patron Menu')
                    else:
                        error_msg('Invalid Input, Returning To Patron Menu')
                else:
                    warning_msg('No Items Are Currently Being Spied On')
            # Remove Item From Being Spied On
            elif selection == '4':
                current_items = self.active_patron.grab_items()               
                if current_items:
                    print('Current Items Being Spied On')
                    print('----------------------------------------------------')
                    self.active_patron.display_items(show_target=False, item_list=current_items)
                    prompt_msg('\nSelect Item That You No Longer Want To Spy On')
                    item_selection = self.user_input()
                    if not item_selection: continue # empty input returns to previous menu
                    if item_selection.isnumeric():
                        item_selection = int(item_selection)
                        if item_selection > 0 and item_selection <= len(current_items):
                            item = current_items[item_selection-1]
                            prompt_msg(f'Are You Sure That You No Longer Want To Spy On {item.item_name}? (y/n)')
                            confirmation = self.user_input().lower()
                            if confirmation.startswith('y'):
                                item.stop_spying()
                                success_msg(f'No Longer Spying On {item.item_name}')
                        else:
                            error_msg('Invalid Input, Returning To Patron Menu')
                    else:
                        error_msg('Invalid Input, Returning To Patron Menu')
                else:
                    warning_msg('No Items Are Currently Being Spied On')
            # Update User Account Info
            elif selection == '5':
                print('Current Account Information')
                print('----------------------------------------------------')
                print(f'Name: {self.active_patron.name}')
                print(f'Email: {self.active_patron.email}')
                menu_display('Account Update Menu: Select what you\'d like to do')
                menu_display('----------------------------------------------------')
                menu_display('1) Update Name')
                menu_display('2) Update Email')
                selection = self.user_input()
                if not selection: continue # empty input returns to previous menu
                if selection == '1':
                    prompt_msg('Input Your Updated Name')
                    new_name = self.user_input()
                    self.active_patron.update_name(new_name)
                    success_msg(f'Successfully Updated Your Name To {new_name}')
                elif selection == '2':
                    new_email = ''
                    prompt_msg('Input A New Email Address For Your Account')
                    while '@' not in new_email:
                        new_email = self.user_input().lower()
                    try:
                        self.active_patron.update_email(new_email)
                        success_msg(f'Successfully Updated The Email On Your Account To {new_email}')
                    except sqlite3.IntegrityError:
                        error_msg(f'Already a patron account associated with {new_email}')
                else:
                    error_msg('Invalid Input, Returningh To Patron Menu')
            elif selection == '6':
                stop_ui = True
        # Exit User Interface
        self.active_patron = None
        print('Exiting User Interface and Returning To Program Main Menu')

    def user_input(self):
        # this is only used in UI part of program
        if self.active_patron:
            selection = input((Fore.CYAN + f'{self.active_patron.name} > ' + Fore.RESET)).strip()
        else:
            selection = input((Fore.CYAN + '> ' + Fore.RESET)).strip()
        return selection   

def main(debug=False):
    db_name = 'db.sqlite3'
    price_drop_spy = MainProgam(db_name)
    price_drop_spy.start_program()
    if debug:
        con = sqlite3.connect(db_name)
        cur = con.cursor()
        table_names = ['patrons','targets', 'spy_urls', 'tag_attrs']
        for name in table_names:
            print(f'Table: {name}')
            res = cur.execute(f'SELECT * FROM {name}') # not supposed to this but here we are since it's just for debugging
            for item in res.fetchall():
                print(item) 
            print()
        con.close()       

if __name__=='__main__':
    debug_flag = False
    main(debug=debug_flag)