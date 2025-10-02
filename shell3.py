import os
import sys
import socket
import shlex
import argparse
import xml.etree.ElementTree as ET
import hashlib
import base64


class VFSNode:
    """Базовый класс для элементов VFS"""

    def __init__(self, name, path):
        self.name = name
        self.path = path


class VFSFile(VFSNode):
    """Файл в VFS"""

    def __init__(self, name, path, content="", encoding="text"):
        super().__init__(name, path)
        self.content = content
        self.encoding = encoding
        self.size = len(content)


class VFSFolder(VFSNode):
    """Папка в VFS"""

    def __init__(self, name, path):
        super().__init__(name, path)
        self.children = {}  # name -> VFSNode


class VirtualFileSystem:
    """Виртуальная файловая система"""

    def __init__(self):
        self.root = VFSFolder("", "/")
        self.name = ""
        self.raw_data = ""

    def load_from_xml(self, xml_path):
        """Загружает VFS из XML файла"""
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
        """Рекурсивно парсит XML и строит структуру VFS"""
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

                # Декодируем base64 если нужно
                if encoding == 'base64' and content:
                    try:
                        content = base64.b64decode(content).decode('utf-8')
                    except Exception as e:
                        print(f"Ошибка декодирования base64 файла {file_name}: {e}")

                new_file = VFSFile(file_name, file_path, content, encoding)
                current_folder.children[file_name] = new_file

    def calculate_sha256(self):
        """Вычисляет SHA-256 хеш данных VFS"""
        if not self.raw_data:
            return "N/A"
        return hashlib.sha256(self.raw_data.encode('utf-8')).hexdigest()

    def get_info(self):
        """Возвращает информацию о VFS"""
        return {
            'name': self.name,
            'sha256': self.calculate_sha256(),
            'loaded': bool(self.raw_data)
        }


class ComLineEm:
    def __init__(self, vfs_path=None, script_path=None):
        self.current_path = "~"
        self.user = os.getlogin()
        self.hostname = socket.gethostname()
        self.script_path = script_path
        self.vfs = VirtualFileSystem()  # НОВОЕ: создаем VFS

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
                return None
            else:
                print("Команда exit не принимает аргументы")
        elif command == 'ls':
            self.ls(args)
        elif command == 'cd':
            self.cd(args)
        elif command == 'help':
            self.help()
        elif command == 'vfs-info':  # НОВАЯ КОМАНДА
            self.vfs_info(args)
        else:
            print(f"Ошибка: неизвестная команда '{command}'")
            if from_script:
                return False
        return True

    def ls(self, args):

        if args:
            print(f"ls {args} (VFS: {self.vfs.get_info()['name']})")
        else:
            print(f"ls [] (VFS: {self.vfs.get_info()['name']})")

    def cd(self, args):

        if args:
            print(f"cd {args} (VFS: {self.vfs.get_info()['name']})")
        else:
            print(f"cd [] (VFS: {self.vfs.get_info()['name']})")

    def vfs_info(self, args):
        """Новая команда: информация о загруженной VFS"""
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
        print("  ls [аргументы] - показать содержимое директории")
        print("  cd [путь] - сменить директорию")
        print("  vfs-info - информация о загруженной VFS")  # НОВОЕ
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