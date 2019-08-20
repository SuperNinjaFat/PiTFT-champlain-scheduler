import os
import datetime
import pygame
from pygame.locals import *
import matplotlib
import matplotlib.backends.backend_agg as agg
import pylab
from climata.usgs import DailyValueIO
import pandas
matplotlib.use("Agg")

# Base Directory
BASE_DIR = os.path.join(os.path.dirname(__file__), '..')

# PiTFT Screen Size (320x240)
SCREEN_SIZE = 320, 240

pygame.init()
pygame.time.set_timer(USEREVENT+1, 28800000) # Every 8 hours, update

screen = pygame.display.set_mode(SCREEN_SIZE)

# Fonts
FONT_TIME = pygame.font.Font('r_fallouty.ttf', 30) #TODO: Fix directory access outside of local directory

# colors
COLOR_BLACK = 0, 0, 0
COLOR_GRAY_19 = 31, 31, 31
COLOR_GRAY_21 = 54, 54, 54
COLOR_GRAY_41 = 105, 105, 105
COLOR_ORANGE = 251, 126, 20
COLOR_LAVENDER = 230, 230, 250

class Environment:
    def __init__(self):
        self.surf = None
        self.time_text = None
    def menu(self):
        self.plot()

        crashed = False
        while not crashed:
            for event in pygame.event.get():
                if event.type == USEREVENT + 1:
                    self.plot()
                if event.type == pygame.QUIT:
                    crashed = True
            self.refresh()

    def refresh(self):
        screen.blit(self.surf, (0, 0))

        d = datetime.datetime.strptime(str(datetime.datetime.now().time()), "%H:%M:%S.%f")
        self.time_text = FONT_TIME.render(d.strftime("%I:%M:%S %p"), True, COLOR_ORANGE)
        screen.blit(self.time_text, (70, 20))
        pygame.display.update()

    def plot(self):
        print("plot")
        ndays = 7
        station_id = "04294500"
        param_id = "00010"
        datelist = pandas.date_range(end=pandas.datetime.today(), periods=ndays).tolist()
        data = DailyValueIO(
            start_date=datelist[0],
            end_date=datelist[-1],
            station=station_id,
            parameter=param_id,
        )
        # Create list of date-flow values
        for series in data:
            flow = [r[0] for r in series.data]
            dates = [r[1] for r in series.data]

        # render matplotgraph to bitmap
        fig = pylab.figure(figsize=[6.4, 4.8],  # Inches
                           dpi=50,  # 100 dots per inch, so the resulting buffer is 400x400 pixels
                           )
        ax = fig.gca()
        ax.plot(flow, dates)
        # print(flow)
        # print(dates)
        # Source name
        # fig.text(0.02, 0.5, series.variable_name, fontsize=10, rotation='vertical', verticalalignment='center')
        fig.text(0.02, 0.5, 'Water Temperature (\N{DEGREE SIGN}C)', fontsize=10, rotation='vertical',
                 verticalalignment='center')
        fig.text(0.5, 0.9, series.site_name, fontsize=18, horizontalalignment='center')

        # Draw raw data
        canvas = agg.FigureCanvasAgg(fig)
        canvas.draw()
        renderer = canvas.get_renderer()
        raw_data = renderer.tostring_rgb()

        window = pygame.display.set_mode(SCREEN_SIZE, DOUBLEBUF)
        screen = pygame.display.get_surface()

        size = canvas.get_width_height()

        # Set surface image TODO: Make a timer increment ever so often to re-download and apply this image
        self.surf = pygame.image.fromstring(raw_data, size, "RGB")

        # image_graph = pygame.image.load(os.path.join(BASE_DIR, 'resource', 'test_graph_1.png'))
        # image_graph = pygame.transform.scale(image_graph, SCREEN_SIZE)
        # screen.blit(image_graph, (0, 0))