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
import sys
if platform.system() == "Windows":
    import fake_rpi
    sys.modules['RPi'] = fake_rpi.RPi     # Fake RPi (GPIO)
    sys.modules['smbus'] = fake_rpi.smbus # Fake smbus (I2C)
    from fake_rpi import toggle_print
    toggle_print(False)
# if platform.system() == "Linux":
from RPi import GPIO

matplotlib.use("Agg")

# Base Directory
BASE_DIR = os.path.join(os.path.dirname(__file__), '..')

# PiTFT Screen Dimension (320x240)
DIM_SCREEN = 320, 240
DIM_ICON = 10, 10  # Icon Dimensions

# PiTFT Button Map
button_map = (23, 22, 27, 18)

# Setup the GPIOs as inputs with Pull Ups since the buttons are connected to GND
GPIO.setmode(GPIO.BCM)
# GPIO.setmode(io.BCM)
for k in button_map:
    GPIO.setup(k, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# TODO: Once buttons are soldered on: https://web.archive.org/web/20151027165018/http://jeremyblythe.blogspot.com/2014/09/raspberry-pi-pygame-ui-basics.html

# Initialize OS Screen
os.putenv('SDL_FBDEV', '/dev/fb1')
os.putenv('SDL_MOUSEDRV', 'TSLIB')
os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')

# Initialize Pygame
pygame.init()
pygame.mouse.set_visible(False)
# Initialize Events
pygame.time.set_timer(USEREVENT + 1, 28800000)  # Every 8 hours, download new data.
pygame.time.set_timer(USEREVENT + 2, 10000)  # 10 seconds # 120000)  # Every 2 minutes, switch the surface.
pygame.time.set_timer(USEREVENT + 3, 6000)  # Every minute, refresh the clock.
# pygame.time.set_timer(USEREVENT + 4, 0)  # Not an event that needs to be set here, but just pointing out it exists.
# pygame.time.set_timer(USEREVENT + 5, 0)  # Not an event that needs to be set here, but just pointing out it exists.

# Fonts
# print(pygame.font.get_fonts())
if platform.system() == "Windows":
    print("Windows fonts")
    #  TODO: Fix directory access outside of local directory
    FONT_FALLOUT = pygame.font.Font('r_fallouty.ttf', 30)
    FONT_BM = pygame.font.Font('din1451alt.ttf', 10)
elif platform.system() == "Linux":
    print("Linux fonts")
    FONT_FALLOUT = pygame.font.Font('resource/fonts/r_fallouty.ttf', 30)
    FONT_BM = pygame.font.Font('resource/fonts/din1451alt.ttf', 10)
else:
    print("default fonts")
    FONT_FALLOUT = pygame.font.SysFont(None, 30)
    FONT_BM = pygame.font.SysFont(None, 13)
#  TODO: Fix Font not working on Raspberry Pi

screen = pygame.display.set_mode(DIM_SCREEN)

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

# Icon Constants
ICON_SLIDESHOW = 0  # Slideshow Icon
ICON_TEST = 1  # Slideshow Icon

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

        self.surf = None  # Surface buffer
        self.time_text = (None, None)  # Time Buffer
        self.slideshow = True  # slideshow toggler
        self.buttonDelay = False  # Button delay
        self.backlight = True  # Backlight is On
        self.nextContent = Content.TEMPERATURE  # Content Switcher (Temperature First)
        # Icons
        self.icon = [pygame.transform.scale(pygame.image.load(os.path.join(BASE_DIR, 'resource', 'mode_slideshow.png')), DIM_ICON),  # Slideshow
                     pygame.transform.scale(pygame.image.load(os.path.join(BASE_DIR, 'resource', 'Mana.png')), DIM_ICON)  # Test
                     ]
        # Pull data from internet/system
        self.pullTime()  # set time
        self.pullData()  # download data

        # You have to run a set-surface function before the slides start up.
        self.surf_startup()  # Start with lake temperature
        if platform.system() == "Linux":
            # Only use the sleep function for the raspberry pi
            pygame.time.set_timer(USEREVENT + 5, 60000)  # 1 minute # 600000) # 10 minutes

    def menu(self):
        crashed = False
        while not crashed:
            for event in pygame.event.get():
                # Every 8 hours, download data
                if event.type == USEREVENT + 1:  # Activated every 2 minutes to change the surface
                    self.pullData()
                if event.type == USEREVENT + 2:
                    self.setContent()
                if event.type == USEREVENT + 3:
                    self.pullTime()  # TODO: Make time toggleable and an options menu to do it.
                if event.type == USEREVENT + 4:
                    self.buttonDelay = False  # Button time buffer
                    pygame.time.set_timer(USEREVENT + 4, 0)  # TODO: Update to pygame 2.0.0dev3 to upgrade pygame.time.set_timer()
                if event.type == USEREVENT + 5:
                    # self.backlight = True
                    # self.backlight_toggle()  # Turn Backlight Off
                    os.system("sudo sh -c \'echo \"0\" > /sys/class/backlight/soc\:backlight/brightness\'")  # Off
                    self.backlight = False  # "backlight is not on"
                    pygame.time.set_timer(USEREVENT + 5, 0)  # Shut off sleep timer
                if event.type == pygame.QUIT:
                    crashed = True

                # Quit
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
            # Scan the buttons
            for k in button_map:
                if not GPIO.input(k) and platform.system() == "Linux" and not self.buttonDelay:
                    if k == button_map[0]:
                        pygame.quit()
                    if k == button_map[1]:
                        self.toggleSlideshow()
                    if k == button_map[2]:
                        self.setContent(prev=True)
                        pygame.time.set_timer(USEREVENT + 2, 10000)  # 10 seconds
                    if k == button_map[3]:
                        self.setContent()
                        pygame.time.set_timer(USEREVENT + 2, 10000)  # 10 seconds
                    self.buttonDelay = True
                    pygame.time.set_timer(USEREVENT + 4, 200)
                    # Whenever the user presses a button/interacts with the device, reset the sleep event.
                    pygame.time.set_timer(USEREVENT + 5, 60000)  # 1 minute # 600000) # 10 minutes
                    # Prevents the backlight from constantly getting set on instead of just to turn it back on.
                    if not self.backlight:  # if "backlight turn-on has been tripped"
                        os.system("sudo sh -c \'echo \"1\" > /sys/class/backlight/soc\:backlight/brightness\'")  # On
                        self.backlight = True  # "backlight turn-on has been tripped"
            self.refresh()

    def backlight_toggle(self):
        if self.backlight:
            os.system("sudo sh -c \'echo \"0\" > /sys/class/backlight/soc\:backlight/brightness\'")  # if bool, turn Off
        else:
            os.system(
                "sudo sh -c \'echo \"1\" > /sys/class/backlight/soc\:backlight/brightness\'")  # if not bool, turn On

    def setContent(self, prev=False):
        if prev:
            if self.nextContent.value == self.nextContent.value - 1:
                self.nextContent = Content.SHUTTLE
            else:
                self.nextContent = self.nextContent.value - 1
        if self.nextContent is Content.TEMPERATURE:  # Next is TEMPERATURE
            self.surf_plot()
            self.nextContent = Content.PICTURE  # Content(1 + self.content.value) # Next is PICTURE
        elif self.nextContent is Content.PICTURE:
            self.surf_picture()
            self.nextContent = Content.MAINSTREET  # Content(1 + self.content.value)  # Next is MAINSTREET
        elif self.nextContent is Content.MAINSTREET:
            self.surf_mainstreet()
            self.nextContent = Content.SHUTTLE  # Content(1 + self.content.value)  # Next is SHUTTLE
        elif self.nextContent is Content.SHUTTLE:
            self.surf_shuttle()
            self.nextContent = Content.TEMPERATURE

    def refresh(self):
        screen.blit(self.surf, (0, 0))  # Background

        # Icons Todo: make icon bar toggleable in options
        pygame.draw.rect(screen, COLOR_WHITE, pygame.Rect((0, 0), (DIM_SCREEN[0], 13)), 0)  # Icon bar backing
        if self.buttonDelay:
            screen.blit(self.icon[ICON_TEST], (56, 1))
        if self.slideshow:
            screen.blit(self.icon[ICON_SLIDESHOW], (44, 1))

        # Clock
        pygame.draw.rect(screen, COLOR_WHITE, pygame.Rect((0, 0), (40, 13)), 0)  # Clock backing
        screen.blit(self.time_text[0], (2, 1))  # time text 12:00
        screen.blit(self.time_text[1], (25, 1))  # time text am/pm
        pygame.display.update()

    def surf_startup(self):
        print("Startup")
        # Set surface image
        self.surf = pygame.transform.scale(pygame.image.load(os.path.join(BASE_DIR, 'resource', 'PiOnline.png')), DIM_SCREEN)

    def surf_picture(self):
        # TODO: https://developers.google.com/drive/api/v3/manage-downloads
        # TODO: http://blog.vogella.com/2011/06/21/creating-bitmaps-from-the-internet-via-apache-httpclient/
        print("Picture Album")
        # Set surface image
        self.surf = pygame.transform.scale(pygame.image.load(os.path.join(BASE_DIR, 'resource', 'burlington.jpg')), DIM_SCREEN)
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
                                               DIM_SCREEN)

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
        ax.set_ylim(50, 70)
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
        return pygame.image.fromstring(raw_data, DIM_SCREEN, "RGB")

    def pullData(self):
        # 11 days
        ndays = 11
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
        self.time_text = (FONT_BM.render(d.strftime("%I:%M"), True, COLOR_BLACK), FONT_BM.render(d.strftime("%p"), True, COLOR_BLACK))

    def toggleSlideshow(self):
        if self.slideshow:
            pygame.time.set_timer(USEREVENT + 2, 0)  # turn off the slideshow userevent
        else:
            pygame.time.set_timer(USEREVENT + 2, 10000)  # turn on the slideshow userevent
        self.slideshow = not self.slideshow # toggle the slideshow bool
