from colorama import init, Fore

# Basing Colors On What Shows Up Well In VSCODE
## Looks good on command prompt too, powershell not so much 

init(convert=True)

def error_msg(text):
    print(Fore.RED + text + Fore.RESET)

def success_msg(text):
    print(Fore.GREEN + text + Fore.RESET)

def warning_msg(text):
    print(Fore.YELLOW + text + Fore.RESET)

def menu_display(text):
    print(Fore.BLUE + text + Fore.RESET)

def prompt_msg(text):
    print(Fore.CYAN + text + Fore.RESET)

if __name__ == '__main__':
    error_msg('Whoops, made a mistake')
    success_msg('Yay, did something good')
    warning_msg("Ugh, we're okay but thought you should know")
    menu_display('Welcome Menu')
    menu_display('1) Option 1')
    prompt_msg('Do something!')
    print('Normal Text')