import pygame
import sys
import os
import json

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Игра Алхимия")

# Colors
WHITE = (255, 255, 255)
GRAY = (200, 200, 200)
BLACK = (0, 0, 0)

# Fonts
font = pygame.font.SysFont(None, 24)
large_font = pygame.font.SysFont(None, 36)

# Load elements and combinations from JSON
with open("data/elements.json", "r") as file:
    data = json.load(file)

elements = data["elements"]
combinations = data["combinations"]

# Load placeholder icon
ELEMENT_SIZE = 50
placeholder_icon = pygame.Surface((ELEMENT_SIZE, ELEMENT_SIZE))
placeholder_icon.fill((150, 150, 150))  # Gray background for placeholder
placeholder_label = font.render("?", True, BLACK)
label_x = (ELEMENT_SIZE - placeholder_label.get_width()) // 2
label_y = (ELEMENT_SIZE - placeholder_label.get_height()) // 2
placeholder_icon.blit(placeholder_label, (label_x, label_y))

# Load element images
all_elements = []
for el in elements:
    try:
        image_path = os.path.join("images", el["image"])
        if os.path.exists(image_path):  # Check if the image exists
            image = pygame.image.load(image_path)
            image = pygame.transform.scale(image, (ELEMENT_SIZE, ELEMENT_SIZE))
        else:
            raise FileNotFoundError  # Use placeholder if image is missing
    except FileNotFoundError:
        image = placeholder_icon

    all_elements.append({"name": el["name"], "icon": image, "pos": [10, 50 + len(all_elements) * 70]})

# Trash can dimensions and position
TRASH_CAN_SIZE = 80
trash_x = (WIDTH + 200) // 2 - TRASH_CAN_SIZE // 2
trash_y = HEIGHT - TRASH_CAN_SIZE - 10

# Interactive elements on the field
field_elements = []
dragged_element = None
drag_offset = (0, 0)

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Drag and drop handling
        elif event.type == pygame.MOUSEBUTTONDOWN:
            for element in all_elements + field_elements:
                rect = pygame.Rect(element["pos"], (ELEMENT_SIZE, ELEMENT_SIZE))
                if rect.collidepoint(event.pos):
                    dragged_element = element
                    drag_offset = (element["pos"][0] - event.pos[0], element["pos"][1] - event.pos[1])
                    if element in all_elements:  # Clone element if dragged from panel
                        new_element = element.copy()
                        new_element["pos"] = event.pos
                        field_elements.append(new_element)
                    break

        elif event.type == pygame.MOUSEBUTTONUP:
            if dragged_element:
                # Check if dropped in trash can
                trash_rect = pygame.Rect(trash_x, trash_y, TRASH_CAN_SIZE, TRASH_CAN_SIZE)
                if trash_rect.collidepoint(event.pos):
                    if dragged_element in field_elements:
                        field_elements.remove(dragged_element)

                dragged_element = None

        elif event.type == pygame.MOUSEMOTION:
            if dragged_element and dragged_element in field_elements:
                dragged_element["pos"][0] = event.pos[0] + drag_offset[0]
                dragged_element["pos"][1] = event.pos[1] + drag_offset[1]

    # Check for collisions on the field
    for i, el1 in enumerate(field_elements):
        for j, el2 in enumerate(field_elements):
            if i != j:
                rect1 = pygame.Rect(el1["pos"], (ELEMENT_SIZE, ELEMENT_SIZE))
                rect2 = pygame.Rect(el2["pos"], (ELEMENT_SIZE, ELEMENT_SIZE))
                if rect1.colliderect(rect2):
                    combo_key = f"{el1['name']}+{el2['name']}"
                    if combo_key in combinations:
                        new_name = combinations[combo_key]
                        new_element = {
                            "name": new_name,
                            "icon": placeholder_icon,  # Placeholder until custom icon is added
                            "pos": el1["pos"]
                        }
                        field_elements.append(new_element)
                        field_elements.remove(el1)
                        field_elements.remove(el2)
                        break

    # Draw background and panels
    screen.fill(WHITE)
    pygame.draw.rect(screen, GRAY, (0, 0, 200, HEIGHT))  # Left panel
    pygame.draw.rect(screen, GRAY, (trash_x, trash_y, TRASH_CAN_SIZE, TRASH_CAN_SIZE))  # Trash can

    # Draw trash label
    trash_label = large_font.render("Корзина", True, BLACK)
    screen.blit(trash_label, (trash_x + 5, trash_y + 5))

    # Draw unlocked elements panel
    unlocked_label = large_font.render("Открытые элементы", True, BLACK)
    screen.blit(unlocked_label, (10, 10))

    for element in all_elements:
        screen.blit(element["icon"], element["pos"])
        label = font.render(element["name"], True, BLACK)
        label_x = element["pos"][0] + ELEMENT_SIZE // 2 - label.get_width() // 2
        label_y = element["pos"][1] + ELEMENT_SIZE + 5
        screen.blit(label, (label_x, label_y))

    # Draw field elements
    for element in field_elements:
        screen.blit(element["icon"], element["pos"])
        label = font.render(element["name"], True, BLACK)
        label_x = element["pos"][0] + ELEMENT_SIZE // 2 - label.get_width() // 2
        label_y = element["pos"][1] + ELEMENT_SIZE + 5
        screen.blit(label, (label_x, label_y))

    # Update display
    pygame.display.flip()

pygame.quit()
sys.exit()
