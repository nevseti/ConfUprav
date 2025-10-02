import os
import sys
import socket
import shlex
import argparse


class ComLineEm:
    def __init__(self, vfs_path=None, script_path=None):
        self.current_path = "~"
        self.user = os.getlogin()
        self.hostname = socket.gethostname()
        self.vfs_path = vfs_path
        self.script_path = script_path

        print("=== Конфигурация эмулятора ===")
        print(f"VFS path: {vfs_path or 'Не указан'}")
        print(f"Script path: {script_path or 'Не указан'}")
        print("=" * 30)

    def run(self):
        if self.script_path:
            self.run_script()
        else:
            self.run_interactive()

    def run_interactive(self):
        # print("Эмулятор командной строки. Для справки введите 'help'. Для выхода введите 'exit'")
        # print("-" * 50)

        while True:
            try:
                prompt = f"{self.user}@{self.hostname}:{self.current_path}$ "
                command_input = input(prompt).strip()

                if not command_input:
                    continue

                result = self.execute_command(command_input)
                if result is None:
                    break
                elif not result:
                    continue

            except KeyboardInterrupt:
                print("\nВыход из эмулятора")
                break
            except Exception as e:
                print(f"Ошибка: {e}")

    def run_script(self):
        try:
            with open(self.script_path, 'r', encoding='utf-8') as file:
                commands = file.readlines()

            print(f"Выполнение скрипта: {self.script_path}")
            print("-" * 50)

            for line_num, command_line in enumerate(commands, 1):
                command_line = command_line.strip()

                # пустые строки и комментарии
                if not command_line or command_line.startswith('#'):
                    continue

                print(f"{self.user}@{self.hostname}:{self.current_path}$ {command_line}")

                result = self.execute_command(command_line, from_script=True)
                if result is None:
                    print("Скрипт завершен")
                    break
                elif not result:
                    print(f"Ошибка в строке {line_num}. Остановка выполнения.")
                    break

        except FileNotFoundError:
            print(f"Ошибка: скрипт '{self.script_path}' не найден")
        except Exception as e:
            print(f"Ошибка при выполнении скрипта: {e}")

    def execute_command(self, command_input, from_script=False):
        try:
            parsed_args = shlex.split(command_input)
        except ValueError as e:
            print(f"Ошибка парсинга: {e}")
            return False

        command = parsed_args[0]
        args = parsed_args[1:]

        if command == 'exit':
            if not args:
                if not from_script:
                    print("Выход из эмулятора")
                return None  # Останавливаем выполнение
            else:
                print("Команда exit не принимает аргументы")
        elif command == 'ls':
            self.ls(args)
        elif command == 'cd':
            self.cd(args)
        elif command == 'help':
            self.help()
        else:
            print(f"Ошибка: неизвестная команда '{command}'")
            if from_script:
                return False
        return True

    def ls(self, args):
        if args:
            print(f"ls {args} ")
        else:
            print(f"ls [] ")

    def cd(self, args):
        if args:
            print(f"cd {args} ")
        else:
            print(f"cd [] ")

    def help(self):
        print(" Доступные команды")
        print("  ls [аргументы] - показать содержимое директории")
        print("  cd [путь] - сменить директорию")
        print("  exit - выход из эмулятора")
        print("  help - показать эту справку")


def main():
    parser = argparse.ArgumentParser(description='Эмулятор командной строки')
    parser.add_argument('--vfs-path', '-v', help='Путь к виртуальной файловой системе')
    parser.add_argument('--script', '-s', help='Путь к стартовому скрипту')

    args = parser.parse_args()

    shell = ComLineEm(vfs_path=args.vfs_path, script_path=args.script)
    shell.run()


if __name__ == "__main__":
    main()