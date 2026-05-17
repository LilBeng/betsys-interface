from multiprocessing import set_start_method, freeze_support

from src.main import run

if __name__ == "__main__":
    set_start_method('spawn', force=True)
    freeze_support()

    run()
