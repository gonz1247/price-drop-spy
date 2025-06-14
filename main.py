from bs4 import BeautifulSoup
import requests

def find_tag(SCRAPE_URL, current_price):
    
    # Verify that URL is valid before attemping to scrape it
    html = requests.get(SCRAPE_URL)
    if html.ok:
        soup = BeautifulSoup(html.text, 'lxml', multi_valued_attributes=None)
    else:
        raise ValueError(f'{SCRAPE_URL} is not valid URL')

    # Find tag that is best representation of the price inputted
    tag_options = soup.body.find_all(lambda tag: current_price in tag.text)
    tag_shortest_text = tag_options[0]
    correct_tag_options = list()
    for tag in tag_options:
        # Assume that the price will be self contained and therefore short
        # # Want to grab the tag that simply has the price, not one that has a the story of why it's that price
        if len(tag.text) < len(tag_shortest_text.text):
            tag_shortest_text = tag
            correct_tag_options = [tag]
        elif len(tag.text) == len(tag_shortest_text.text):
            # If tag has text of same length then likely a child of previos tag identified
            # # Will check all tag to which one was reliably can get the price  
            correct_tag_options.append(tag)

    # Verify that identifed tag(s) actually have the right price/can be used to reliably to get the price
    for tag in correct_tag_options:
        correct_tag = soup.find(tag.name,**tag.attrs)
        price = list()
        for char in correct_tag.text:
            # only grab numbers and decimals from tag text (will strip out any extra decimals that may be leading or trailing the price)
            if char.isnumeric() or char == '.':
                price.append(char)
        verified_price = ''.join(price).strip('.')
        # Let user know if you were able to verify the price or not
        if current_price == verified_price:
            print('yay, was able to verify price')
            return 
    # If for loop is exited then did none of the options worked for verifying the price
    print('sorry, was not able to verify item price')

if __name__ == '__main__':

    # Get URL to scrape
    SCRAPE_URL = 'https://shop.lululemon.com/p/men-ss-tops/Organic-Cotton-Classic-Fit-T-Shirt/_/prod11680617?color=0002'
    #SCRAPE_URL = 'https://skims.com/products/sheer-cotton-t-shirt-blue-bell'
    SCRAPE_URL = 'https://www.nike.com/t/killshot-2-leather-mens-shoes-1lEPvIbm/HM9431-001?nikemt=true&cp=54011862001_search_--g-21728772664-171403009167--c-1015651687-00197859044818&dplnk=member&gad_source=1&gad_campaignid=21728772664&gbraid=0AAAAADy86kOsh9txv0At5foYSBh1PKgh2&gclid=Cj0KCQjwmK_CBhCEARIsAMKwcD42_Q8_DvZjKSqoRPxGsbbizPOGjqJxcmOwd3WzISxWOaBes6b6OMQaAnWxEALw_wcB&gclsrc=aw.ds'

    # Get item current price to develop scraping approach 
    current_price = '58.97'

    find_tag(SCRAPE_URL,current_price)