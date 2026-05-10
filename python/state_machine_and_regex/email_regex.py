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
    print(f'sssss@gmail.com: {valid_email('sssss@gmail.com')}')
    print(f'sss.sss@gmail.com: {valid_email('sss.sss@gmail.com')}')
    print(f'sssss@gm.ail.com: {valid_email('sssss@gm.ail.com')}')
    print(f'ssss_ss@gmail.com: {valid_email('ssss_ss@gmail.com')}')
    print(f'sssss@gmail.c.o.m: {valid_email('sssss@gmail.c.o.m')}')
    print(f'sss...sss@gmailcom: {valid_email('sss...sss@gmail.com')}')

    print(f'sssss@gmail.com: {remove_points('sssss@gmail.com')}')
    print(f'sss.sss@gmail.com: {remove_points('sss.sss@gmail.com')}')
    print(f'sssss@gm.ail.com: {remove_points('sssss@gm.ail.com')}')
    print(f'ssss_ss@gmail.com: {remove_points('ssss_ss@gmail.com')}')
    print(f'sssss@gmail.c.o.m: {remove_points('sssss@gmail.c.o.m')}')
    print(f'sss..sss@gmailcom: {remove_points('sss...sss@gmail.com')}')