import email
import imapclient
import pyzmail
import bs4
import getpass
import requests
import traceback
# User input
user_email = input('Enter your email username: ')
user_pass = getpass.getpass(prompt='Enter your password: ',stream=None) # Getpass hide's input stream on input

auto_unsub = False
auto_delete = False
print_links = True
# Connects to IMAP Server
unsub_links = []
unsub_uids = []
unsub_headers = []
imap_obj = imapclient.IMAPClient('imap.gmail.com', ssl=True)
imap_obj.login(user_email, user_pass)
imap_obj.select_folder('INBOX', readonly=True if auto_delete is False else False) # reads from your inbox
UIDs = imap_obj.gmail_search('ALL') # searches for everything

raw_messages = imap_obj.fetch(UIDs, ['RFC822', 'BODY[]']) # grabs UID from body of email

for i in UIDs:
    raw_message = pyzmail.PyzMessage.factory(raw_messages[i][b'BODY[]'])
    add_uid = False
    if raw_message is not None:
        encoded_msg = raw_messages[i][b'RFC822']
        email_msg = email.message_from_string(encoded_msg.decode())
        usl = email_msg.get('List-Unsubscribe')
        
        if usl is not None:
            add_uid = True
            if "mailto" not in usl and  ("https://" in usl or "http://" in usl):
                parsed_link = usl.replace("<","").replace(">","")
                if parsed_link not in unsub_links:
                    unsub_links.append(parsed_link)

    if raw_message.html_part is not None:
        raw_soup = raw_message.html_part.get_payload().decode(raw_message.html_part.charset)
        soup = bs4.BeautifulSoup(raw_soup, 'html.parser')
        link_elems = soup.select('a')
        for unsub in soup.findAll('a'):
            if 'unsubscribe' in str(unsub).lower():
                unsub_link = unsub.get('href')
                if unsub_link not in unsub_links:
                    unsub_links.append(unsub.get('href'))
                add_uid = True
    if add_uid:
        unsub_uids.append(i)
        
if auto_delete:
    print("Deleting Messages")
    imap_obj.delete_messages(unsub_uids)
    imap_obj.expunge()

imap_obj.logout()       


if print_links:
    print('Crap to unsub:')
    for link in unsub_links:
        print(link)

if auto_unsub:
    for link in unsub_links:
        try:
            if link is None or "http" not in link:
                continue
            r = requests.get(link)
            if r.status_code == 200:
                print("Unsubbed from: " + link )
        except Exception as e:
            print("Failed to Unsub from: " + link + " due to: " + traceback.format_exc())
            print("Status Code was : " + r.status_code)


