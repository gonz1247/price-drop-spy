# Price Drop Spy
Program to track price drops of online shopping items.

We do a lot of online shopping in my household so I thought a useful tool would be a program that could send out emails whenever there was a price change that met my spending power. Some online shops have notifications for when there are price drops in general, but this could result in unnecessary emails if it's still not low enough for the specific user. Price Drop Spy ensures that when you get a email notification about a price drop, it means that you can be ready to buy it right then and not have to worry about getting false hopes up for a $1 drop. 

# Getting Started
- Create a .env file that has all the required information indicated in the .env.example file (note that .env is in .gitignore since it will contain personal/sensitive information)
  - If using a smtp such as gmail (or maybe others) you may need to create an [application password](https://support.google.com/accounts/answer/185833?hl=en)
- Set up a virtual enviroment using `requirements.txt`
  - `python -m pip install -r requirements.txt`
- If going to do local development, set `debug_flag` to `True` at the bottom of main.py
- Run program by calling main.py
  - `python main.py`

# Thank You
Thanks for checking out my project! Currently, I am an aerospace engineer but, I am hoping to pivot my career to software engineering hopefully soon. I am hopeful that continuing to work on personal projects like this will help me to develop the skills and portfolio necessary to make the switch in careers.

# Limitations 
- Program does not work with websites that don't allow requests from the Python requests package (e.g., amazon.com)
- Program has not been tested against real price drops, all testing was done by changing the target price in the database while another instance of the program was in spy mode

# Future Work 
At this time I don't have any plans to continue to develop this program as this was just intended to be a mock-up/a way to introduce myself to web scraping in Python. However, some things that can be addressed by myself (or you!) in the future are:
- Address incompatibilities with major online stores that currently don't work (e.g., amazon.com)
  - Option 1: I think there is an amazon API that could be leveraged
  - Option 2: Utilize a different Python package than BeautifulSoup (maybe this solves it, maybe not)
- Convert program to be a web app 
- Run spying operation on a cloud server/not on a local development machine 
- Maybe some other things that I haven't thought of yet
