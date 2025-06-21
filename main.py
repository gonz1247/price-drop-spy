from patron import Patron
from spy_item import SpyItem
from display_styles import error_msg, success_msg, warning_msg, menu_display, prompt_msg
import os, sqlite3
from colorama import Fore

class MainProgam():

    active_patron = None

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
            self.db_cur.execute('CREATE TABLE targets(patron_id INTEGER, name TEXT, target_price REAL, url_id INTEGER)')
            self.db_cur.execute('CREATE TABLE spy_urls(url TEXT, tag_type TEXT, tag_idx INTEGER)')
            # Need a another table to save the dictionary that stores the logic for scraping a website for a price change
            self.db_cur.execute('CREATE TABLE tag_attrs(url_id INTEGER, key TEXT, value TEXT)')
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
            menu_display('\nMain Menu: Select what you\'d like to do')
            menu_display('-----------------------------')
            menu_display('1) Start Spying On Items')
            menu_display('2) Use User Interface')
            menu_display('3) End Program')
            selection = self.user_input()
            if selection.strip() == '1':
                self.start_spying()
            elif selection.strip() == '2':
                self.run_ui()
            elif selection.strip() == '3':
                stop_program = True
                print('Stopping Price Drop Spy Program, Goodbye')
            else:
                error_msg('Invalid selection, please try again\n')

    def start_spying(self):
        # TODO: Work on spying functionality. Determine if can search items on behalf of multiples patrons at a time
        pass

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
            menu_display('4) Update Account Info')
            menu_display('5) Exit To Program Main Menu')
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
                print('Current Items Being Spied On')
                print('----------------------------------------------------')
                current_items = self.active_patron.grab_items()
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
            # Update User Account Info
            elif selection == '4':
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
            elif selection == '5':
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

def main():
    price_drop_spy = MainProgam('db.sqlite3')
    price_drop_spy.start_program()

if __name__=='__main__':
    main()