import os
import socket
import getpass
import sys


def get_prompt():
    """Формирует приглашение командной строки"""
    username = getpass.getuser()
    hostname = socket.gethostname()
    current_dir = os.getcwd()
    home_dir = os.path.expanduser("~")

    # Сокращаем домашнюю директорию до ~
    if current_dir.startswith(home_dir):
        current_dir = current_dir.replace(home_dir, "~", 1)

    return f"{username}@{hostname}:{current_dir}$ "


def parse_input(input_string):
    """Парсит входную строку с поддержкой кавычек"""
    tokens = []
    current_token = []
    in_double_quotes = False
    in_single_quotes = False
    escaped = False

    for char in input_string:
        if escaped:
            current_token.append(char)
            escaped = False
        elif char == '\\':
            escaped = True
        elif char == '"' and not in_single_quotes:
            in_double_quotes = not in_double_quotes
        elif char == "'" and not in_double_quotes:
            in_single_quotes = not in_single_quotes
        elif char.isspace() and not (in_double_quotes or in_single_quotes):
            if current_token:
                tokens.append(''.join(current_token))
                current_token = []
        else:
            current_token.append(char)

    if current_token:
        tokens.append(''.join(current_token))

    if in_double_quotes or in_single_quotes:
        raise ValueError("Незакрытые кавычки")

    return tokens


def execute_command(args):
    """Выполняет команду и возвращает результат"""
    if not args:
        return ""

    command = args[0]

    if command == "exit":
        if len(args) > 1:
            return "exit: слишком много аргументов"
        return "EXIT_COMMAND"
    elif command == "ls":
        return f"ls: аргументы {args[1:]}"
    elif command == "cd":
        if len(args) > 2:
            return "cd: слишком много аргументов"
        elif len(args) == 1:
            try:
                os.chdir(os.path.expanduser("~"))
                return "cd: переход в домашнюю директорию"
            except Exception as e:
                return f"cd: ошибка: {e}"
        else:
            try:
                os.chdir(args[1])
                return f"cd: успешный переход в '{args[1]}'"
            except FileNotFoundError:
                return f"cd: нет такой директории: {args[1]}"
            except NotADirectoryError:
                return f"cd: не является директорией: {args[1]}"
            except PermissionError:
                return f"cd: нет прав доступа: {args[1]}"
            except Exception as e:
                return f"cd: неизвестная ошибка: {e}"
    else:
        return f"{command}: команда не найдена"


def run_interactive_mode():
    """Запускает интерактивный режим работы"""
    print("Эмулятор командной строки UNIX. Для выхода введите 'exit'")
    print("=" * 60)

    while True:
        try:
            prompt = get_prompt()
            user_input = input(prompt).strip()

            if not user_input:
                continue

            try:
                args = parse_input(user_input)
                result = execute_command(args)

                if result == "EXIT_COMMAND":
                    print("Выход из эмулятора")
                    break
                elif result:
                    print(result)

            except ValueError as e:
                print(f"Ошибка парсинга: {e}")
            except Exception as e:
                print(f"Неожиданная ошибка: {e}")

        except KeyboardInterrupt:
            print("\nДля выхода введите 'exit'")
        except EOFError:
            print("\nДля выхода введите 'exit'")


def demonstrate_prototype():
    """Демонстрирует работу прототипа"""
    print("=" * 60)
    print("ДЕМОНСТРАЦИЯ РАБОТЫ ЭМУЛЯТОРА КОМАНДНОЙ СТРОКИ")
    print("=" * 60)

    # Тестовые команды для демонстрации
    test_cases = [
        "ls",
        "ls -l -a",
        'ls "file with spaces"',
        "ls 'another file'",
        "cd",
        "cd /tmp",
        "cd nonexistent_directory",
        "cd /root",  # Обычно нет прав доступа
        "invalid_command",
        "exit"
    ]

    print("Сценарий 1: Базовые команды")
    print("-" * 40)
    for command in test_cases[:4]:
        print(f"{get_prompt()}{command}")
        try:
            args = parse_input(command)
            result = execute_command(args)
            print(result)
        except Exception as e:
            print(f"Ошибка: {e}")
        print()

    print("Сценарий 2: Команда cd с обработкой ошибок")
    print("-" * 40)
    for command in test_cases[4:8]:
        print(f"{get_prompt()}{command}")
        try:
            args = parse_input(command)
            result = execute_command(args)
            print(result)
        except Exception as e:
            print(f"Ошибка: {e}")
        print()

    print("Сценарий 3: Ошибки и завершение")
    print("-" * 40)
    for command in test_cases[8:]:
        print(f"{get_prompt()}{command}")
        try:
            args = parse_input(command)
            result = execute_command(args)
            print(result)
        except Exception as e:
            print(f"Ошибка: {e}")
        print()

    print("Сценарий 4: Тестирование парсера с кавычками")
    print("-" * 40)
    test_quotes = [
        'echo "hello world"',
        "echo 'hello world'",
        'echo "hello\'world"',
        "echo 'hello\"world'",
        'echo "unclosed quote',
        "echo 'unclosed quote"
    ]

    for command in test_quotes:
        print(f"Ввод: {command}")
        try:
            args = parse_input(command)
            print(f"Результат парсинга: {args}")
        except ValueError as e:
            print(f"Ошибка: {e}")
        print()

    print("=" * 60)
    print("ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
    print("=" * 60)



def main():
    """Основная функция"""
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demonstrate_prototype()
    else:
        run_interactive_mode()


if __name__ == "__main__":
    main()