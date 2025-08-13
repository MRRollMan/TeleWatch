from TeleWatch import TeleWatch
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

tw = TeleWatch()

if __name__ == '__main__':
    tw.start()
