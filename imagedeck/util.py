from .models import *
import glob


def import_glob(pattern, destination):
    for file in glob.glob(pattern):
        print(f"Moving {file}")
