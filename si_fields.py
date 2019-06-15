#!/usr/bin/env python

import curses
import curses.panel


class Game:
    def __init__(self, max_y, max_x):
        self.win = curses.newwin(max_y, max_x, 3, 0)
        self.panel = curses.panel.new_panel(self.win)


class Stat:
    def __init__(self, x):
        self.win = curses.newwin(16, 16, 3, x)
        self.panel = curses.panel.new_panel(self.win)
        self.win.box()


class Head:
    def __init__(self, x):
        self.win = curses.newwin(3, x, 0, 0)
        self.panel = curses.panel.new_panel(self.win)
        self.win.box()
        self.head_str = "Space Invaders"
        self.win.addstr(1, (x - len(self.head_str)) // 2, self.head_str)


class Menu:
    def __init__(self, x, menu_elements, cursor=">>", head="Menu"):
        self.max_x = x
        self.win = curses.newwin(16, self.max_x, 3, 0)
        self.panel = curses.panel.new_panel(self.win)
        self.cursor = cursor
        self.menu_elements = menu_elements
        self.head = head
        self.update()

    def update(self, cursor_pos=0):
        self.win.clear()
        self.win.box()
        self.win.addstr(1, (self.max_x - len(self.head)) // 2, self.head)

        for i, menu_element in enumerate(self.menu_elements):
            if cursor_pos == i:
                self.win.addstr(i + 3, 1, self.cursor)
            self.win.addstr(i + 3, 4, menu_element)

        curses.panel.update_panels()
        curses.doupdate()


class File:
    def __init__(self, filename):
        self.max_x = 32
        self.win = curses.newwin(16, self.max_x, 3, 0)
        self.panel = curses.panel.new_panel(self.win)
        self.print_file(filename)

    def print_file(self, filename):
        self.win.box()
        i = 0
        try:
            with open(filename) as file:
                for i, line in enumerate(file):
                    self.win.addstr(i + 1, 1, line[:-1])
        except Exception as e:
            self.win.addstr("Exception {}".format(e))
        self.win.addstr(i + 2, 1, "Press any key to continue...")
        curses.panel.update_panels()
        curses.doupdate()


class Lose:
    def __init__(self, score):
        self.win = curses.newwin(10, 40, 0, 0)
        self.panel = curses.panel.new_panel(self.win)
        self.win.box()

        self.win.addstr(5, 5, "You lose")
        self.win.addstr(6, 5, "Score: {}".format(str(score)))

        self.win.addstr(7, 5, "Press any key to exit")
