import os
import sys
import socket
import shlex


class ComLineEm:
    def __init__(self):
        self.current_path = "~"
        self.user = os.getlogin()
        self.hostname = socket.gethostname()

    def run(self):
        print("Эмулятор командной строки. Для выхода введите 'exit'")
        print("-" * 50)

        while True:
            try:
                # приглашение с реальными данными ОС
                prompt = f"{self.user}@{self.hostname}:{self.current_path}$ "
                command_input = input(prompt).strip()

                if not command_input:
                    continue

                # shlex для корректного парсинга аргументов в кавычках
                try:
                    parsed_args = shlex.split(command_input)
                except ValueError as e:
                    print(f"Ошибка парсинга: {e}")
                    continue

                command = parsed_args[0]
                args = parsed_args[1:]

                if command == 'exit':
                    if not args:
                        print("Выход из эмулятора")
                        break
                    else:
                        print("Ошибка: команда exit не принимает аргументы")
                elif command == 'ls':
                    self.ls(args)
                elif command == 'cd':
                    self.cd(args)
                elif command == 'help':
                    self.help()
                else:
                    print(f"Ошибка: неизвестная команда '{command}'")

            except KeyboardInterrupt:
                print("\nДля выхода введите 'exit'")
            except EOFError:
                print("\nВыход из эмулятора")
                break
            except Exception as e:
                print(f"Ошибка: {e}")

    def ls(self, args):
        """Заглушка для команды ls - выводит имя и аргументы"""
        if args:
            print(f"ls {args}")
        else:
            print("введите аргументы")

    def cd(self, args):
        """Заглушка для команды cd - выводит имя и аргументы"""
        if args:
            print(f"cd {args}")
        else:
            print("введите аргументы")

    def help(self):
        print("Доступные команды")
        print("  ls [аргументы] - показать содержимое директории")
        print("  cd [путь] - сменить директорию")
        print("  exit - выход из эмулятора")
        print("  help - показать эту справку")

if __name__ == "__main__":
    shell = ComLineEm()
    shell.run()