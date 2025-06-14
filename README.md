# price-drop-spy
Program to track price drops of online shopping items

## program outline
- Features/Capabilties 
  - patrons sign up to get alerts when item goes on sale for at least the desired amount 
  - option for patron to check current price of items being tracked
  - email patron when item goes on sale
- Planned Tools / Methods
  - save information in SQLite db
  - use beautiful soup for web scrapping of prices 
- Patron Account
  - email (must be unique)
  - name 
  - no password (could add this if working in a framework like Django, but this is just a mockup)
  - watch items
- Watch Item 
  - URL to item
  - current price (this will be used to verify item/get logic for how to scrap it more efficiently later but will not be saved to item)
  - target price
  - Name of item (user input, not scrapped)