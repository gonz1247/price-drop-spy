from patron import Patron
import os, sqlite3

class MainProgam():

    def __init__(self, db_name):
        if os.path.exists(db_name):
            # database already exist so just set up connection and cursor
            self.db_con = sqlite3.connect(db_name)
            self.db_cur = self.db_con.cursor()
        else:
            # database does not exist yet so need to set up tables in addition to connection and cursor
            self.db_con = sqlite3.connect(db_name)
            self.db_cur = self.db_con.cursor()
            # Set up tables 
            self.db_cur.execute('CREATE TABLE patrons(name TEXT, email TEXT UNIQUE)') # adding unique on email may be overbearing and could be accomplished elsewhere
            self.db_cur.execute('CREATE TABLE items(patron_id INTEGER, url TEXT, tag_type TEXT, logic_id INTEGER, target_price REAL)')
            # Need a third table to save the dictionary that stores the logic for scraping a website for a price change
            self.db_cur.execute('CREATE TABLE logic(item_id INTEGER, key TEXT, value TEXT)')
            self.db_con.commit()


    def start_program(self):
        self.main_menu()

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
        pass

    def run_ui(self):
        active_patron = None
        stop_ui = False
        # Sign in or create an account
        while not active_patron and not stop_ui:
            print('\nLog In Menu: Select what you\'d like to do')
            print('-----------------------------')
            print('1) Sign In')
            print('2) Create Account')
            print('3) Exit To Program Main Menu')
            selection = input('> ').strip()
            if selection == '1':
                while not active_patron:
                    print('Please enter the email associated with your account')
                    patron_email = input('> ').strip()
                    res = self.db_cur.execute("SELECT name, email, rowid FROM patrons WHERE email=?", (patron_email,))
                    account_info = res.fetchone()
                    if account_info:
                        patron = Patron(*account_info)
                        active_patron = patron
                        print(f'Welcome back {active_patron.name}, successfully logged in')  
                    else:
                        print(f'There is no patron account associated with {patron_email}')
                        print('Would you like to try a different email or return to the log in menu?')
                        print('1) Different Email')
                        print('2) Log In Menu')
                        selection = input('> ').strip()
                        if selection == '2':
                            break
            elif selection == '2':
                print('Please enter your name')
                patron_name = input('> ').strip()
                while not active_patron:
                    print('Please enter your email')
                    patron_email = input('> ').strip()
                    if '@' in patron_email:
                        # check to see if email is already asssociated with anther patron account 
                        res = self.db_cur.execute("SELECT email FROM patrons WHERE email=?", (patron_email,))
                        if not res.fetchone():
                            self.db_cur.execute("INSERT INTO patrons VALUES (?, ?)", (patron_name, patron_email))
                            self.db_con.commit()
                            patron = Patron(patron_name, patron_email, self.db_cur.lastrowid)
                            active_patron = patron
                            print(f'Welcome {active_patron.name}, successfully created account with email {active_patron.email}')  
                        else:
                            print(f'Already a patron account associated with {patron_email}')
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
            selection = input(f'{active_patron.name} > ').strip()
            if selection == '5':
                stop_ui = True
        # Exit User Interface
        print('Exiting User Interface and Returning To Program Main Menu')

    

def main():
    price_drop_spy = MainProgam('db.sqlite3')
    price_drop_spy.start_program()

if __name__=='__main__':
    main()