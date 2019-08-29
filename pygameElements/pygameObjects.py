import pandas
import matplotlib
import matplotlib.backends.backend_agg as agg
import os
import platform
import datetime
import socket
from enum import Enum
import pygame
import requests
from pygame.locals import *
import pylab
from climata.usgs import DailyValueIO
# import RPi.GPIO as GPIO

matplotlib.use("Agg")

# Base Directory
BASE_DIR = os.path.join(os.path.dirname(__file__), '..')

# PiTFT Screen Size (320x240)
SCREEN_SIZE = 320, 240

button_map = {23: (255, 0, 0), 22: (0, 255, 0), 27: (0, 0, 255), 18: (0, 0, 0)}

# Setup the GPIOs as inputs with Pull Ups since the buttons are connected to GND
# GPIO.setmode(GPIO.BCM)
# for k in button_map.keys():
#     GPIO.setup(k, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# TODO: Once buttons are soldered on: https://web.archive.org/web/20151027165018/http://jeremyblythe.blogspot.com/2014/09/raspberry-pi-pygame-ui-basics.html

# Innitialize OS Screen
#os.environ["SDL_FBDEV"] = "/dev/fb1"
os.putenv('SDL_FBDEV', '/dev/fb1')
os.putenv('SDL_MOUSEDRV', 'TSLIB')
os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')

# Initialize Pygame
pygame.init()
pygame.mouse.set_visible(False)
screen = pygame.display.set_mode(SCREEN_SIZE)

# Initialize Events
pygame.time.set_timer(USEREVENT + 1, 28800000)  # Every 8 hours, download new data.
pygame.time.set_timer(USEREVENT + 2, 10000)#120000)  # Every 2 minutes, switch the surface.

# Fonts
# print(pygame.font.get_fonts())
# print(platform.node())
if platform.system() is 'Windows':
    print("Windows fonts")
#  TODO: Fix directory access outside of local directory
    FONT_FALLOUT = pygame.font.Font('r_fallouty.ttf', 30)
    FONT_BM = pygame.font.Font('din1451alt.ttf', 30)
elif platform.system() is 'Linux':
    print("Linux fonts")
    FONT_FALLOUT = pygame.font.Font('resource/fonts/r_fallouty.ttf', 30)
    FONT_BM = pygame.font.Font('resource/fonts/din1451alt.ttf', 30)
else:
    print("default fonts")
    FONT_FALLOUT = pygame.font.SysFont(None, 30)
    FONT_BM = pygame.font.SysFont(None, 40)
#  TODO: Fix Font not working on Raspberry Pi


# colors
COLOR_BLACK = 0, 0, 0
COLOR_GRAY_19 = 31, 31, 31
COLOR_GRAY_21 = 54, 54, 54
COLOR_GRAY_41 = 105, 105, 105
COLOR_ORANGE = 251, 126, 20
COLOR_LAVENDER = 230, 230, 250

# Content switching
class Content(Enum):
    TEMPERATURE = 1
    PICTURE = 2
    SHUTTLE = 3


class Environment:
    def __init__(self):
        # Initialize data buffers
        self.temp_data = None
        # Surface buffer
        self.surf = None
        # Time Buffer
        self.time_text = None
        # Content Switcher (Temperature First)
        self.content = Content.TEMPERATURE

    def menu(self):
        # download data #TODO: See if I can move this into def __init__
        self.pullData()
        #Display Temperature first
        self.surf_startup()

        crashed = False
        while not crashed:
            for event in pygame.event.get():
                # Every 8 hours, download data
                if event.type == USEREVENT + 1:
                    self.pullData()
                # Every 2 minutes, change the surface
                if event.type == USEREVENT + 2:
                    if self.content is Content.TEMPERATURE: # Next is TEMPERATURE
                        self.surf_plot()
                        self.content = Content.PICTURE #Content(1 + self.content.value) # Next is PICTURE
                    elif self.content is Content.PICTURE:
                        self.surf_picture()
                        self.content = Content.SHUTTLE #Content(1 + self.content.value)  # Next is SHUTTLE
                    elif self.content is Content.SHUTTLE:
                        self.surf_shuttle()
                        self.content = Content.TEMPERATURE
                if event.type == pygame.QUIT:
                    crashed = True
                # Quit
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
            self.refresh()

    def refresh(self):
        screen.blit(self.surf, (0, 0))

        d = datetime.datetime.strptime(str(datetime.datetime.now().time()), "%H:%M:%S.%f")
        self.time_text = FONT_BM.render(d.strftime("%I:%M:%S %p"), True, COLOR_ORANGE)
        screen.blit(self.time_text, (70, 20))
        pygame.display.update()

    def surf_startup(self):
        print("Startup")
        image_startup = pygame.image.load(os.path.join(BASE_DIR, 'resource', 'PiOnline.png'))
        image_startup = pygame.transform.scale(image_startup, SCREEN_SIZE)
        # Set surface image
        self.surf = image_startup

    def surf_picture(self):  # TODO: https://developers.google.com/drive/api/v3/manage-downloads
        # TODO: http://blog.vogella.com/2011/06/21/creating-bitmaps-from-the-internet-via-apache-httpclient/
        print("Picture Album")
        pass

    def surf_shuttle(self):  # TODO: https://shuttle.champlain.edu/
        print("Shuttle Map")
        pass

    def surf_plot(self):
        print("Lake Temperature")
        # window = pygame.display.set_mode(SCREEN_SIZE, DOUBLEBUF)
        # screen = pygame.display.get_surface()

        # Create list of date-flow values TODO: separate processes of re-downloading data and applying image
        if self.temp_data:
            self.surf = self.graph_temp()
        else:
            image_offline = pygame.image.load(os.path.join(BASE_DIR, 'resource', 'PiOffline.png'))
            image_offline = pygame.transform.scale(image_offline, SCREEN_SIZE)
            # Set surface image
            self.surf = image_offline

    def graph_temp(self):
        for series in self.temp_data:
            dates = [r[0] for r in series.data]  # TODO: Convert Celsius to Fahrenheit
            flow = [r[1] for r in series.data]
        # render matplotgraph to bitmap
        fig = pylab.figure(figsize=[6.4, 4.8],  # Inches
                           dpi=50,  # 100 dots per inch, so the resulting buffer is 400x400 pixels
                           )
        ax = fig.gca()
        for i, cel in enumerate(flow):
            flow[i] = (cel * (9/5)) + 32
        ax.grid(True)
        ax.plot(dates, flow)
        # print(flow)
        # print(dates)
        # Source name
        # fig.text(0.02, 0.5, series.variable_name, fontsize=10, rotation='vertical', verticalalignment='center')
        fig.text(0.02, 0.5, 'Water Temperature (\N{DEGREE SIGN}F)', fontsize=10, rotation='vertical',
                 verticalalignment='center')
        fig.text(0.5, 0.9, series.site_name, fontsize=18, horizontalalignment='center')
        fig.text(0.87, 0.82, str(round(flow[-1]))+'\N{DEGREE SIGN}F', fontsize=25,
                 bbox=dict(boxstyle="round4", pad=0.3, fc='#ee8d18', ec="b", lw=2))
        # TODO: better annotation:
        # https://matplotlib.org/users/annotations.html#plotting-guide-annotation
        # Draw raw data
        canvas = agg.FigureCanvasAgg(fig)
        canvas.draw()
        renderer = canvas.get_renderer()
        # size = canvas.get_width_height()
        raw_data = renderer.tostring_rgb()

        # close figure
        pylab.close(fig)
        # Set surface image
        return pygame.image.fromstring(raw_data, SCREEN_SIZE, "RGB")

    def pullData(self):
        ndays = 7
        station_id = "04294500"
        param_id = "00010"
        datelist = pandas.date_range(end=pandas.datetime.today(), periods=ndays).tolist()
        data = None  # https://www.earthdatascience.org/tutorials/acquire-and-visualize-usgs-hydrology-data/
        try:
            data = DailyValueIO(
                start_date=datelist[0],
                end_date=datelist[-1],
                station=station_id,
                parameter=param_id,
            )
        except (requests.exceptions.ConnectionError, socket.gaierror, ConnectionError) as e:
            print(e)
        self.temp_data = data
