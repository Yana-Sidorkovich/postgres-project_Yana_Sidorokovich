from datetime import datetime


class Room:

    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name

    def __repr__(self):
        return f"Room(id={self.id}, name='{self.name}')"


class Student:

    def __init__(self, id: int, name: str, birthday: str, sex: str, room: int):
        self.id = id
        self.name = name
        self.birthday = birthday
        self.sex = sex
        self.room = room

    def get_age(self) -> int:
        # Обрезаем время, оставляем только дату
        birth_date = datetime.fromisoformat(self.birthday.split('T')[0])
        today = datetime.now()
        age = today.year - birth_date.year
        # Корректируем, если день рождения ещё не был в этом году
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            age -= 1
        return age

    def __repr__(self):
        return f"Student(id={self.id}, name='{self.name}', age={self.get_age()})"
