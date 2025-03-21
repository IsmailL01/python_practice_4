import json
import threading
import time
from datetime import datetime


DATA_FILE = "users_data.json"
LOG_FILE = "app.log"


lock = threading.Lock()


class Logger(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.log_queue = []
        self.running = True

    def log(self, level, username, message):
        timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        log_entry = f"[{level}] [{timestamp}] [{username}] - {message}\n"
        with lock:
            self.log_queue.append(log_entry)

    def run(self):
        while self.running:
            if self.log_queue:
                with lock:
                    with open(LOG_FILE, "a") as file:
                        file.writelines(self.log_queue)
                    self.log_queue.clear()
            time.sleep(3)

    def stop(self):
        self.running = False
        self.run()

logger = Logger()
logger.start()


def load_data():
    with lock:
        try:
            with open(DATA_FILE, "r") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}


def save_data():
    def save():
        with lock:
            with open(DATA_FILE, "w") as file:
                json.dump(users, file, indent=4)
    
    threading.Thread(target=save, daemon=True).start()


users = load_data()

class User:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.tasks = users.get(username, {}).get("tasks", [])

    def add_task(self, task):
        self.tasks.append({"task": task, "done": False})
        logger.log("INFO", self.username, f"Добавлена задача: {task}")
        save_data()

    def remove_task(self, index):
        try:
            task = self.tasks.pop(index)
            logger.log("INFO", self.username, f"Удалена задача: {task['task']}")
            save_data()
        except IndexError:
            logger.log("ERROR", self.username, f"Ошибка удаления задачи: неверный индекс {index}")

    def complete_task(self, index):
        try:
            self.tasks[index]["done"] = True
            logger.log("INFO", self.username, f"Задача выполнена: {self.tasks[index]['task']}")
            save_data()
        except IndexError:
            logger.log("ERROR", self.username, f"Ошибка выполнения задачи: неверный индекс {index}")

    def show_tasks(self):
        for i, task in enumerate(self.tasks, 1):
            status = "✔" if task["done"] else "✘"
            print(f"{i}. [{status}] {task['task']}")


def auto_save():
    while True:
        time.sleep(10)
        save_data()

threading.Thread(target=auto_save, daemon=True).start()

def register():
    username = input("Введите имя пользователя: ")
    if username in users:
        print("Пользователь уже существует!")
        return None
    password = input("Введите пароль: ")
    users[username] = {"password": password, "tasks": []}
    save_data()
    print("Регистрация успешна!")
    return username

def login():
    username = input("Введите имя пользователя: ")
    password = input("Введите пароль: ")
    if username in users and users[username]["password"] == password:
        print("Вход выполнен!")
        return username
    print("Неверные данные!")
    return None

def main():
    print("1. Регистрация\n2. Вход")
    choice = input("Выберите действие: ")
    user = None
    
    if choice == "1":
        user = register()
    elif choice == "2":
        user = login()
    
    if not user:
        return
    
    current_user = User(user, users[user]["password"])
    
    while True:
        print("\n1. Добавить задачу\n2. Удалить задачу\n3. Отметить задачу выполненной\n4. Показать задачи\n5. Выйти")
        action = input("Выберите действие: ")
        if action == "1":
            task = input("Введите задачу: ")
            current_user.add_task(task)
        elif action == "2":
            index = int(input("Введите номер задачи: "))
            current_user.remove_task(index - 1)
        elif action == "3":
            index = int(input("Введите номер задачи: "))
            current_user.complete_task(index - 1)
        elif action == "4":
            current_user.show_tasks()
        elif action == "5":
            save_data()
            logger.stop()
            print("Выход из программы...")
            break
        else:
            print("Неверный ввод!")

if __name__ == "__main__":
    main()
