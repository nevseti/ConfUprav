import os
import sys
import socket
import shlex
import argparse
import xml.etree.ElementTree as ET
import hashlib
import base64
import calendar
from datetime import datetime


class VFSNode:
    def __init__(self, name, path):
        self.name = name
        self.path = path


class VFSFile(VFSNode):

    def __init__(self, name, path, content="", encoding="text"):
        super().__init__(name, path)
        self.content = content
        self.encoding = encoding
        self.size = len(content)


class VFSFolder(VFSNode):

    def __init__(self, name, path):
        super().__init__(name, path)
        self.children = {}  # name -> VFSNode


class VirtualFileSystem:

    def __init__(self):
        self.root = VFSFolder("", "/")
        self.name = ""
        self.raw_data = ""

    def load_from_xml(self, xml_path):
        try:
            with open(xml_path, 'r', encoding='utf-8') as f:
                self.raw_data = f.read()

            tree = ET.ElementTree(ET.fromstring(self.raw_data))
            root = tree.getroot()

            self.name = root.get('name', 'unnamed_vfs')
            self.root = VFSFolder("", "/")

            # Рекурсивно строим структуру VFS
            self._parse_folder(root, self.root, "/")

            print(f"VFS '{self.name}' успешно загружена из {xml_path}")
            return True

        except Exception as e:
            print(f"Ошибка загрузки VFS: {e}")
            return False

    def _parse_folder(self, xml_element, current_folder, current_path):
        for child in xml_element:
            if child.tag == 'folder':
                folder_name = child.get('name', '')
                folder_path = os.path.join(current_path, folder_name).replace('\\', '/')
                new_folder = VFSFolder(folder_name, folder_path)
                current_folder.children[folder_name] = new_folder
                self._parse_folder(child, new_folder, folder_path)

            elif child.tag == 'file':
                file_name = child.get('name', '')
                file_path = os.path.join(current_path, file_name).replace('\\', '/')
                encoding = child.get('encoding', 'text')
                content = child.text or ""

                if encoding == 'base64' and content:
                    try:
                        content = base64.b64decode(content).decode('utf-8')
                    except Exception as e:
                        print(f"Ошибка декодирования base64 файла {file_name}: {e}")

                new_file = VFSFile(file_name, file_path, content, encoding)
                current_folder.children[file_name] = new_file

    def calculate_sha256(self):
        if not self.raw_data:
            return "N/A"
        return hashlib.sha256(self.raw_data.encode('utf-8')).hexdigest()

    def get_info(self):
        return {
            'name': self.name,
            'sha256': self.calculate_sha256(),
            'loaded': bool(self.raw_data)
        }

    # НОВЫЕ МЕТОДЫ ДЛЯ ЭТАПА 4
    def get_node(self, path):
        if path == "/":
            return self.root

        parts = [p for p in path.split('/') if p]  # Убираем пустые части
        current = self.root

        for part in parts:
            if part in current.children:
                current = current.children[part]
            else:
                return None
        return current

    def list_directory(self, path):
        node = self.get_node(path)
        if node and isinstance(node, VFSFolder):
            return list(node.children.keys())
        return None

    def is_directory(self, path):
        node = self.get_node(path)
        return node and isinstance(node, VFSFolder)

    def read_file(self, path):
        node = self.get_node(path)
        if node and isinstance(node, VFSFile):
            return node.content
        return None


class ComLineEm:
    def __init__(self, vfs_path=None, script_path=None):
        self.current_path = "/"
        self.user = os.getlogin()
        self.hostname = socket.gethostname()
        self.script_path = script_path
        self.vfs = VirtualFileSystem()

        vfs_loaded = False
        if vfs_path:
            vfs_loaded = self.vfs.load_from_xml(vfs_path)
            if not vfs_loaded:
                print("Не удалось загрузить VFS. Завершение работы.")
                sys.exit(1)

        print("=== Конфигурация эмулятора ===")
        print(f"VFS path: {vfs_path or 'Не указан'}")
        print(f"Script path: {script_path or 'Не указан'}")
        if vfs_path:
            vfs_info = self.vfs.get_info()
            print(f"VFS name: {vfs_info['name']}")
            print(f"VFS SHA-256: {vfs_info['sha256']}")
        print("=" * 30)

    def run(self):
        if self.script_path:
            self.run_script()
        else:
            self.run_interactive()

    def run_interactive(self):
        while True:
            try:
                display_path = self._get_display_path()
                prompt = f"{self.user}@{self.hostname}:{display_path}$ "
                command_input = input(prompt).strip()

                if not command_input:
                    continue

                result = self.execute_command(command_input)
                if result is None:
                    break
                elif not result:
                    continue

            except KeyboardInterrupt:
                print("\n")
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

                if not command_line or command_line.startswith('#'):
                    continue

                display_path = self._get_display_path()
                print(f"{self.user}@{self.hostname}:{display_path}$ {command_line}")

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

    def _get_display_path(self):
        if self.current_path == "/":
            return "~"
        else:
            parts = [p for p in self.current_path.split('/') if p]
            return f"~/{parts[-1]}" if parts else "~"

    def _normalize_path(self, target_path):
        if target_path.startswith('/'):
            # Абсолютный путь
            path = target_path
        else:
            # Относительный путь
            if self.current_path == "/":
                path = f"/{target_path}"
            else:
                path = f"{self.current_path}/{target_path}"

        # Обрабатываем . и ..
        parts = []
        for part in path.split('/'):
            if part == '' or part == '.':
                continue
            elif part == '..':
                if parts:
                    parts.pop()
            else:
                parts.append(part)

        return '/' + '/'.join(parts) if parts else '/'

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
                return None
            else:
                print("Команда exit не принимает аргументы")
        elif command == 'ls':
            return self.ls(args)
        elif command == 'cd':
            return self.cd(args)
        elif command == 'help':
            self.help()
        elif command == 'vfs-info':
            self.vfs_info(args)
        elif command == 'cal':
            return self.cal(args)
        elif command == 'uniq':
            return self.uniq(args)
        elif command == 'uname':
            return self.uname(args)
        else:
            print(f"Ошибка: неизвестная команда '{command}'")
            if from_script:
                return False
        return True

    def ls(self, args):
        if not self.vfs.get_info()['loaded']:
            print("Ошибка: VFS не загружена")
            return False

        if args:
            if len(args) > 1:
                print("Ошибка: слишком много аргументов")
                return False
            target_path = self._normalize_path(args[0])
        else:
            target_path = self.current_path

        if not self.vfs.get_node(target_path):
            print(f"Ошибка: путь не существует: {target_path}")
            return False

        if not self.vfs.is_directory(target_path):
            print(f"Ошибка: не является директорией: {target_path}")
            return False

        items = self.vfs.list_directory(target_path)
        if items is None:
            print(f"Ошибка при чтении директории: {target_path}")
            return False

        if not items:
            print("Директория пуста")
        else:
            for item in sorted(items):
                print(item)

        return True

    def cd(self, args):
        if not self.vfs.get_info()['loaded']:
            print("Ошибка: VFS не загружена")
            return False

        if not args:
            self.current_path = "/"
            return True

        if len(args) > 1:
            print("Ошибка: слишком много аргументов")
            return False

        target_path = self._normalize_path(args[0])

        # Проверяем существование пути
        if not self.vfs.get_node(target_path):
            print(f"Ошибка: путь не существует: {target_path}")
            return False

        # Проверяем, что это директория
        if not self.vfs.is_directory(target_path):
            print(f"Ошибка: не является директорией: {target_path}")
            return False

        old_path = self.current_path
        self.current_path = target_path
        return True

    def cal(self, args):
        now = datetime.now()

        try:
            if len(args) == 0:
                # cal - текущий месяц
                print(calendar.month(now.year, now.month))
            elif len(args) == 1:
                # cal <год>
                year = int(args[0])
                if 1 <= year <= 9999:
                    print(calendar.calendar(year))
                else:
                    print("Ошибка: год должен быть в диапазоне 1-9999")
                    return False
            elif len(args) == 2:
                # cal <месяц> <год>
                month = int(args[0])
                year = int(args[1])
                if 1 <= month <= 12 and 1 <= year <= 9999:
                    print(calendar.month(year, month))
                else:
                    print("Ошибка: месяц должен быть 1-12, год 1-9999")
                    return False
            else:
                print("Ошибка: неверное количество аргументов")
                print("Использование: cal [год] или cal [месяц] [год]")
                return False
        except ValueError:
            print("Ошибка: аргументы должны быть числами")
            return False

        return True

    def uniq(self, args):
        if not args:
            print("Ошибка: укажите файл")
            return False

        if len(args) > 1:
            print("Ошибка: слишком много аргументов")
            return False

        file_path = self._normalize_path(args[0])

        if not self.vfs.get_info()['loaded']:
            print("Ошибка: VFS не загружена")
            return False

        # Читаем файл из VFS
        content = self.vfs.read_file(file_path)
        if content is None:
            print(f"Ошибка: файл не существует или не может быть прочитан: {file_path}")
            return False

        lines = content.split('\n')
        unique_lines = []
        previous_line = None

        for line in lines:
            if line != previous_line:
                unique_lines.append(line)
                previous_line = line

        for line in unique_lines:
            print(line)

        return True

    def uname(self, args):
        info = [
            f"Операционная система: {sys.platform}",
            f"Имя хоста: {self.hostname}",
            f"Пользователь: {self.user}",
            f"Python версия: {sys.version.split()[0]}"
        ]

        for line in info:
            print(line)

        return True

    def vfs_info(self, args):
        if args:
            print("Команда vfs-info не принимает аргументы")
            return

        info = self.vfs.get_info()
        if info['loaded']:
            print(f"VFS name: {info['name']}")
            print(f"SHA-256: {info['sha256']}")
        else:
            print("VFS не загружена")

    def help(self):
        print(" Доступные команды")
        print("  ls [путь] - показать содержимое директории")
        print("  cd [путь] - сменить директорию")
        print("  cal [год] или cal [месяц] [год] - вывод календаря")
        print("  uniq [файл] - фильтрация повторяющихся строк")
        print("  uname - информация о системе")
        print("  vfs-info - информация о загруженной VFS")
        print("  exit - выход из эмулятора")
        print("  help - показать эту справку")


def main():
    parser = argparse.ArgumentParser(description='Эмулятор командной строки')
    parser.add_argument('--vfs-path', '-v', help='Путь к XML файлу VFS')
    parser.add_argument('--script', '-s', help='Путь к стартовому скрипту')

    args = parser.parse_args()

    shell = ComLineEm(vfs_path=args.vfs_path, script_path=args.script)
    shell.run()


if __name__ == "__main__":
    main()