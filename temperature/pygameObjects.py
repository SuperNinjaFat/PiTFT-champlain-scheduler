import os
import pygame

# Base Directory
BASE_DIR = os.path.join(os.path.dirname(__file__), '..')

# PiTFT Screen Size (320x240)
SCREEN_SIZE = 320, 240

pygame.init()
screen = pygame.display.set_mode(SCREEN_SIZE)

class Environment:
    # def __init__(self):
    #
    def menu(self):
        lock = True
        while lock:
            for event in pygame.event.get():
                print(event)
                if event.type == pygame.QUIT:
                    pygame.quit()
                    lock = False
            if lock:
                image_graph = pygame.image.load(os.path.join(BASE_DIR, 'resource', 'test_graph_1.png'))
                image_graph = pygame.transform.scale(image_graph, SCREEN_SIZE)
                screen.blit(image_graph, (0, 0))
                pygame.display.update()
