import datetime
MIN_STOCK = 3 #мин остаток

def validate_material(name, category, quantity):
    """Проверяет корректность введённых данных."""
    if not name.strip():
        return "Ошибка: название материала не может быть пустым."
    if not category.strip():
        return "Ошибка: категория не может быть пустой."
    if quantity <= 0:
        return "Ошибка: количество должно быть больше нуля."
    return "OK"

def add_material(name, category, quantity):
    """Добавляет материал в учёт и возвращает карточку материала."""
    material = {
        "name": name,
        "category": category,
        "quantity": quantity,
        "added_at": datetime.date.today()
    }
    return material

def show_material(material):
    """Выводит информацию о материале."""
    print("Карточка материала-->")
    print(f"Название:  {material['name']}")
    print(f"Категория: {material['category']}")
    print(f"Количество: {material['quantity']} шт.")
    print(f"Добавлен:  {material['added_at']}")

def check_low_stock(material):
    """Отслеживает материалы с малым остатком."""
    if material["quantity"] <= MIN_STOCK:
        return f"Внимание: материал «{material['name']}» заканчивается!"
    return f"Материал «{material['name']}» в достаточном количестве."

print("Добавление нового материала для творчества")

name = input("Введите название материала: ")
category = input("Введите категорию: ")
quantity_str = input("Введите количество: ")

if not quantity_str.isdigit():
    print("Ошибка: количество должно быть целым числом.")
else:
    quantity = int(quantity_str)
    status = validate_material(name, category, quantity)

    if status == "OK":
        material = add_material(name, category, quantity)
        show_material(material)
        print(check_low_stock(material))
    else:
        print(status)