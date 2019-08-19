from temperature.pygameObjects import *

#os.environ["SDL_FBDEV"] = "/dev/fb1"


def main():
    env = Environment()
    while True:
        env.menu()


if __name__ == '__main__':
    main()
