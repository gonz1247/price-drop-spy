from patron import Patron
from spy_item import SpyItem
import os, sqlite3

class MainProgam():

    active_patron = None

    # TODO: Add coloring to messages and input prompts 
    def __init__(self, db_name):
        if os.path.exists(db_name):
            # database already exist so just set up connection and cursor
            self.db_name = db_name
            self.db_con = sqlite3.connect(db_name)
            self.db_cur = self.db_con.cursor()
        else:
            # database does not exist yet so need to set up tables in addition to connection and cursor
            self.db_name = db_name
            self.db_con = sqlite3.connect(db_name)
            self.db_cur = self.db_con.cursor()
            # Set up tables 
            self.db_cur.execute('CREATE TABLE patrons(name TEXT, email TEXT UNIQUE)') # adding unique on email may be overbearing and could be accomplished elsewhere
            self.db_cur.execute('CREATE TABLE items(patron_id INTEGER, name TEXT, url TEXT, tag_type TEXT, tag_idx INTEGER, target_price REAL)')
            # Need a third table to save the dictionary that stores the logic for scraping a website for a price change
            self.db_cur.execute('CREATE TABLE logic(item_id INTEGER, key TEXT, value TEXT)')
            self.db_con.commit()

    def start_program(self):
        self.main_menu()
        self.end_program()

    def end_program(self):
        self.db_con.close()

    def main_menu(self):
        print('Welcome The Price Drop Spy Program')
        stop_program = False
        # present main menu to see which side or program to run
        while not stop_program:
            print('\nMain Menu: Select what you\'d like to do')
            print('-----------------------------')
            print('1) Start Spying On Items')
            print('2) Use User Interface')
            print('3) End Program')
            selection = input('> ')
            if selection.strip() == '1':
                self.start_spying()
            elif selection.strip() == '2':
                self.run_ui()
            elif selection.strip() == '3':
                stop_program = True
                print('Stopping Price Drop Spy Program, Goodbye')
            else:
                print('Invalid selection, please try again\n')

    def start_spying(self):
        # TODO: Work on spying functionality. Determine if can search items on behalf of multiples patrons at a time
        pass

    def run_ui(self):
        stop_ui = False
        # Sign in or create an account
        while not self.active_patron and not stop_ui:
            print('\nLogin Menu: Select what you\'d like to do')
            print('-----------------------------')
            print('1) Sign In')
            print('2) Create Account')
            print('3) Exit To Program Main Menu')
            selection = self.user_input()
            # Sign Into Existing Account
            if selection == '1':
                while not self.active_patron:
                    print('Please enter the email associated with your account')
                    patron_email = input('> ').strip().lower()
                    if not patron_email: break # empty input returns to previous menu
                    res = self.db_cur.execute("SELECT name, email, rowid FROM patrons WHERE email=?", (patron_email,))
                    account_info = res.fetchone()
                    if account_info:
                        patron = Patron(*account_info, self.db_name)
                        self.active_patron = patron
                        print(f'Welcome back {self.active_patron.name}, successfully logged in')  
                    else:
                        print(f'There is no patron account associated with {patron_email}')
                        print('Would you like to try a different email or return to the login menu?')
                        print('1) Different Email')
                        print('2) Login Menu')
                        selection = self.user_input()
                        if selection == '2':
                            break
            # Create A New Account 
            elif selection == '2':
                print('Please enter your name')
                patron_name = input('> ').strip()
                if not patron_name: continue # empty input returns to previous menu
                while not self.active_patron:
                    print('Please enter your email')
                    patron_email = input('> ').strip()
                    if '@' in patron_email:
                        # check to see if email is already asssociated with anther patron account 
                        res = self.db_cur.execute("SELECT email FROM patrons WHERE email=?", (patron_email,))
                        if not res.fetchone():
                            self.db_cur.execute("INSERT INTO patrons VALUES (?, ?)", (patron_name, patron_email))
                            self.db_con.commit()
                            patron = Patron(patron_name, patron_email, self.db_cur.lastrowid, self.db_name)
                            self.active_patron = patron
                            print(f'Welcome {self.active_patron.name}, successfully created account with email {self.active_patron.email}')
                            print('Name And Email On Your Account Can Be Updated On The Patron Menu If Needed')
                        else:
                            print(f'Already a patron account associated with {patron_email}')
                            print('Returning To Login Menu')
                            break
                    else:
                        print('Invalid email, please try again')
            elif selection == '3':
                stop_ui = True
            else:
                print('Invalid selection, please try again\n')
        # Display User Interface Menu
        while not stop_ui:
            print('\nPatron Menu: Select what you\'d like to do')
            print('-----------------------------')
            print('1) Add Item To Spy On')
            print('2) See Current Price Of Items')
            print('3) Update Target Price Of Items')
            print('4) Update Account Info')
            print('5) Exit To Program Main Menu')
            selection = self.user_input()
            # Add Item To Patron Account To Spy On
            if selection == '1':
                print('Enter URL for item that you want to spy on')
                url = self.user_input()
                if not url: continue # empty input returns to previous menu
                if SpyItem.valid_url(url):
                    print('Enter Name Of Item (This Is What You Refer To The Item As)')
                    item_name = self.user_input()
                    print('Enter Current Price Of The Item')
                    current_price = self.user_input().strip('$')
                    print('Enter Maximum Price That You Want To Pay')
                    target_price = self.user_input().strip('$')
                    lookup_logic = SpyItem.get_tag_lookup_logic(url, current_price) 
                    if lookup_logic:
                        # patron_id INTEGER, name TEXT, url TEXT, tag_type TEXT, tag_idx INTEGER, target_price REAL
                        self.db_cur.execute("INSERT INTO items VALUES (?, ?, ?, ?, ?, ?)", (self.active_patron.id, item_name, url, lookup_logic[0], lookup_logic[2], float(target_price)))
                        # item_id INTEGER, key TEXT, value TEXT
                        logic_entries = [(self.db_cur.lastrowid, attr, value) for attr, value in lookup_logic[1].items()]
                        self.db_cur.executemany("INSERT INTO logic VALUES (?, ?, ?)", logic_entries)
                        self.db_con.commit()
                        print(f'{item_name} Has Successfully Been Added To Your Account For Price Spying')
                    else:
                        print('Inputted Current Price Was Not Found On The Webpage Given')
                        print(f'Are you sure that the current price of the {item_name} is ${current_price}?')
                        print('Returning To Patron Menu')
                else:
                    if 'https://' in url:
                        domain_name = url.split('/')[2]
                        print(f'{domain_name.upper()} Does Not Allow Price Spying On Their Website')
                    else:
                        print('Invalid URL, Returning To Patron Menu')
            # Display Current Items Being Tracked And Their Current Price
            elif selection == '2':
                print('Current Price Of Items Being Spied On')
                print('-------------------------------------')
                self.active_patron.display_items()
            # Display Items For Patron To Select To Update Target Price On
            elif selection == '3':
                print('Current Items Being Spied On')
                print('----------------------------------------------------')
                current_items = self.active_patron.grab_items()
                self.active_patron.display_items(show_target=True, item_list=current_items)
                print('\nSelect Item That You Want To Update Target Price For')
                item_selection = self.user_input()
                if not item_selection: continue # empty input returns to previous menu
                if item_selection.isnumeric():
                    item_selection = int(item_selection)
                    if item_selection > 0 and item_selection <= len(current_items):
                        item = current_items[item_selection-1]
                        print(f'Update Target Price For {item.item_name}')
                        print('----------------------------------------------------')
                        print(f'Current Target Price is ${item.target_price}')
                        print('Input New Target Price')
                        new_price = '-'
                        while not new_price.isnumeric():
                            new_price = self.user_input().strip('$')
                        item.update_target_price(new_price)
                        print('Updated Target Price On Item')
                    else:
                        print('Invalid Input, Returning To Patron Menu')
                else:
                    print('Invalid Input, Returning To Patron Menu')
            # Update User Account Info
            elif selection == '4':
                print('Current Account Information')
                print('----------------------------------------------------')
                print(f'Name: {self.active_patron.name}')
                print(f'Email: {self.active_patron.email}')
                print('Account Update Menu: Select what you\'d like to do')
                print('----------------------------------------------------')
                print('1) Update Name')
                print('2) Update Email')
                selection = self.user_input()
                if not selection: continue # empty input returns to previous menu
                if selection == '1':
                    print('Input Your Updated Name')
                    new_name = self.user_input()
                    self.active_patron.update_name(new_name)
                    print(f'Successfully Updated Your Name To {new_name}')
                elif selection == '2':
                    new_email = ''
                    print('Input A New Email Address For Your Account')
                    while '@' not in new_email:
                        new_email = self.user_input().lower()
                    try:
                        self.active_patron.update_email(new_email)
                        print(f'Successfully Updated The Email On Your Account To {new_email}')
                    except sqlite3.IntegrityError:
                        print(f'Already a patron account associated with {new_email}')
                else:
                    print('Invalid Input, Returningh To Patron Menu')
            elif selection == '5':
                stop_ui = True
        # Exit User Interface
        self.active_patron = None
        print('Exiting User Interface and Returning To Program Main Menu')

    def user_input(self):
        # this is only used in UI part of program
        if self.active_patron:
            selection = input(f'{self.active_patron.name} > ').strip()
        else:
            selection = input('> ').strip()
        return selection   

def main():
    price_drop_spy = MainProgam('db.sqlite3')
    price_drop_spy.start_program()

if __name__=='__main__':
    main()