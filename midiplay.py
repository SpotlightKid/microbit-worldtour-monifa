# -----------------------------------------------------------------------------
# START OF MIDI LIBRARY CODE
#
# Copy everything below here until the END OF MIDI LIBRARY CODE line
# to the *start* of your micro:bit MicroPython script
# in which you want to use MIDI output.

from microbit import uart

# global constants
NOTE_OFF = 0x80
NOTE_ON = 0x90
CONTROLLER_CHANGE = 0xB0
PROGRAM_CHANGE = 0xC0

class MidiOut:
    def __init__(self, device=None, channel=1):
        if device is None:
            self.device = uart
            self.device.init(baudrate=31250)
        elif not hasattr(device, 'write'):
            raise TypeError("device instance must have a 'write' method.")
        else:
            self.device = device

        if channel < 1 or channel > 16:
            raise ValueError('channel must be an integer between 1..16.')
        self.channel = channel
    def send(self, msg):
        return self.device.write(bytes(msg))
    def channel_message(self, command, *data, ch=None):
        command = (command & 0xf0) | ((ch if ch else self.channel) - 1 & 0xf)
        msg = [command] + [value & 0x7f for value in data]
        self.send(msg)
    def note_off(self, note, velocity=0, ch=None):
        self.channel_message(NOTE_OFF, note, velocity)
    def note_on(self, note, velocity=127, ch=None):
        self.channel_message(NOTE_ON, note, velocity)
    def control_change(self, control, value, lsb=False, ch=None):
        self.channel_message(CONTROLLER_CHANGE, control,
                             value >> 7 if lsb else value, ch=ch)
        if lsb and control < 20:
            self.channel_message(CONTROLLER_CHANGE, control + 32, value, ch=ch)
    def program_change(self, program, ch=None):
        self.channel_message(PROGRAM_CHANGE, program, ch=ch)

# END OF MIDI LIBRARY CODE
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Main script

import music
from microbit import button_a, display, sleep

TUNES = ['DADADADUM', 'ENTERTAINER', 'PRELUDE', 'ODE', 'NYAN', 'RINGTONE',
    'FUNK', 'BLUES', 'BIRTHDAY', 'WEDDING', 'FUNERAL', 'PUNCHLINE', 'PYTHON',
    'BADDY', 'CHASE', 'BA_DING', 'WAWAWAWAA', 'JUMP_UP', 'JUMP_DOWN',
    'POWER_UP', 'POWER_DOWN']

NOTES = {
    'c': 0,
    'd': 2,
    'e': 4,
    'f': 5,
    'g': 7,
    'a': 9,
    'b': 11,
}


def play(midi, notes):
    duration = octave = 4
    bpm, ticks = music.get_tempo()
    mpt = 60000 / bpm / ticks

    try:
        for note in notes:
            try:
                note, duration = note.split(':')
                duration = int(duration)
            except:
                pass

            try:
                octave = int(note[-1])
                note = note[:-1]
            except (ValueError, IndexError):
                pass

            note = note.lower()
            midinote = NOTES.get(note[0])

            if midinote is not None:
                if note.endswith('#'):
                    midinote += 1
                elif len(note) > 1 and note.endswith('b'):
                    midinote -= 1

                midinote = max(0, min(127, midinote + 12 * octave))
                midi.note_on(midinote, 96)

            sleep(duration * mpt)

            if midinote is not None:
                midi.note_off(midinote)
    except:
        # Send all sound off to prevent hanging notes
        midi.control_change(0x78, 0)


# wait for button A press before initializing the UART
# to allow uploading of new firmware
display.set_pixel(0, 0, 5)
while True:
    if button_a.is_pressed():
        break

    display.set_pixel(0, 0, 5)
    sleep(100)
    display.set_pixel(0, 0, 0)
    sleep(100)

# Initialize UART for MIDI
midi = MidiOut()

# At each button A press, play the next of the builtin tunes
tune = 0
while True:
    if button_a.is_pressed():
        display.set_pixel(0, 0, 5)
        play(midi, getattr(music, TUNES[tune]))
        display.set_pixel(0, 0, 0)
        tune = (tune+1) % len(TUNES)

    sleep(200)
