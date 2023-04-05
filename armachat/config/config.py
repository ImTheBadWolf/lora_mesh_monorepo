import board
import digitalio
cols = [
    digitalio.DigitalInOut(x)
    for x in (board.GP1, board.GP2, board.GP3, board.GP4, board.GP5)
]
rows = [
    digitalio.DigitalInOut(x)
    for x in (board.GP6, board.GP9, board.GP15, board.GP8, board.GP7, board.GP22)
]
keys1 = (
    ("ent", " ", "m", "n", "b"),
    ("bsp", "l", "k", "j", "h"),
    ("p", "o", "i", "u", "y"),
    ("alt", "z", "x", "c", "v"),
    ("a", "s", "d", "f", "g"),
    ("q", "w", "e", "r", "t"),
)

keys2 = (
    ("rt", ",", ">", "<", '""'),
    ("lt", "-", "*", "&", "+"),
    ("0", "9", "8", "7", "6"),
    ("alt", "(", ")", "?", "/"),
    ("!", "@", "#", "$", "%"),
    ("1", "2", "3", "4", "5"),
)

keys3 = (
    ("dn", ";", "M", "N", "B"),
    ("up", "L", "K", "J", "H"),
    ("P", "O", "I", "U", "Y"),
    ("alt", "Z", "X", "C", "V"),
    ("A", "S", "D", "F", "G"),
    ("Q", "W", "E", "R", "T"),
)
