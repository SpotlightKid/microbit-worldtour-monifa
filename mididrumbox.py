from microbit import button_a, display
from microbit import uart
from microbit import running_time, sleep

NOTE_ON = 0x90
CONTROLLER_CHANGE = 0xB0
PROGRAM_CHANGE = 0xC0

class MidiOut:
    def __init__(self, device, channel=1):
        if channel < 1 or channel > 16:
            raise ValueError('channel must be an integer between 1..16.')
        self.channel = channel
        self.device = device
    def channel_message(self, command, *data, ch=None):
        command = (command & 0xf0) | ((ch if ch else self.channel) - 1 & 0xf)
        msg = [command] + [value & 0x7f for value in data]
        self.device.write(bytes(msg))
    def note_on(self, note, velocity=127, ch=None):
        self.channel_message(NOTE_ON, note, velocity, ch=ch)
    def control_change(self, control, value, lsb=False, ch=None):
        self.channel_message(CONTROLLER_CHANGE, control,
                             value >> 7 if lsb else value, ch=ch)
        if lsb and control < 20:
            self.channel_message(CONTROLLER_CHANGE, control + 32, value, ch=ch)
    def program_change(self, program, ch=None):
        self.channel_message(PROGRAM_CHANGE, program, ch=ch)

class Pattern:
    velocities = {
        "-": None, # continue note
        ".": 0,    # off
        "+": 10,   # ghost
        "s": 60,   # soft
        "m": 100,  # medium
        "x": 120,  # hard
    }

    def __init__(self, src):
        self.step = 0
        self.instruments = []
        self._active_notes = {}
        pattern = (line.strip() for line in src.split('\n'))
        pattern = (line for line in pattern
                   if line and not line.startswith('#'))

        for line in pattern:
            parts = line.split(" ", 2)

            if len(parts) == 3:
                note, hits, description = parts
            elif len(parts) == 2:
                note, hits = parts
                description = None
            else:
                continue

            note = int(note)
            self.instruments.append((note, hits))

        self.steps = max(len(hits) for _, hits in self.instruments)

    def playstep(self, midiout, channel=10):
        for note, hits in self.instruments:
            velocity = self.velocities.get(hits[self.step])

            if velocity is not None:
                if self._active_notes.get(note):
                    # velocity==0 <=> note off
                    midiout.note_on(note, 0, ch=channel)
                    self._active_notes[note] = 0
                if velocity > 0:
                    midiout.note_on(note, max(1, velocity), ch=channel)
                    self._active_notes[note] = velocity

        self.step = (self.step + 1) % self.steps


class Sequencer:
    def __init__(self, midiout, bpm=120, channel=10):
        self.midiout = midiout
        self.mpq = 15000. / max(20, min(bpm, 400))
        self.channel = channel

    def play(self, pattern, kit=None):
        if kit:
            self.midiout.program_change(kit, ch=self.channel)
            # give MIDI instrument some time to load drumkit
            sleep(300)

        while True:
            last_tick = running_time()
            pattern.playstep(self.midiout, self.channel)
            timetowait = max(0, self.mpq - (running_time() - last_tick))
            if timetowait > 0:
                sleep(timetowait)

FUNKYDRUMMER = """\
36 x.x.......x..x..
38 ....x..m.m.mx..m
42 xxxxx.x.xxxxx.xx
46 .....x.x.....x..
"""

while True:
    if button_a.is_pressed():
        display.set_pixel(0, 0, 0)
        break

    display.set_pixel(0, 0, 5)
    sleep(100)
    display.set_pixel(0, 0, 0)
    sleep(100)

# Initialize UART for MIDI
uart.init(baudrate=31250)
midi = MidiOut(uart)
seq = Sequencer(midi, bpm=90)
seq.play(Pattern(FUNKYDRUMMER), kit=9)
