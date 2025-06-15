from patron import Patron

class MainProgam():

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
            elif selection == '2':
                print('Please enter your name')
                patron_name = input('> ').strip()
                while not active_patron:
                    print('Please enter your email')
                    patron_email = input('> ').strip()
                    try:
                        patron = Patron(patron_name, patron_email)
                        active_patron = patron
                        print(f'Welcome {active_patron.name}, successfully created account with email {active_patron.email}')
                    except ValueError:
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
    price_drop_spy = MainProgam()
    price_drop_spy.start_program()

if __name__=='__main__':
    main()