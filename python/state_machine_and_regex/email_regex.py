import re
def valid_email(email: str):
    pattern = r'^[\w.%+-]+@[\w.-]+\.[a-zA-Z]{2,}$'
    return bool(re.search(pattern, email))

def remove_points(email: str):
    pattern = r'^([\w.%+-]+)(@[\w.-]+\.[a-zA-Z]{2,})$'
    match = re.match(pattern, email)
    if match:
        username = match.group(1)
        username = re.sub(r'\.','',username)
        return username + match.group(2)
    return "Invalid email"

if __name__=="__main__":
    print(f'sthait@gmail.com: {valid_email('sthait@gmail.com')}')
    print(f'sth.ait@gmail.com: {valid_email('sth.ait@gmail.com')}')
    print(f'sthait@gm.ail.com: {valid_email('sthait@gm.ail.com')}')
    print(f'stha_it@gmail.com: {valid_email('stha_it@gmail.com')}')
    print(f'sthait@gmail.c.o.m: {valid_email('sthait@gmail.c.o.m')}')
    print(f'sth...ait@gmailcom: {valid_email('sth...ait@gmail.com')}')

    print(f'sthait@gmail.com: {remove_points('sthait@gmail.com')}')
    print(f'sth.ait@gmail.com: {remove_points('sth.ait@gmail.com')}')
    print(f'sthait@gm.ail.com: {remove_points('sthait@gm.ail.com')}')
    print(f'stha_it@gmail.com: {remove_points('stha_it@gmail.com')}')
    print(f'sthait@gmail.c.o.m: {remove_points('sthait@gmail.c.o.m')}')
    print(f'sth...ait@gmailcom: {remove_points('sth...ait@gmail.com')}')