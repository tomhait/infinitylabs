import re

class MissingLowerLetterError(Exception):
    """ Raised when password doesn't contain lower letters"""
    pass

class MissingUpperLetterError(Exception):
    """ Raised when password doesn't contain upper letters"""
    pass

class MissingDigitsError(Exception):
    """ Raised when password doesn't contain digits letters"""
    pass

class MissingSpecialError(Exception):
    """ Raised when password doesn't
    contain special letters (@,#,%,&)
    """
    pass

class InsufficientLettersError(Exception):
    """ Raised when password doesn't
    contain at least 8 letters
    """
    pass

def check_password(password, length = 8):
    """ Check validity of a password"""
    has_lower = re.search(r'[a-z]', password) is not None
    has_upper = re.search(r'[A-Z]', password) is not None
    has_digits = re.search(r'[0-9]', password) is not None
    has_special = re.search(r'[@#%&]', password) is not None
    if not has_lower:
        raise MissingLowerLetterError("Missing lower letters")
    if not has_upper:
        raise MissingUpperLetterError("Missing upper letters")
    if not has_digits:
        raise MissingDigitsError("Missing digits letters")
    if not has_special:
        raise MissingSpecialError("Missing special letters - @, #, %, &")
    if len(password) < length:
        raise InsufficientLettersError(f"Password's length isn't at least {length}")

def handle_pass_with_exceptions(password):
    try:
        check_password(password)
    except MissingLowerLetterError as e:
        print(e)
    except MissingUpperLetterError as e:
        print(e)
    except MissingDigitsError as e:
        print(e)
    except MissingSpecialError as e:
        print(e)
    except InsufficientLettersError as e:
        print(e)
    else:
        return True