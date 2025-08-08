from TeleWatch import TeleWatch
import logging

logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.INFO)

tw = TeleWatch()

if __name__ == '__main__':
    tw.start()
