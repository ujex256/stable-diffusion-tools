import sys
import time

import keyboard
import colorama
from colorama import Fore, Back, Style


def ansi_escape(es):
    sys.stdout.write(es)
    sys.stdout.flush()


def delete_all(now, max_length):
    # 一度上に戻って消す
    if now != 0:
        ansi_escape(f"\033[{now}A")
    for _ in range(max_length):
        ansi_escape("\033[2K\033[1B")
    ansi_escape(f"\033[{max_length}A")


def print_selector(choice: list, back_length: int | None = None):
    if back_length is None:
        back_length = max(len(i) for i in choice)
    colorama.init(autoreset=True)
    ansi_escape("\033[?25l")  # カーソルを非表示

    def draw():
        for index, i in enumerate(choice):
            if index == now:
                ansi_escape("\033[2K\033[G" + Back.CYAN + i + (back_length-len(i))*" ")  # noqa
                print()
            else:
                print(i)
        ansi_escape(f"\033[{len(choice)}A")
        if now >= 1:
            ansi_escape(f"\033[{now}B")

    now = 0
    draw()
    try:
        while True:
            key = keyboard.read_key()
            delete_all(now, len(choice))
            if key == "up" and now != 0:
                now -= 1
            elif key == "down" and now != len(choice) - 1:
                now += 1
            elif key == "enter":
                ansi_escape("\033[?25h")
                return choice[now]
            draw()
            time.sleep(0.1)
    except KeyboardInterrupt:
        ansi_escape("\033[?25h")  # 途中で終了されたらカーソルを表示させる
        raise KeyboardInterrupt


if __name__ == "__main__":
    selectors = [
        "選択肢1 - 内容",
        "選択肢2 - 内容2",
        "選択肢3 - 内容3",
        "test",
        "テスト",
    ]
    print(print_selector(selectors))
