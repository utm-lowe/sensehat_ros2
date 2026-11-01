# Payload for LedCommand.type == MESSAGE (SenseHat.show_message).

string message

# An all-zero colour means "not specified" and the node default is used.
RGB text_color
RGB background_color

# Seconds between scroll frames. Values <= 0.0 use the node default.
float32 scroll_speed
