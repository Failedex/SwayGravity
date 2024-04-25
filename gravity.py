#! /usr/bin/env python3
from i3ipc import Rect, Event
from i3ipc.aio import Connection
import time
import asyncio
import subprocess

GRAVITY = 2
FRICTION = 0.92
# set your screen size here
SCREEN = Rect(dict(
    x = 0,
    y = 0,
    width = 1920,
    height = 1080
))

async def sound(vx, vy): 
    vol = min((max(abs(vy), abs(vx))), 400)/5
    subprocess.Popen(["mpv", "--no-video", "./boing.mov", f"--volume={vol+40}"])

class Window(Rect):
    def __init__(self, data, id): 
        self.id = id 
        self.pos = Rect(data)
        self.old_pos = Rect(data)
        super().__init__(data)

    async def tick(self, i3, new_rect): 
        self.old_pos = self.pos
        self.pos = new_rect

        old_pos = self.old_pos
        pos = self.pos

        velocity = [
                int((pos.x - old_pos.x)*FRICTION),
                int((pos.y - old_pos.y)+GRAVITY)
                ]

        # bounds checking
        if pos.x < SCREEN.x and velocity[0] < 0: 
            await i3.command(f"[con_id={self.id}] move absolute position {SCREEN.x}px {pos.y}px")
            velocity[0] *= -1
            await sound(velocity[0], velocity[1])

        if pos.x + pos.width > SCREEN.x+SCREEN.width and velocity[0] > 0: 
            await i3.command(f"[con_id={self.id}] move absolute position {SCREEN.x+SCREEN.width-pos.width}px {pos.y}px")
            velocity[0] *= -1
            await sound(velocity[0], velocity[1])

        if pos.y < SCREEN.y and velocity[1] < 0: 
            await i3.command(f"[con_id={self.id}] move absolute position {pos.x}px {SCREEN.y}px")
            self.pos.y = SCREEN.y
            velocity[1] = 0

        if pos.y+pos.height > SCREEN.y+SCREEN.height and velocity[1] > 0: 
            if abs(velocity[1]-GRAVITY) > 5:
                await i3.command(f"[con_id={self.id}] move absolute position {pos.x}px {SCREEN.y+SCREEN.height-pos.height+5}px")

                # stop fucking moving
                # self.pos.y = SCREEN.y+SCREEN.height-pos.height+5

                velocity[1] *= 0.5
                velocity[1] = int(velocity[1])
                velocity[1] *= -1
            else:
                velocity[1] = 0

        if max(abs(velocity[0]), abs(velocity[1])) > 1:
            await i3.command(f"[con_id={self.id}] move absolute position {pos.x+velocity[0]}px {pos.y+velocity[1]}px")

class Main_Loop: 
    def __init__(self):
        self.i3 = None
        self.windows = {}

    async def start(self):
        self.i3 = await Connection().connect()
        await self.loop()

    async def loop(self):
        while True:
            start = time.time()
            new = await self.find_windows()
            untampered = set(self.windows.keys())

            for k, v in new.items():
                if k in self.windows:
                    await self.windows[k].tick(self.i3, v)
                    untampered.remove(k)
                else:
                    self.windows[k] = Window(dict(
                        x = v.x,
                        y = v.y,
                        width = v.width,
                        height = v.height,
                    ), k)

            for k in untampered:
                del self.windows[k]

            await asyncio.sleep(max(1/60 - (time.time()-start), 0))

    async def find_windows(self):
    
        tree = await self.i3.get_tree()

        focused = tree.find_focused()

        if not focused:
            return {}

        workspace = focused.workspace()

        windows = {}
        for c in workspace:
            if c.pid:
                c.rect.y -= c.deco_rect.height
                c.rect.height += c.deco_rect.height
                windows[c.id] = c.rect

        return windows



if __name__ == "__main__":
    m = Main_Loop()
    asyncio.run(m.start())
