import pytest

from exceptions import *

def test_pass_exceptions():
    assert(handle_pass_with_exceptions("Tom12345#"))
    handle_pass_with_exceptions("Tom123#")
    handle_pass_with_exceptions("Tom12345")
    handle_pass_with_exceptions("tom12345#")
    handle_pass_with_exceptions("TOM12345#")
    handle_pass_with_exceptions("Tommmmmm#")
