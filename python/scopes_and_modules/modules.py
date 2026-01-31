import os
import sys
import stat
import platform

def is_in_global(name):
    """ Checks if name is in global namespace"""
    return name in globals()

my_name = "Tom"

def print_os_info():
    """ Prints OS name, Logged user, and current directory"""
    print(f'Operating system: {platform.system()}')
    print("Logged user: ", os.getlogin())
    print("Current directory: ", os.getcwd())

def reverse_args():
    """ Reverse argument list provided in the command line"""
    args = sys.argv[1:]
    reverse_args_list = args[::-1]
    if not args:
        print("No arguments")
    else:
        print(' '.join(reverse_args_list))

def change_file_permissions(file_name):
    """ Searches for file in the system
    If found, checks if executable
    If not, grants permission to Owner and Group only
    """
    found = False
    for root, dirs, files in os.walk('/'):
        if file_name in files:
            found = True
            file_path = os.path.join(root, file_name)
            current_perm = os.stat(file_path).st_mode

            perm_str = stat.filemode(current_perm)

            if 'x' not in perm_str:
                os.chmod(file_path, 0o770)
                print("Owner and Group received updated permissions")
            else:
                print("File is already executable")
            break

    if not found:
        print(f"The file {file_name} was not found in the system")
