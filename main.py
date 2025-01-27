import pygame
import sys
import os
import json

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 1000, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Игра Алхимия")

# Colors
WHITE = (255, 255, 255)
GRAY = (200, 200, 200)
RED = (250, 0, 0)
LIGHT_BLUE = (173, 216, 230)
BLACK = (0, 0, 0)
TRANSPARENT = (0, 0, 0, 0)

# Fonts
font = pygame.font.SysFont(None, 24)
large_font = pygame.font.SysFont(None, 32)

# Load elements and combinations from JSON
with open("data/elements.json", "r", encoding="utf-8") as file:
    data = json.load(file)

unlocked_elements = ["Воздух", "Огонь", "Земля", "Вода"]
elements = data["elements"]
combinations = data["combinations"]

ELEMENT_SIZE = 50

# Load placeholder icon
placeholder_path = os.path.join("images", "placeholder.png")
if os.path.exists(placeholder_path):
    placeholder_icon = pygame.image.load(placeholder_path).convert_alpha()
    placeholder_icon = pygame.transform.smoothscale(placeholder_icon, (ELEMENT_SIZE, ELEMENT_SIZE))
else:
    raise FileNotFoundError("Placeholder image 'placeholder.png' not found in 'images' folder!")

# Отступы и размеры для левой панели
ROW_GAP = 20
PANEL_PADDING = 10
ELEMENT_PADDING = 15
ELEMENT_COLUMNS = 3  # Количество столбцов
COLUMN_WIDTH = (200 - PANEL_PADDING * 2) // ELEMENT_COLUMNS

# Распределяем элементы в панели
all_elements = []
for i, el in enumerate(elements):
    try:
        image_path = os.path.join("images", el["image"])
        if os.path.exists(image_path):
            image = pygame.image.load(image_path)
            image = pygame.transform.smoothscale(image, (ELEMENT_SIZE, ELEMENT_SIZE))
        else:
            raise FileNotFoundError
    except FileNotFoundError:
        image = placeholder_icon

    # Позиция на основе индекса
    col = i % ELEMENT_COLUMNS  # Номер столбца
    row = i // ELEMENT_COLUMNS  # Номер строки
    x = PANEL_PADDING + col * COLUMN_WIDTH + (COLUMN_WIDTH - ELEMENT_SIZE) // 2
    y = 50 + row * (ELEMENT_SIZE + ELEMENT_PADDING)

    all_elements.append({"name": el["name"], "icon": image, "pos": [x, y]})

# Trash can dimensions and position
TRASH_CAN_SIZE = 80
trash_x = (WIDTH + 200) // 2 - TRASH_CAN_SIZE // 2
trash_y = HEIGHT - TRASH_CAN_SIZE - 10
trash_rect = pygame.Rect(trash_x, trash_y, TRASH_CAN_SIZE, TRASH_CAN_SIZE)

# Interactive elements on the field
field_elements = []
dragged_element = None
drag_offset = (0, 0)

# Animation variables
animations = []  # Holds animations like removal or combination


def get_element_position(index, cols=3, spacing=20, x_start=20, y_start=50):
    """Рассчитывает позицию элемента в сетке."""
    row = index // cols
    col = index % cols
    x = x_start + col * (ELEMENT_SIZE + spacing)
    y = y_start + row * (ELEMENT_SIZE + spacing)
    return x, y


def combine_elements(el1, el2):
    """Обработка комбинации двух элементов."""
    combo_key = f"{el1['name']}+{el2['name']}"
    if combo_key in combinations:
        new_name = combinations[combo_key]

        # Проверяем, открыт ли элемент
        if new_name not in unlocked_elements:
            unlocked_elements.append(new_name)
            print(f"Новый элемент открыт: {new_name}")

        # Найти данные о новом элементе в JSON
        new_element_data = next((el for el in elements if el["name"] == new_name), None)

        # Попытка загрузить изображение для нового элемента
        if new_element_data:
            try:
                image_path = os.path.join("images", new_element_data["image"])
                if os.path.exists(image_path):
                    new_icon = pygame.image.load(image_path).convert_alpha()
                    new_icon = pygame.transform.smoothscale(new_icon, (ELEMENT_SIZE, ELEMENT_SIZE))
                else:
                    print(f"Image not found for element: {new_name} ({image_path}). Using placeholder.")
                    raise FileNotFoundError
            except FileNotFoundError:
                new_icon = placeholder_icon  # Использовать placeholder, если изображение отсутствует
        else:
            new_icon = placeholder_icon  # Использовать placeholder, если данных нет

        # Создаем новый элемент на поле
        new_element = {
            "name": new_name,
            "icon": new_icon,  # По умолчанию - шаблонная иконка
            "pos": el1["pos"]
        }

        return new_element
    return None


def render_unlocked_elements():
    """Отображение открытых элементов в панели в виде сетки."""
    cols = 3  # Количество столбцов
    spacing = 20  # Расстояние между элементами
    size = ELEMENT_SIZE  # Размер иконки

    # Начальная позиция
    x_start = 20
    y_start = 50

    for i, element_name in enumerate(unlocked_elements):
        row = i // cols
        col = i % cols
        x = x_start + col * (size + spacing)
        y = y_start + row * (size + spacing)

        # Получаем иконку элемента
        icon = next(el["icon"] for el in all_elements if el["name"] == element_name)
        screen.blit(icon, (x, y))

        # Подпись под элементом
        # label = font.render(element_name, True, BLACK)
        # label_x = x + size // 2 - label.get_width() // 2
        # label_y = y + size + 5
        # screen.blit(label, (label_x, label_y))


def animate_removal(element):
    """Animate removal of an element (shrinks and fades out)."""
    start_pos = element["pos"]
    duration = 300  # Milliseconds
    animations.append({
        "type": "removal",
        "start_time": pygame.time.get_ticks(),
        "duration": duration,
        "element": element,
        "start_pos": start_pos,
    })


def animate_combination(new_element, pos, callback):
    """Animate the appearance of a new element (grows and fades in)."""
    duration = 300
    animations.append({
        "type": "combination",
        "start_time": pygame.time.get_ticks(),
        "duration": duration,
        "element": new_element,
        "pos": pos,
        "callback": callback,
    })


def draw_animations():
    """Обрабатывает анимации добавления и удаления элементов."""
    current_time = pygame.time.get_ticks()
    completed_animations = []

    for anim in animations:
        elapsed = current_time - anim["start_time"]
        progress = min(1, elapsed / anim["duration"])  # Прогресс от 0 до 1

        if anim["type"] == "removal":
            element = anim["element"]
            scale = 1 - progress  # Сжатие до нуля
            alpha = int(255 * (1 - progress))  # Прозрачность уменьшается
            icon = element["icon"].copy()
            icon = pygame.transform.smoothscale(icon, (int(ELEMENT_SIZE * scale), int(ELEMENT_SIZE * scale)))
            icon.set_alpha(alpha)
            x, y = anim["start_pos"]
            screen.blit(icon, (x + (ELEMENT_SIZE - icon.get_width()) // 2, y + (ELEMENT_SIZE - icon.get_height()) // 2))

            if progress == 1:
                completed_animations.append(anim)

        elif anim["type"] == "combination":
            element = anim["element"]
            scale = progress  # Увеличение от нуля до нормального размера
            alpha = int(255 * progress)  # Прозрачность увеличивается
            icon = element["icon"].copy()
            icon = pygame.transform.smoothscale(icon, (int(ELEMENT_SIZE * scale), int(ELEMENT_SIZE * scale)))
            icon.set_alpha(alpha)
            x, y = anim["pos"]
            screen.blit(icon, (x + (ELEMENT_SIZE - icon.get_width()) // 2, y + (ELEMENT_SIZE - icon.get_height()) // 2))

            if progress == 1:
                if anim.get("callback"):
                    anim["callback"]()  # Выполнить callback
                completed_animations.append(anim)

    # Удаление завершённых анимаций
    for anim in completed_animations:
        animations.remove(anim)


# Обновление основного цикла
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Drag and drop
        elif event.type == pygame.MOUSEBUTTONDOWN:
            for element in all_elements + field_elements:
                rect = pygame.Rect(element["pos"], (ELEMENT_SIZE, ELEMENT_SIZE))
                if rect.collidepoint(event.pos):
                    dragged_element = element
                    drag_offset = (element["pos"][0] - event.pos[0], element["pos"][1] - event.pos[1])
                    if element in all_elements:  # Если перетаскивается с панели, клонируем
                        if element["name"] in unlocked_elements:
                            new_element = {"name": element["name"], "icon": element["icon"], "pos": list(event.pos)}
                            field_elements.append(new_element)
                            dragged_element = new_element
                    break


        elif event.type == pygame.MOUSEBUTTONUP:
            if dragged_element:
                # Проверка, попала ли точка в область корзины
                if trash_rect.collidepoint(event.pos) and dragged_element in field_elements:
                    animate_removal(dragged_element)
                    field_elements.remove(dragged_element)

                dragged_element = None


        elif event.type == pygame.MOUSEMOTION:
            if dragged_element and dragged_element in field_elements:
                dragged_element["pos"][0] = event.pos[0] + drag_offset[0]
                dragged_element["pos"][1] = event.pos[1] + drag_offset[1]

    # Проверка на комбинации
    for i, el1 in enumerate(field_elements):
        for j, el2 in enumerate(field_elements):
            if i != j:
                rect1 = pygame.Rect(el1["pos"], (ELEMENT_SIZE, ELEMENT_SIZE))
                rect2 = pygame.Rect(el2["pos"], (ELEMENT_SIZE, ELEMENT_SIZE))
                if rect1.colliderect(rect2):
                    new_element = combine_elements(el1, el2)
                    if new_element:
                        field_elements.remove(el1)
                        field_elements.remove(el2)


                        def add_new_element():
                            field_elements.append(new_element)


                        animate_combination(new_element, el1["pos"], callback=add_new_element)
                        break

    # Рендеринг
    screen.fill(LIGHT_BLUE)
    pygame.draw.rect(screen, GRAY, (0, 0, 200, HEIGHT))  # Левая панель
    pygame.draw.rect(screen, RED, (trash_x, trash_y, TRASH_CAN_SIZE, TRASH_CAN_SIZE))  # Корзина

    # Заголовок панели
    unlocked_label = large_font.render("Открытые элементы", True, BLACK)
    screen.blit(unlocked_label, (10, 10))

    # Рендеринг открытых элементов
    render_unlocked_elements()

    # Рендеринг элементов на поле
    for element in field_elements:
        screen.blit(element["icon"], element["pos"])
        label = font.render(element["name"], True, BLACK)
        label_x = element["pos"][0] + ELEMENT_SIZE // 2 - label.get_width() // 2
        label_y = element["pos"][1] + ELEMENT_SIZE + 5
        screen.blit(label, (label_x, label_y))

    # Рендеринг анимаций
    draw_animations()

    # Обновление экрана
    pygame.display.flip()

pygame.quit()
sys.exit()

# все дело в том что element["pos"] используется даже в анимациях, то есть когда элемент уже где на поле для соединения, соответственно надо всегда хранить позицию, надо как то исправить эту часть кода
