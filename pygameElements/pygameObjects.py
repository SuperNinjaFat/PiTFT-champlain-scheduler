import pandas
import matplotlib
import matplotlib.backends.backend_agg as agg
import os
import platform
import datetime
import socket
from enum import Enum
import pygame
from pygame.locals import *
import pylab
from climata.usgs import DailyValueIO
import requests
from bs4 import BeautifulSoup
from html.parser import HTMLParser

# import RPi.GPIO as GPIO

matplotlib.use("Agg")

# Base Directory
BASE_DIR = os.path.join(os.path.dirname(__file__), '..')

# PiTFT Screen Size (320x240)
SCREEN_SIZE = 320, 240

# PiTFT Button Map
button_map = {23: (255, 0, 0), 22: (0, 255, 0), 27: (0, 0, 255), 18: (0, 0, 0)}

# Setup the GPIOs as inputs with Pull Ups since the buttons are connected to GND
# GPIO.setmode(GPIO.BCM)
# for k in button_map.keys():
#     GPIO.setup(k, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# TODO: Once buttons are soldered on: https://web.archive.org/web/20151027165018/http://jeremyblythe.blogspot.com/2014/09/raspberry-pi-pygame-ui-basics.html

# Innitialize OS Screen
# os.environ["SDL_FBDEV"] = "/dev/fb1"
os.putenv('SDL_FBDEV', '/dev/fb1')
os.putenv('SDL_MOUSEDRV', 'TSLIB')
os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')

# Initialize Pygame
print("Before init")
pygame.init()
print("After init")
pygame.mouse.set_visible(False)
print("Before set_mode")
screen = pygame.display.set_mode(SCREEN_SIZE)
print("After set_mode")
# Initialize Events
pygame.time.set_timer(USEREVENT + 1, 28800000)  # Every 8 hours, download new data.
pygame.time.set_timer(USEREVENT + 2, 10000)  # 120000)  # Every 2 minutes, switch the surface.
pygame.time.set_timer(USEREVENT + 3, 6000)  # Every minute, refresh the clock.

# Fonts
# print(pygame.font.get_fonts())
# print(platform.node())
if platform.system() is 'Windows':
    print("Windows fonts")
    #  TODO: Fix directory access outside of local directory
    FONT_FALLOUT = pygame.font.Font('r_fallouty.ttf', 30)
    FONT_BM = pygame.font.Font('din1451alt.ttf', 8)
elif platform.system() is 'Linux':
    print("Linux fonts")
    FONT_FALLOUT = pygame.font.Font('resource/fonts/r_fallouty.ttf', 30)
    FONT_BM = pygame.font.Font('resource/fonts/din1451alt.ttf', 8)
else:
    print("default fonts")
    FONT_FALLOUT = pygame.font.SysFont(None, 30)
    FONT_BM = pygame.font.SysFont(None, 40)
#  TODO: Fix Font not working on Raspberry Pi
print("didn't it work??")

# colors
COLOR_BLACK = 0, 0, 0
COLOR_WHITE = 255, 255, 255
COLOR_GRAY_19 = 31, 31, 31
COLOR_GRAY_21 = 54, 54, 54
COLOR_GRAY_41 = 105, 105, 105
COLOR_ORANGE = 251, 126, 20
COLOR_LAVENDER = 230, 230, 250

# urls
URL_MAINSTREET = "https://www.mainstreetlanding.com"


# Content switching
class Content(Enum):
    TEMPERATURE = 1
    PICTURE = 2
    MAINSTREET = 3
    SHUTTLE = 4


class Card:
    def __init__(self, title="", desc="", dim=[0,0], img=pygame.image.load(os.path.join(BASE_DIR, 'resource', 'PiOffline.png'))):
        self.title = title
        self.desc = desc
        self.dim = dim
        self.img = img


# TODO: Error Checking requests.get() error
def downloadImage(output, address):
    f = open(os.path.join(BASE_DIR, 'resource', output), 'wb')
    f.write(requests.get(address).content)
    f.close()


class Environment:
    def __init__(self):
        # Initialize data buffers
        self.temp_data = None
        self.movies = []
        self.sponsor = Card
        # Surface buffer
        self.surf = None
        # Time Buffer
        self.time_text = (None, None)
        # Content Switcher (Temperature First)
        self.content = Content.TEMPERATURE

    def menu(self):
        # set time
        self.pullTime()
        # download data #TODO: See if I can move this into def __init__
        self.pullData()
        # Display Temperature first
        self.surf_startup()

        crashed = False
        while not crashed:
            for event in pygame.event.get():
                # Every 8 hours, download data
                if event.type == USEREVENT + 1:
                    self.pullData()
                # Every 2 minutes, change the surface
                if event.type == USEREVENT + 2:
                    if self.content is Content.TEMPERATURE:  # Next is TEMPERATURE
                        self.surf_plot()
                        self.content = Content.PICTURE  # Content(1 + self.content.value) # Next is PICTURE
                    elif self.content is Content.PICTURE:
                        self.surf_picture()
                        self.content = Content.MAINSTREET  # Content(1 + self.content.value)  # Next is MAINSTREET
                    elif self.content is Content.MAINSTREET:
                        self.surf_mainstreet()
                        self.content = Content.SHUTTLE  # Content(1 + self.content.value)  # Next is SHUTTLE
                    elif self.content is Content.SHUTTLE:
                        self.surf_shuttle()
                        self.content = Content.TEMPERATURE
                if event.type == USEREVENT + 3:
                    self.pullTime()
                if event.type == pygame.QUIT:
                    crashed = True
                # Quit
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
            self.refresh()

    def refresh(self):
        # Background
        screen.blit(self.surf, (0, 0))
        # Clock
        # Todo: make a backing to the text
        clockBacking = pygame.Rect((0, 0), (37, 10))
        pygame.draw.rect(screen, COLOR_WHITE, clockBacking, 0)
        # screen.blit(pygame.draw.rect(screen, COLOR_GRAY_19, clockBacking, 0), (4, 4))
        screen.blit(self.time_text[0], (2, 1))
        screen.blit(self.time_text[1], (23, 1))
        pygame.display.update()

    def surf_startup(self):
        print("Startup")
        image_startup = pygame.image.load(os.path.join(BASE_DIR, 'resource', 'PiOnline.png'))
        image_startup = pygame.transform.scale(image_startup, SCREEN_SIZE)
        # Set surface image
        self.surf = image_startup

    def surf_picture(self):
        # TODO: https://developers.google.com/drive/api/v3/manage-downloads
        # TODO: http://blog.vogella.com/2011/06/21/creating-bitmaps-from-the-internet-via-apache-httpclient/
        print("Picture Album")
        #  TODO: Display image in graph
        #  os.path.join(BASE_DIR, 'resource', 'burlington.jpg')
        # Set surface image
        self.surf = pygame.transform.scale(pygame.image.load(os.path.join(BASE_DIR, 'resource', 'burlington.jpg')), SCREEN_SIZE)
        pass

    def surf_mainstreet(self):
        # TODO: https://www.mainstreetlanding.com/performing-arts-center/daily-rental-information/movies-at-main-street-landing/
        # TODO: https://stackoverflow.com/questions/18294711/extracting-images-from-html-pages-with-python
        print("Mainstreet Landing Movies")
        # TODO: Make a sub-screen that allows you to flip through the content held in the movie cards.
        # and scroll through movie descriptions
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
            # Set surface image to offline
            self.surf = pygame.transform.scale(pygame.image.load(os.path.join(BASE_DIR, 'resource', 'PiOffline.png')),
                                               SCREEN_SIZE)

    def graph_temp(self):
        for series in self.temp_data:
            dates = [r[0] for r in series.data]
            flow = [r[1] for r in series.data]
        # render matplotgraph to bitmap
        fig = pylab.figure(figsize=[6.4, 4.8],  # Inches
                           dpi=50,  # 100 dots per inch, so the resulting buffer is 400x400 pixels
                           )
        ax = fig.gca()
        # Convert Celsius to Fahrenheit
        for i, cel in enumerate(flow):
            flow[i] = (cel * (9 / 5)) + 32
        # Format dates
        for i, day in enumerate(dates):
            dates[i] = '{:%b-%d\n(%a)}'.format(datetime.datetime.strptime(str(dates[i]), '%Y-%m-%d %H:%M:%S'))
        ax.grid(True)
        ax.plot(dates, flow)
        # print(flow)
        # print(dates)
        # Source name
        # fig.text(0.02, 0.5, series.variable_name, fontsize=10, rotation='vertical', verticalalignment='center')
        fig.text(0.02, 0.5, 'Water Temperature (\N{DEGREE SIGN}F)', fontsize=10, rotation='vertical',
                 verticalalignment='center')
        fig.text(0.5, 0.9, series.site_name, fontsize=18, horizontalalignment='center')
        fig.text(0.84, 0.81, str(round(flow[-1])) + '\N{DEGREE SIGN}F', fontsize=25,
                 bbox=dict(boxstyle="round", pad=0.1, fc='#ee8d18', ec="#a05d0c", lw=2))
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

        # Pull image and text data from mainstreetlanding.com
        html = requests.get(
            "https://www.mainstreetlanding.com/performing-arts-center/daily-rental-information/movies-at-main-street-landing/")
        soup = BeautifulSoup(html.text, features="html.parser")
        listings_raw = soup.findAll("article", {"class": "listing"})

        sponsor_raw = listings_raw.pop(-1)
        # download image (sponsor)
        downloadImage('sponsor.jpg', URL_MAINSTREET + "/" + str(sponsor_raw.contents[1].contents[1].contents[1].attrs['src']))
        self.sponsor = Card(
                               title=str(sponsor_raw.contents[1].contents[1].contents[1].attrs['alt']),
                               # TODO: Parse description html (maybe allow it to italicize when printing it?)
                               desc=str(sponsor_raw.contents[1].contents[3].contents[1]),
                               # TODO: Parse image src into html link, download the image,
                               # and pygame.image.load() it into 'Sponsor.img'.
                               # pygame.image.load(os.path.join(BASE_DIR, 'resource', 'PiOffline.png'))
                               img=pygame.image.load(os.path.join(BASE_DIR, 'resource', 'sponsor.jpg'))
                               )
        for listing in listings_raw:
            # download image (movies)
            m_image_name = 'movie' + str(listings_raw.index(listing)) + '.jpg'
            downloadImage(m_image_name,
                          URL_MAINSTREET + "/" + str(listing.contents[1].contents[1].contents[1].attrs['src']))
            self.movies.append(Card(
                                     title=str(listing.contents[1].contents[3].contents[1].contents[0]),
                                     # TODO: Parse description html (maybe allow it to italicize when printing it?)
                                     desc=str(listing.contents[1].contents[3].contents[5]),
                                     # TODO: Parse image src into html link, download the image,
                                     # and pygame.image.load() it into 'Movie.img'.
                                     # pygame.image.load(os.path.join(BASE_DIR, 'resource', 'PiOffline.png'))
                                     img=pygame.image.load(os.path.join(BASE_DIR, 'resource', m_image_name))
                                     ))

        # Pull image from Camnet
        downloadImage('burlington.jpg', 'https://hazecam.net/images/large/burlington_left.jpg')

    def pullTime(self):
        d = datetime.datetime.strptime(str(datetime.datetime.now().time()), "%H:%M:%S.%f")
        self.time_text = (FONT_BM.render(d.strftime("%I:%M"), True, COLOR_ORANGE), FONT_BM.render(d.strftime("%p"), True, COLOR_ORANGE))
