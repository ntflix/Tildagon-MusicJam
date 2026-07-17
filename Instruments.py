from .Instrument import Instrument

INSTRUMENTS: list[Instrument] = [
    Instrument(
        "Dreamy Vox",
        1,
        hint="hold buttons to play\ntilt to modulate and bend!",
    ),
    Instrument(
        "Phasing Plucks",
        13,
        shouldPitchBend=False,
        shouldModulate=True,
        hint="hold buttons to play\ntilt to glitch!",
    ),
    Instrument(
        "Chiptune Kit",
        5,
        shouldPitchBend=False,
        shouldModulate=False,
        hint="hold buttons to play\nto the beat!",
    ),
    Instrument("Chimera Bells", 2),
    Instrument("Space Funk", 3),
    Instrument("Synth Bass", 4),
    Instrument("Time Bomb", 6),
    Instrument("Dalek", 7),
    Instrument("Bleep Bloop", 8),
    Instrument("Moon Fusion Organ", 9),
    Instrument("Moob", 10),
    Instrument("Violins", 11),
    Instrument("Dream Sequence", 12),
    Instrument("70s Funk Clav", 14),
    Instrument("Ballad", 15),
]
