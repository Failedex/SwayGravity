#! /usr/bin/env python3

import i3ipc
import time
import threading
import subprocess

i3 = i3ipc.Connection()

old_pos = (0, 0)
pos = (0, 0)
velocity = [0, 0]
friction = 0.92
gravity = 2
pid = 0

# set your boundaries here
screen = i3ipc.Rect(dict(
    x = 1440,
    y = 0,
    width = 1920,
    height = 1080
))

def sound(vx, vy): 
    vol = min((max(abs(vy), abs(vx))), 400)/5
    s = threading.Thread(target = subprocess.run, args=(["mpv", "--no-video", "./boing.mov", f"--volume={vol+40}"], ), daemon=True)
    s.start()

while True:
    old_pos = pos
    
    focused = i3.get_tree().find_focused()

    if not focused:
        time.sleep(1/60)
        continue
    
    rect = focused.rect
    rect.y -= focused.deco_rect.height
    rect.height += focused.deco_rect.height
    pos = (rect.x, rect.y)

    if focused.pid != pid: 
        pid = focused.pid
        continue
    
    # velocity = [
    #         int((pos[0] - old_pos[0])*friction),
    #         int((pos[1] - old_pos[1])+gravity if (screen.y+screen.height) - (pos[1]+rect.height) > 5 else 0)
    #         ]
    velocity = [
            int((pos[0] - old_pos[0])*friction),
            int((pos[1] - old_pos[1])+gravity if "silly" not in focused.marks else (pos[1] - old_pos[1])-2)
            ]

    if pos[0] < screen.x and velocity[0] < 0:
        i3.command(f"[pid={pid}] move absolute position {screen.x}px {pos[1]}px")
        velocity[0] *= -1
        sound(velocity[0], velocity[1])

    if pos[0]+rect.width > screen.x+screen.width and velocity[0] > 0:
        i3.command(f"[pid={pid}] move absolute position {screen.x+screen.width-rect.width}px {pos[1]}px")
        velocity[0] *= -1
        sound(velocity[0], velocity[1])

    if pos[1] < screen.y and velocity[1] < 0 and not "silly" in focused.marks:
        i3.command(f"[pid={pid}] move absolute position {pos[0]}px {screen.y}px")
        velocity[1] = 0
        sound(velocity[0], velocity[1])

    if pos[1]+rect.height > screen.y+screen.height and velocity[1] > 0 and not "silly" in focused.marks:
        
        if abs(velocity[1]-gravity) < 5:
            velocity[1] = 0
        else:
            i3.command(f"[pid={pid}] move absolute position {pos[0]}px {screen.y+screen.height-rect.height}px")
            velocity[1] *= 0.5
            velocity[1] = int(velocity[1])
            velocity[1] *= -1
        # sound(velocity[0], velocity[1])

    if max(abs(velocity[0]), abs(velocity[1])) > 1 and old_pos != (0, 0):
        i3.command(f"[pid={pid}] move absolute position {pos[0]+velocity[0]}px {pos[1]+velocity[1]}px")

    time.sleep(1/60)

