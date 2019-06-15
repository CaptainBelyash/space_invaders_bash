#!/usr/bin/env python

import os
import sys
from operator import itemgetter
import time
import threading
import curses
import curses.panel
import si_objects
import si_fields
import random
import argparse


class Game:
    def __init__(self, map_file_name, score=0, lifes=3):
        self.stdscr = curses.initscr()
        curses.start_color()
        curses.noecho()
        curses.curs_set(False)

        self.color = {}
        self.init_colors()

        self.stdscr.keypad(True)
        self.max_x = 2
        self.max_y = 3
        self.aliens = []
        self.bullet_tick = 0.12
        self.alien_tick = 1
        self.alien_acceleration = 0.9
        self.bullets = []
        self.bunkers = []
        self.field = None
        self.score = score
        self.ship = None
        self.ship_spawn_chance = 0.06

        self.create_field(map_file_name)
        self.player = si_objects.Player(self.max_x, self.max_y, lifes=lifes)
        self.create_map(map_file_name)
        self.head = si_fields.Head(self.max_x + 16)
        self.stat = si_fields.Stat(self.max_x)
        self.ALIVE = True

    def init_colors(self):
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)

        self.color = {"white": curses.color_pair(1) + curses.A_BOLD,
                      "red": curses.color_pair(2) + curses.A_BOLD,
                      "yellow": curses.color_pair(3) + curses.A_BOLD,
                      "green": curses.color_pair(4) + curses.A_BOLD,
                      "magenta": curses.color_pair(5) + curses.A_BOLD,
                      "cyan": curses.color_pair(6) + curses.A_BOLD}

    def create_field(self, map_file_name):
        with open(map_file_name) as map_file:
            for line in map_file:
                self.max_y += 1
                self.max_x = len(line) + 1
        self.field = si_fields.Game(self.max_y, self.max_x)

    def create_map(self, map_file_name):
        with open(map_file_name) as map_file:
            for curr_y, line in enumerate(map_file):
                prev_is_bunker = False
                bunker_start_x = None
                for curr_x, symbol in enumerate(line):
                    if symbol == 'a':
                        self.aliens.append(si_objects.Alien(self.max_x,
                                                            curr_x,
                                                            curr_y + 1))

                    if symbol == 'c':
                        self.aliens.append(si_objects.Crab(self.max_x,
                                                           curr_x,
                                                           curr_y + 1))

                    if symbol == 'o':
                        self.aliens.append(si_objects.Octopus(self.max_x,
                                                              curr_x,
                                                              curr_y + 1))

                    if symbol == 'b':
                        if not prev_is_bunker:
                            bunker_start_x = curr_x
                        prev_is_bunker = True
                        if curr_x == self.max_x:
                            self.bunkers.append(
                                si_objects.Bunker(bunker_start_x,
                                                  curr_x, curr_y))
                    elif prev_is_bunker:
                        prev_is_bunker = False
                        self.bunkers.append(si_objects.Bunker(bunker_start_x,
                                                              curr_x - 1,
                                                              curr_y))

    def start(self):
        ki_thread = threading.Thread(target=self.keyboard_interrupt,
                                     daemon=True)
        ki_thread.start()

        am_thread = threading.Thread(target=self.alien_move, daemon=True)
        am_thread.start()
        
        while self.aliens and self.ALIVE:
            self.update()
            self.bullet_move()
            time.sleep(self.bullet_tick)
        self.update()
        curses.panel.update_panels()
        curses.doupdate()
        curses.endwin()
        return self.score, self.player.lifes + 1, self.ALIVE

    def alien_move(self):
        while self.aliens:
            can_move = True
            alien_count = len(self.aliens)
            for alien in self.aliens:
                alien.shoot_chance = 0.5 / alien_count
                can_move *= alien.can_move()
            if not can_move:
                self.alien_tick *= self.alien_acceleration
            for alien in self.aliens:
                alien.move(can_move)
                if alien.shoot_chance > random.random():
                    if 0.5 > random.random():
                        self.shoot(alien.x, alien.y + 1, 1, alien)
                    else:
                        self.shoot(alien.x + 1, alien.y + 1, 1, alien)
                if alien.y + 2 == self.player.y:
                    self.lose()
            time.sleep(self.alien_tick)
            self.update()

    def keyboard_interrupt(self):
        while self.aliens:
            key = self.stdscr.getch()
            self.ki_event_handler(key)

    def ki_event_handler(self, key):
        if key == curses.KEY_LEFT or key == ord('a'):
            self.player.move(-1)

        if key == curses.KEY_RIGHT or key == ord('d'):
            self.player.move(1)

        if key == curses.KEY_UP or key == ord(' '):
            if not self.player.have_bullet:
                self.shoot(self.player.x, self.player.y, -1, self.player)

        self.update()

    def shoot(self, x, y, dy, owner):
        bullet = si_objects.Bullet(x, y, dy, self.max_y, owner)
        owner.have_bullet = True
        self.bullets.append(bullet)

    def bullet_move(self):

        if self.ship:
            self.ship.move()
            if not self.ship.can_move():
                self.ship = None
        elif self.ship_spawn_chance > random.random():
            self.ship = si_objects.Ship(self.max_x)
        remaining_bullet = []
        reset_bullets = False
        for bullet in self.bullets:
            bullet_delete = False
            move_next = bullet.can_move()
            if move_next:
                bullet.move()
                if (self.ship
                        and bullet.x in range(self.ship.x, self.ship.x + 3)
                        and bullet.y == self.ship.y):
                    self.score += self.ship.cost
                    self.ship = None
                if bullet.x == self.player.x and bullet.y == self.player.y:
                    self.player.lifes -= 1
                    self.player.x = self.player.max_x // 2
                    reset_bullets = True
                    time.sleep(1)
                    if self.player.lifes == 0:
                        self.lose()
                for bunker in self.bunkers:
                    if (bunker.y == bullet.y
                            and bullet.x in range(bunker.start_x,
                                                  bunker.finish_x + 1)):
                        bullet_delete = bunker.death_in_conflict(bullet)

                remaining_aliens = []
                for alien in self.aliens:
                    dead_in_conflict = False
                    if ((bullet.x == alien.x
                            or bullet.x == alien.x + 1)
                            and alien.y == bullet.y):
                        bullet_delete = True
                        dead_in_conflict = alien.conflict_case(bullet)
                    if dead_in_conflict:
                        self.score += alien.cost
                    else:
                        remaining_aliens.append(alien)

                if bullet_delete:
                    pass
                else:
                    remaining_bullet.append(bullet)
                self.aliens = remaining_aliens

            if not move_next or bullet_delete:
                bullet.owner.have_bullet = False
        if reset_bullets:
            self.bullets = []
            self.player.have_bullet = False
        else:
            self.bullets = remaining_bullet

    def redraw(self):
        self.stat.win.clear()
        self.stat.win.box()
        self.stat.win.addstr(1, 1, "Lifes: {}".format(self.player.lifes))
        self.stat.win.addstr(2, 1, "Score: {}".format(self.score))

        self.field.win.clear()
        self.field.win.box()
        if self.bullets:
            for bullet in self.bullets:
                self.field.win.addstr(bullet.y, bullet.x, bullet.body,
                                      self.color[bullet.color])

        self.field.win.addstr(self.player.y, self.player.x, self.player.body,
                              self.color[self.player.color])
        if self.ship:
            self.field.win.addstr(self.ship.y, self.ship.x, self.ship.body,
                                  self.color[self.ship.color])
        for alien in self.aliens:
            self.field.win.addstr(alien.y, alien.x, alien.body,
                                  self.color[alien.color])
        for bunker_i, bunker in enumerate(self.bunkers):
            bunker_bw = round(bunker.bandwidth * 100)
            self.stat.win.addstr(bunker_i + 4, 1,
                                 "Bunker-{}: {}%".format(bunker_i + 1,
                                                         bunker_bw))
            bunker_i += 1
            for x_coord in range(bunker.start_x, bunker.finish_x + 1):
                self.field.win.addstr(bunker.y, x_coord, bunker.body,
                                      self.color[bunker.color])

    def update(self):
        self.redraw()
        curses.panel.update_panels()
        curses.doupdate()

    def lose(self):
        self.ALIVE = False


class Menu:
    def __init__(self, info_filename="info", sb_filename="scoreboard"):
        self.info_file = info_filename
        self.sb_file = sb_filename
        self.printed_file = None
        self.stdscr = curses.initscr()
        curses.start_color()
        curses.noecho()
        curses.curs_set(False)
        self.stdscr.keypad(True)
        self.max_x = 32
        self.head = si_fields.Head(self.max_x)
        self.menu_elements = ["Play", "Info", "ScoreBoard"]
        self.menu = si_fields.Menu(self.max_x, self.menu_elements)
        self.cursor_pos = 0
        self.start_menu = None
        self.START_GAME = False

    def start(self):
        while not self.START_GAME:
            self.menu.update(self.cursor_pos)
            key = self.stdscr.getch()
            if ((key == curses.KEY_DOWN or key == ord("s"))
                    and self.cursor_pos < len(self.menu_elements) - 1):
                self.cursor_pos += 1
            elif ((key == curses.KEY_UP or key == ord("w"))
                    and self.cursor_pos != 0):
                self.cursor_pos -= 1
            elif key == ord("\n"):
                if self.cursor_pos == 0:
                    self.START_GAME = True
                elif self.cursor_pos == 1:
                    self.print_file(self.info_file)
                elif self.cursor_pos == 2:
                    self.print_file(self.sb_file)
        curses.endwin()
        return

    def print_file(self, filename):
        self.printed_file = si_fields.File(filename)
        self.stdscr.getch()
        self.printed_file = None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("game_dir", type=str,
                        help="Directory in which the level files are located")
    parser.add_argument("name", type=str,
                        help="Player name")
    args = parser.parse_args()
    if not os.path.isdir(args.game_dir):
        print("No such directory")
    else:
        name = args.name
        if not name:
            name = "Player"
        menu = Menu()
        menu.start()
        levels = os.listdir(args.game_dir)

        score = 0
        life_count = 3
        go_next = True
        while life_count != 0 and go_next:
            for level in levels:
                (score, life_count,
                    go_next) = start_lvl("{}/{}".format(args.game_dir, level),
                                         score=score, life_count=life_count)
                if not go_next:
                    break
        change_scoreboard(name, score)
        curses.endwin()


def change_scoreboard(name, score):
    current_item = (name, score)
    with open("scoreboard", "r") as sb_file:
        items = [parse_scoreboard(line.split()) for line in sb_file]
        items.append(current_item)
    with open("scoreboard", "w")as sb_file:
        for item in sorted(items, key=itemgetter(1), reverse=True)[:10]:
            sb_file.write("{} - {}\n".format(item[0], item[1]))


def parse_scoreboard(split_line):
    return split_line[0], int(split_line[2])


def start_lvl(level_file, score=0, life_count=3):
    time_to_next_lvl = 1
    level = Game(level_file, score, life_count)
    go_next = None
    try:
        score, life_count, go_next = level.start()
    except KeyboardInterrupt:
        score = level.score
        life_count = level.player.lifes
        go_next = False
        curses.endwin()
    time.sleep(time_to_next_lvl)
    return score, life_count, go_next


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        curses.endwin()
