import time
from workers.job import start_worker, stop_worker


def main() -> None:
    start_worker()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        stop_worker()


if __name__ == "__main__":
    main()
