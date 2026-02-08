import os
import cmd


class MyShell(cmd.Cmd):
    intro = "Welcome to MyShell! Type help or ? to list commands.\n"
    prompt = "myshell$ "
    jobs = []

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

    def do_fg(self, arg):
        try:
            pid = int(arg.strip())
            if pid in self.jobs:
                print(f"Bringing {pid} to foreground")
                os.waitpid(pid,0)
                self.jobs.remove(pid)
            else:
                print(f"No background job with PID {pid}")
        except ValueError:
            print("Usage: fg <PID>")

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
        else:
            if not is_bg:
                os.waitpid(pid, 0)
            else:
                self.jobs.append(pid)
                print(f"{len(self.jobs)} {pid} started in background")

if __name__ == "__main__":
    MyShell().cmdloop()
