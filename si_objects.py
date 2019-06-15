#!/usr/bin/env python

import random
import curses


class Player:
    def __init__(self, max_x, max_y, body="W", lifes=3):
        self.max_x = max_x - 1
        self.x = self.max_x // 2
        self.y = max_y - 2
        self.body = body
        self.lifes = lifes
        self.have_bullet = False
        self.color = "red"

    def move(self, dx):
        if self.x + dx in range(1, self.max_x):
            self.x += dx


class Ship:
    def __init__(self, max_x):
        self.x = 1
        self.y = 1
        self.body = "<O>"
        self.color = "cyan"
        self.max_x = max_x - 3
        self.cost = 100 * random.randint(1, 6)
        self.tick = 0

    def move(self):
        self.tick = (self.tick + 1) % 3
        if self.tick == 0:
            self.x += 1

    def can_move(self):
        return self.x + 1 < self.max_x


class Bullet:
    def __init__(self, x, y, dy, max_y, owner, body='!'):
        self.x = x
        self.y = y
        self.owner = owner
        self.dy = dy
        self.body = body
        self.max_y = max_y
        self.color = "white"

    def move(self):
        self.y += self.dy

    def can_move(self):
        y = self.y + self.dy
        return y in range(1, self.max_y - 1)


class Bomb(Bullet):
    def explode(self):
        pass  # Next Versions


class Alien:
    def __init__(self, max_x, x, y, body="}{"):
        self.max_x = max_x - 2
        self.x = x
        self.y = y
        self.body = body
        self.dx = 1
        self.cost = 10
        self.shoot_chance = 0.025
        self.have_bullet = False
        self.color = "magenta"

    def can_move(self):
        return self.x + self.dx in range(1, self.max_x)

    def move(self, h_move):
        if h_move:
            self.x += self.dx
        else:
            self.y += 1
            self.dx *= -1

    def conflict_case(self, bullet):
        return isinstance(bullet.owner, Player)


class Crab(Alien):
    def __init__(self, field, x, y, body="]["):
        super().__init__(field, x, y, body=body)
        self.color = "red"
        self.cost = 20


class Octopus(Alien):
    def __init__(self, field, x, y, body="MM"):
        super().__init__(field, x, y, body=body)
        self.cost = 40
        self.lifes = 2
        self.color = "yellow"

    def conflict_case(self, bullet):
        if isinstance(bullet.owner, Player):
            self.lifes -= 1
            self.color = "red"
            return self.lifes == 0


class Bunker:
    def __init__(self, start_x, finish_x, y, body="n"):
        self.start_x = start_x
        self.finish_x = finish_x
        self.y = y
        self.body = body
        self.bandwidth = 0.5
        self.d_bw = 0.05
        self.color = "green"

    def death_in_conflict(self, bullet):
        if isinstance(bullet.owner, Player):
            if self.bandwidth < 1:
                self.bandwidth += self.d_bw
                self.bandwidth = round(self.bandwidth, 2)
            return random.random() > self.bandwidth
        else:
            if self.bandwidth > 0:
                self.bandwidth -= self.d_bw
                self.bandwidth = round(self.bandwidth, 2)
            return random.random() < self.bandwidth
