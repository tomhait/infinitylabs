import os
import cmd

class MyShell(cmd.Cmd):
    intro = "Welcome to MyShell! Type help or ? to list commands.\n"
    prompt = "myshell$ "

    def do_greet(self, arg):
        """ Greet the named person: greet <name>"""
        name = arg.strip() or "stranger"
        print(f"Hello, {name}")

    def do_exit(self, arg):
        """ Exit the shell"""
        print("Goodbye!")
        return True

    def do_cd(self, args):
        """ change directory"""
        args = args.strip().split()
        if not args:
            return None
        path = args[0]

        try:
            os.chdir(os.path.abspath(path))
        except FileNotFoundError:
            print(f"cd: no such file or directory: {path}")
        except Exception as e:
            print(f"cd: error changing directory: {e}")

    def default(self, args):
        """ Handle other commands using fork and execvp"""
        args = args.strip().split()
        if not args:
            return None
        is_bg = False
        if args[-1] == "&":
            is_bg = True
            args.pop()

        pid = os.fork()

        if pid == 0:
            try:
                os.execvp(args[0], args)
            except FileNotFoundError:
                print(f"myshell: command not found: {args[0]}")
                os._exit(1)
        elif not is_bg:
            os.waitpid(pid, 0)

if __name__ == "__main__":
    MyShell().cmdloop()
