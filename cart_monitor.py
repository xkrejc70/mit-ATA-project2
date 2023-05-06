#!/usr/bin/env python3
"""
Dynamic analyser of a cart controller.
"""

MAX_SLOTS = 4
MAX_CAPACITY = 150

class Request:
    def __init__(self, src, dst, content, w):
        self.id = content + w
        self.src = src
        self.dst = dst
        self.state = 0 # 0-waiting, 1-loaded, 2-unloaded

    def __str__(self):
        return f"{self.id} {self.src} {self.dst} {self.state}"

requests = []
num_used_slots = 0
total_w = 0
end_time = 0
error = False
stations_slots = [[False] * MAX_SLOTS for _ in range(4)]
slot_usage = [False] * MAX_SLOTS
map_station = {
    'A': 0,
    'B': 1,
    'C': 2,
    'D': 3
}

def report_coverage():
    # Counts the number of slots used in stations
    count = 0
    for station in stations_slots:
        for slot in station:
            if slot:
                count += 1
    
    coverage = count / 16 * 100
    print('CartCoverage %d%%' % coverage)

def onmoving(time, pos1, pos2):
    global error
    # Check rule 3
    for req in requests:
        if req.dst == pos1 and req.state == 1:
            error = True
            print(f"{time}:error: didn't unload at position {pos1}")

def onloading(time, pos, content, w, slot):
    global error, num_used_slots, total_w
    slot = int(slot)
    found = False
    num_used_slots += 1
    total_w += int(w)

    # Track Coverage
    stations_slots[map_station[pos]][slot] = True

    # Check rule 6
    if num_used_slots > 4:
        error = True
        print(f"{time}:error: loading into full slots")

    # Check rule 7
    if total_w > MAX_CAPACITY:
        error = True
        print(f"{time}:error: loading in excess of maximum capacity")

    # Check rule 1
    if slot_usage[slot]:
        error = True
        print(f"{time}:error: loading into an occupied slot #{slot}")
    
    slot_usage[slot] = True
    # Check rule 5
    for req in requests:
        if req.id == content + w and req.src == pos and req.state == 0:
            found = True
            req.state = 1

    if not found:
        error = True
        print(f"{time}:error: loading is not in requests at position {pos}")

def onunloading(time, pos, content, w, slot):
    global error, num_used_slots, total_w
    pos = map_station[pos]
    slot = int(slot)
    num_used_slots -= 1
    total_w -= int(w)

    # Check rule 2
    if (not slot_usage[slot]):
        error = True
        print(f"{time}:error: unloading from an empty slot #{slot}")

    slot_usage[slot] = False
    for req in requests:
        if req.id == content + w:
            req.state = 2       

def requesting(time, src, dst, content, w):
    requests.append(Request(src, dst, content, w))

def stop(time):
    global end_time
    end_time = time

    # Check rule 3
    for req in requests:
        if req.state == 1:
            error = True
            print(f"{time}:error: didn't unload at position {req.dst}")

    # Check rule 4
    for req in requests:
        if req.state == 0:
            error = True
            print(f"{end_time}:error: request was not loaded")

def onevent(event):    
    event_id = event[1]
    del(event[1])

    if event_id == 'moving':
        onmoving(*event)
    elif event_id == 'loading':
        onloading(*event)
    elif event_id == 'unloading':
        onunloading(*event)
    elif event_id == 'requesting':
        requesting(*event)
    elif event_id == 'stop':
        stop(*event)

###########################################################
# Nize netreba menit.

def monitor(reader):
    global error
    "Main function"
    for line in reader:
        line = line.strip()
        onevent(line.split())
    if not error:
        print('All properties hold.')
    report_coverage()

if __name__ == "__main__":
    import sys
    monitor(sys.stdin)
