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

    def default(self, args):
        """ Handle other commands using fork and execvp"""
        args = args.strip().split()
        if not args:
            return None

        pid = os.fork()

        if pid == 0:
            try:
                os.execvp(args[0], args)
            except FileNotFoundError:
                print(f"myshell: command not found: {args[0]}")
                os._exit(1)
        else:
            os.waitpid(pid, 0)

if __name__ == "__main__":
    MyShell().cmdloop()
