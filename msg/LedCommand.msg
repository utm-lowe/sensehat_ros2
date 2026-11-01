# Command for the 8x8 LED matrix.
# Select the mode with `type`, then fill in the matching payload field.

uint8 CHARACTER=0
uint8 MESSAGE=1
uint8 PIXELS=2

uint8 type 0

CharacterData character
MessageData message
PixelsData pixels
