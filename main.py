import random
import time
import math

from neopixel import NeoPixel

WIDTH = 16  # Width of the LED grid in landscape mode
HEIGHT = 10  # Height of the LED grid in landscape mode
    
# Colors
DARK_GREEN = (0, 2, 0)
LIGHT_GREEN = (0, 3, 0)
GREEN = (0, 2, 0)
BROWN = (4, 2, 0)
YELLOW = (5, 5, 0) 
WHITE = (4, 4, 7) 
BLACK = (0, 0, 0)
DARK_BLUE = (0, 0, 2) 
BLUE = (0, 0, 4)
RED = (2, 0, 0)  
MAGENTA = (2, 0, 2)
ORANGE = (5, 2, 0)
BRIGHT_YELLOW = (8, 8, 0)
LIGHT_YELLOW = (4, 4, 2)

# Print debug messages
DEBUG = False

################################################################################
# region Helper Functions
################################################################################

def pixel2index(u, v, width=WIDTH, height=HEIGHT):
    """Convert (row, col) in portrait to flat index for pixel dict"""
    u_landscape = int(v)
    v_landscape = int(width - 1 - u)
    return u_landscape * width + v_landscape

def index2pixel(i, width=WIDTH, height=HEIGHT):
    """Convert (row, col) in portrait to flat index for pixel dict"""
    u_landscape = i // width
    v_landscape = i % width
    u = width - 1 - v_landscape
    v = u_landscape
    return u, v

p2i = pixel2index  # Alias
i2p = index2pixel  # Alias

################################################################################
# region BaseFont class
################################################################################
class FontBase:
    
    def __init__(self, size, bitmap):
        """
        Initialize font with size and bitmap data.
        
        Parameters:
        - size: Font size (width and height, assumes square font)
        - bitmap: Dictionary mapping characters to list of row bitmasks
        """
        self.size = size
        self.bitmap = bitmap
        self.char_bounds = {k: self._get_char_bounds(k) for k in bitmap}
        
    def _get_char_bounds(self, char):
        char = char.upper()
        if char not in self.bitmap:
            return (0, self.size - 1)
            
        rows = self.bitmap[char]
        
        leftmost = self.size
        rightmost = 0
        
        for row in rows:
            for col in range(self.size):
                if (row >> (self.size - 1 - col)) & 1:
                    leftmost = min(leftmost, col)
                    rightmost = max(rightmost, col)
        
        if rightmost < leftmost:
            return (0, self.size // 2)
            
        return (leftmost, rightmost)
    
    def get_char_bounds(self, char):
        """
        Get the bounding box of a character.
        
        Parameters:
        - char: Character to measure
        
        Returns:
        - (left_col, right_col) tuple with inclusive bounds
        """
        char = char.upper()
        return self.char_bounds.get(char, (0, self.size - 1))
    
    def get_char_width(self, char):
        """
        Get the width of a character.
        
        Parameters:
        - char: Character to measure
        
        Returns:
        - Width in pixels (or default size if character not found)
        """
        leftmost, rightmost = self.char_bounds.get(char, (0, self.size - 1))
        return rightmost - leftmost + 1
    
    def draw(self, pixels, char, row_offset=0, col_offset=0, 
             color=(15, 15, 15), bg_color=None, margins=None,
             variable_box=False):
        """
        Draw a character to the pixel buffer.
        
        Parameters:
        - pixels: Pixel dictionary to draw into
        - char: Character to draw
        - row_offset: Starting row position
        - col_offset: Starting column position
        - color: RGB tuple for the character
        - bg_color: RGB tuple for background (None = transparent)
        - margins: Frame around the character as (top, bottom, left, right)
        
        Returns:
        - Modified pixels dictionary
        """
        char = char.upper()
        if char not in self.bitmap:
            char = ' '
        
        rows = self.bitmap[char]
        box_width = self.get_char_width(char) if variable_box else self.size
        box_height = self.size
        leftmost, rightmost = self.get_char_bounds(char) if variable_box else (0, self.size - 1)
        
        for row in range(self.size):
            for col in range(leftmost, rightmost + 1):
                pixel_on = (rows[row] >> (self.size - 1 - col)) & 1
                actual_row = row_offset + row
                actual_col = col_offset + col #- leftmost
                
                if pixel_on:
                    pixels[p2i(actual_row, actual_col)] = color
                elif bg_color is not None:
                    pixels[p2i(actual_row, actual_col)] = bg_color
                    
        if margins is not None and bg_color is not None:
            top, bottom, left, right = margins
            # Clear top margin
            for r in range(row_offset-top, row_offset):
                for c in range(col_offset-left+leftmost, col_offset+rightmost+1+right):
                    pixels[p2i(r, c)] = bg_color 
            # Clear bottom margin
            for r in range(row_offset+box_height, row_offset+box_height+bottom):
                for c in range(col_offset-left+leftmost, col_offset+rightmost+1+right):
                    pixels[p2i(r, c)] = bg_color
            # Clear left margin
            for r in range(row_offset-top, row_offset+box_height+bottom):
                for c in range(col_offset-left+leftmost, col_offset+leftmost):
                    pixels[p2i(r, c)] = bg_color
            # Clear right margin
            for r in range(row_offset-top, row_offset+box_height+bottom):
                for c in range(col_offset+rightmost+1, col_offset+rightmost+1+right):
                    pixels[p2i(r, c)] = bg_color
        
        return pixels
    
    def get_text_width(self, text, spacing=2):
        """
        Calculate total width of a text string.
        
        Parameters:
        - text: String to measure
        - spacing: Pixels between characters
        
        Returns:
        - Total width in pixels
        """
        if not text:
            return 0
        
        total_width = 0
        for i, char in enumerate(text):
            total_width += self.get_char_width(char)
            if i < len(text) - 1:
                total_width += spacing
        
        return total_width


################################################################################
# region Font9x9 class
#################################################################################
class Font9x9(FontBase):    
    def __init__(self):
        FONT_9X9_BITMAP = {
            'A': [0b001111000, 0b011001100, 0b011001100, 0b011001100, 0b011111100, 0b011001100, 0b011001100, 0b011001100, 0b000000000],
            'B': [0b011111000, 0b011001100, 0b011001100, 0b011111000, 0b011001100, 0b011001100, 0b011001100, 0b011111000, 0b000000000],
            'C': [0b001111000, 0b011001100, 0b011000000, 0b011000000, 0b011000000, 0b011000000, 0b011001100, 0b001111000, 0b000000000],
            'D': [0b011110000, 0b011011000, 0b011001100, 0b011001100, 0b011001100, 0b011001100, 0b011011000, 0b011110000, 0b000000000],
            'E': [0b011111100, 0b011000000, 0b011000000, 0b011111000, 0b011000000, 0b011000000, 0b011000000, 0b011111100, 0b000000000],
            'F': [0b011111100, 0b011000000, 0b011000000, 0b011111000, 0b011000000, 0b011000000, 0b011000000, 0b011000000, 0b000000000],
            'G': [0b001111000, 0b011001100, 0b011000000, 0b011000000, 0b011011100, 0b011001100, 0b011001100, 0b001111000, 0b000000000],
            'H': [0b011001100, 0b011001100, 0b011001100, 0b011111100, 0b011001100, 0b011001100, 0b011001100, 0b011001100, 0b000000000],
            'I': [0b001111000, 0b000110000, 0b000110000, 0b000110000, 0b000110000, 0b000110000, 0b000110000, 0b001111000, 0b000000000],
            'J': [0b000001100, 0b000001100, 0b000001100, 0b000001100, 0b000001100, 0b011001100, 0b011001100, 0b001111000, 0b000000000],
            'K': [0b011001100, 0b011011000, 0b011110000, 0b011100000, 0b011110000, 0b011011000, 0b011001100, 0b011001100, 0b000000000],
            'L': [0b011000000, 0b011000000, 0b011000000, 0b011000000, 0b011000000, 0b011000000, 0b011000000, 0b011111100, 0b000000000],
            'M': [0b011000110, 0b011101110, 0b011111110, 0b011010110, 0b011000110, 0b011000110, 0b011000110, 0b011000110, 0b000000000],
            'N': [0b011000110, 0b011100110, 0b011110110, 0b011011110, 0b011001110, 0b011000110, 0b011000110, 0b011000110, 0b000000000],
            'O': [0b001111000, 0b011001100, 0b011001100, 0b011001100, 0b011001100, 0b011001100, 0b011001100, 0b001111000, 0b000000000],
            'P': [0b011111000, 0b011001100, 0b011001100, 0b011001100, 0b011111000, 0b011000000, 0b011000000, 0b011000000, 0b000000000],
            'Q': [0b001111000, 0b011001100, 0b011001100, 0b011001100, 0b011001100, 0b011011100, 0b011001100, 0b001111000, 0b000001100],
            'R': [0b011111000, 0b011001100, 0b011001100, 0b011001100, 0b011111000, 0b011011000, 0b011001100, 0b011001100, 0b000000000],
            'S': [0b001111000, 0b011001100, 0b011000000, 0b001110000, 0b000011000, 0b000001100, 0b011001100, 0b001111000, 0b000000000],
            'T': [0b011111100, 0b000110000, 0b000110000, 0b000110000, 0b000110000, 0b000110000, 0b000110000, 0b000110000, 0b000000000],
            'U': [0b011001100, 0b011001100, 0b011001100, 0b011001100, 0b011001100, 0b011001100, 0b011001100, 0b001111000, 0b000000000],
            'V': [0b011001100, 0b011001100, 0b011001100, 0b011001100, 0b011001100, 0b011001100, 0b001111000, 0b000110000, 0b000000000],
            'W': [0b011000110, 0b011000110, 0b011000110, 0b011000110, 0b011010110, 0b011111110, 0b011101110, 0b011000110, 0b000000000],
            'X': [0b011001100, 0b011001100, 0b001111000, 0b000110000, 0b000110000, 0b001111000, 0b011001100, 0b011001100, 0b000000000],
            'Y': [0b011001100, 0b011001100, 0b011001100, 0b001111000, 0b000110000, 0b000110000, 0b000110000, 0b000110000, 0b000000000],
            'Z': [0b011111100, 0b000001100, 0b000011000, 0b000110000, 0b001100000, 0b011000000, 0b011000000, 0b011111100, 0b000000000],
            '0': [0b001111000, 0b011001100, 0b011001100, 0b011001100, 0b011001100, 0b011001100, 0b011001100, 0b001111000, 0b000000000],
            '1': [0b000110000, 0b001110000, 0b000110000, 0b000110000, 0b000110000, 0b000110000, 0b000110000, 0b001111000, 0b000000000],
            '2': [0b001111000, 0b011001100, 0b000001100, 0b000011000, 0b000110000, 0b001100000, 0b011000000, 0b011111100, 0b000000000],
            '3': [0b001111000, 0b011001100, 0b000001100, 0b000111000, 0b000001100, 0b000001100, 0b011001100, 0b001111000, 0b000000000],
            '4': [0b000011000, 0b000111000, 0b001111000, 0b011011000, 0b011111100, 0b000011000, 0b000011000, 0b000011000, 0b000000000],
            '5': [0b011111100, 0b011000000, 0b011000000, 0b011111000, 0b000001100, 0b000001100, 0b011001100, 0b001111000, 0b000000000],
            '6': [0b001111000, 0b011001100, 0b011000000, 0b011111000, 0b011001100, 0b011001100, 0b011001100, 0b001111000, 0b000000000],
            '7': [0b011111100, 0b000001100, 0b000011000, 0b000110000, 0b001100000, 0b001100000, 0b001100000, 0b001100000, 0b000000000],
            '8': [0b001111000, 0b011001100, 0b011001100, 0b001111000, 0b011001100, 0b011001100, 0b011001100, 0b001111000, 0b000000000],
            '9': [0b001111000, 0b011001100, 0b011001100, 0b011001100, 0b001111100, 0b000001100, 0b011001100, 0b001111000, 0b000000000],
            '.': [0b000000000, 0b000000000, 0b000000000, 0b000000000, 0b000000000, 0b000000000, 0b001110000, 0b001110000, 0b000000000],
            ',': [0b000000000, 0b000000000, 0b000000000, 0b000000000, 0b000000000, 0b001110000, 0b001110000, 0b000110000, 0b001100000],
            '!': [0b000110000, 0b000110000, 0b000110000, 0b000110000, 0b000110000, 0b000000000, 0b000110000, 0b000110000, 0b000000000],
            '?': [0b001111000, 0b011001100, 0b000001100, 0b000011000, 0b000110000, 0b000000000, 0b000110000, 0b000110000, 0b000000000],
            '-': [0b000000000, 0b000000000, 0b000000000, 0b011111100, 0b011111100, 0b000000000, 0b000000000, 0b000000000, 0b000000000],
            '+': [0b000000000, 0b000110000, 0b000110000, 0b011111100, 0b011111100, 0b000110000, 0b000110000, 0b000000000, 0b000000000],
            ':': [0b000000000, 0b000000000, 0b001110000, 0b001110000, 0b000000000, 0b001110000, 0b001110000, 0b000000000, 0b000000000],
            ' ': [0b000000000, 0b000000000, 0b000000000, 0b000000000, 0b000000000, 0b000000000, 0b000000000, 0b000000000, 0b000000000],
        }
        super().__init__(size=9, bitmap=FONT_9X9_BITMAP)
        
        
################################################################################
# region Font8x8 class
#################################################################################
class Font8x8(FontBase):    
    def __init__(self):
        FONT_8X8_BITMAP = FONT_8X8 = {
            'A': [0b00111100, 0b01000010, 0b01000010, 0b01111110, 0b01000010, 0b01000010, 0b01000010, 0b00000000],
            'B': [0b01111100, 0b01000010, 0b01000010, 0b01111100, 0b01000010, 0b01000010, 0b01111100, 0b00000000],
            'C': [0b00111100, 0b01000010, 0b01000000, 0b01000000, 0b01000000, 0b01000010, 0b00111100, 0b00000000],
            'D': [0b01111000, 0b01000100, 0b01000010, 0b01000010, 0b01000010, 0b01000100, 0b01111000, 0b00000000],
            'E': [0b01111110, 0b01000000, 0b01000000, 0b01111100, 0b01000000, 0b01000000, 0b01111110, 0b00000000],
            'F': [0b01111110, 0b01000000, 0b01000000, 0b01111100, 0b01000000, 0b01000000, 0b01000000, 0b00000000],
            'G': [0b00111100, 0b01000010, 0b01000000, 0b01001110, 0b01000010, 0b01000010, 0b00111100, 0b00000000],
            'H': [0b01000010, 0b01000010, 0b01000010, 0b01111110, 0b01000010, 0b01000010, 0b01000010, 0b00000000],
            'I': [0b00111110, 0b00001000, 0b00001000, 0b00001000, 0b00001000, 0b00001000, 0b00111110, 0b00000000],
            'J': [0b00000010, 0b00000010, 0b00000010, 0b00000010, 0b01000010, 0b01000010, 0b00111100, 0b00000000],
            'K': [0b01000010, 0b01000100, 0b01001000, 0b01110000, 0b01001000, 0b01000100, 0b01000010, 0b00000000],
            'L': [0b01000000, 0b01000000, 0b01000000, 0b01000000, 0b01000000, 0b01000000, 0b01111110, 0b00000000],
            'M': [0b01000010, 0b01100110, 0b01011010, 0b01000010, 0b01000010, 0b01000010, 0b01000010, 0b00000000],
            'N': [0b01000010, 0b01100010, 0b01010010, 0b01001010, 0b01000110, 0b01000010, 0b01000010, 0b00000000],
            'O': [0b00111100, 0b01000010, 0b01000010, 0b01000010, 0b01000010, 0b01000010, 0b00111100, 0b00000000],
            'P': [0b01111100, 0b01000010, 0b01000010, 0b01111100, 0b01000000, 0b01000000, 0b01000000, 0b00000000],
            'Q': [0b00111100, 0b01000010, 0b01000010, 0b01000010, 0b01010010, 0b01001010, 0b00111100, 0b00000110],
            'R': [0b01111100, 0b01000010, 0b01000010, 0b01111100, 0b01001000, 0b01000100, 0b01000010, 0b00000000],
            'S': [0b00111100, 0b01000010, 0b01000000, 0b00111100, 0b00000010, 0b01000010, 0b00111100, 0b00000000],
            'T': [0b01111110, 0b00001000, 0b00001000, 0b00001000, 0b00001000, 0b00001000, 0b00001000, 0b00000000],
            'U': [0b01000010, 0b01000010, 0b01000010, 0b01000010, 0b01000010, 0b01000010, 0b00111100, 0b00000000],
            'V': [0b01000010, 0b01000010, 0b01000010, 0b01000010, 0b01000010, 0b00100100, 0b00011000, 0b00000000],
            'W': [0b01000010, 0b01000010, 0b01000010, 0b01000010, 0b01011010, 0b01100110, 0b01000010, 0b00000000],
            'X': [0b01000010, 0b01000010, 0b00100100, 0b00011000, 0b00100100, 0b01000010, 0b01000010, 0b00000000],
            'Y': [0b01000010, 0b01000010, 0b00100100, 0b00011000, 0b00001000, 0b00001000, 0b00001000, 0b00000000],
            'Z': [0b01111110, 0b00000010, 0b00000100, 0b00011000, 0b00100000, 0b01000000, 0b01111110, 0b00000000],
            '0': [0b00111100, 0b01000110, 0b01001010, 0b01010010, 0b01100010, 0b01000010, 0b00111100, 0b00000000],
            '1': [0b00001000, 0b00011000, 0b00001000, 0b00001000, 0b00001000, 0b00001000, 0b00011100, 0b00000000],
            '2': [0b00111100, 0b01000010, 0b00000010, 0b00001100, 0b00110000, 0b01000000, 0b01111110, 0b00000000],
            '3': [0b00111100, 0b01000010, 0b00000010, 0b00011100, 0b00000010, 0b01000010, 0b00111100, 0b00000000],
            '4': [0b00000100, 0b00001100, 0b00010100, 0b00100100, 0b01111110, 0b00000100, 0b00000100, 0b00000000],
            '5': [0b01111110, 0b01000000, 0b01111100, 0b00000010, 0b00000010, 0b01000010, 0b00111100, 0b00000000],
            '6': [0b00111100, 0b01000000, 0b01000000, 0b01111100, 0b01000010, 0b01000010, 0b00111100, 0b00000000],
            '7': [0b01111110, 0b00000010, 0b00000100, 0b00001000, 0b00010000, 0b00010000, 0b00010000, 0b00000000],
            '8': [0b00111100, 0b01000010, 0b01000010, 0b00111100, 0b01000010, 0b01000010, 0b00111100, 0b00000000],
            '9': [0b00111100, 0b01000010, 0b01000010, 0b00111110, 0b00000010, 0b00000010, 0b00111100, 0b00000000],
            '.': [0b00000000, 0b00000000, 0b00000000, 0b00000000, 0b00000000, 0b00011000, 0b00011000, 0b00000000],
            ',': [0b00000000, 0b00000000, 0b00000000, 0b00000000, 0b00011000, 0b00011000, 0b00001000, 0b00010000],
            '!': [0b00011000, 0b00011000, 0b00011000, 0b00011000, 0b00011000, 0b00000000, 0b00011000, 0b00000000],
            '?': [0b00111100, 0b01000010, 0b00000010, 0b00001100, 0b00010000, 0b00000000, 0b00010000, 0b00000000],
            '-': [0b00000000, 0b00000000, 0b00000000, 0b01111110, 0b00000000, 0b00000000, 0b00000000, 0b00000000],
            '+': [0b00000000, 0b00001000, 0b00001000, 0b00111110, 0b00001000, 0b00001000, 0b00000000, 0b00000000],
            ':': [0b00000000, 0b00011000, 0b00011000, 0b00000000, 0b00011000, 0b00011000, 0b00000000, 0b00000000],
            ' ': [0b00000000, 0b00000000, 0b00000000, 0b00000000, 0b00000000, 0b00000000, 0b00000000, 0b00000000],
        }
        super().__init__(size=8, bitmap=FONT_8X8_BITMAP)
        
        
################################################################################
# region Font7x7 class
################################################################################
class Font7x7(FontBase):
    def __init__(self):
        FONT_7X7_BITMAP = {
            'A': [0b0111000, 0b1000100, 0b1000100, 0b1111100, 0b1000100, 0b1000100, 0b0000000],
            'B': [0b1111000, 0b1000100, 0b1111000, 0b1000100, 0b1000100, 0b1111000, 0b0000000],
            'C': [0b0111000, 0b1000100, 0b1000000, 0b1000000, 0b1000100, 0b0111000, 0b0000000],
            'D': [0b1110000, 0b1001000, 0b1000100, 0b1000100, 0b1001000, 0b1110000, 0b0000000],
            'E': [0b1111100, 0b1000000, 0b1111000, 0b1000000, 0b1000000, 0b1111100, 0b0000000],
            'F': [0b1111100, 0b1000000, 0b1111000, 0b1000000, 0b1000000, 0b1000000, 0b0000000],
            'G': [0b0111000, 0b1000100, 0b1000000, 0b1011100, 0b1000100, 0b0111000, 0b0000000],
            'H': [0b1000100, 0b1000100, 0b1111100, 0b1000100, 0b1000100, 0b1000100, 0b0000000],
            'I': [0b0111000, 0b0010000, 0b0010000, 0b0010000, 0b0010000, 0b0111000, 0b0000000],
            'J': [0b0001000, 0b0001000, 0b0001000, 0b1001000, 0b1001000, 0b0110000, 0b0000000],
            'K': [0b1000100, 0b1001000, 0b1110000, 0b1001000, 0b1000100, 0b1000100, 0b0000000],
            'L': [0b1000000, 0b1000000, 0b1000000, 0b1000000, 0b1000000, 0b1111100, 0b0000000],
            'M': [0b1000100, 0b1101100, 0b1010100, 0b1000100, 0b1000100, 0b1000100, 0b0000000],
            'N': [0b1000100, 0b1100100, 0b1010100, 0b1001100, 0b1000100, 0b1000100, 0b0000000],
            'O': [0b0111000, 0b1000100, 0b1000100, 0b1000100, 0b1000100, 0b0111000, 0b0000000],
            'P': [0b1111000, 0b1000100, 0b1000100, 0b1111000, 0b1000000, 0b1000000, 0b0000000],
            'Q': [0b0111000, 0b1000100, 0b1000100, 0b1010100, 0b1001000, 0b0110100, 0b0000000],
            'R': [0b1111000, 0b1000100, 0b1111000, 0b1010000, 0b1001000, 0b1000100, 0b0000000],
            'S': [0b0111000, 0b1000100, 0b0110000, 0b0001100, 0b1000100, 0b0111000, 0b0000000],
            'T': [0b1111100, 0b0010000, 0b0010000, 0b0010000, 0b0010000, 0b0010000, 0b0000000],
            'U': [0b1000100, 0b1000100, 0b1000100, 0b1000100, 0b1000100, 0b0111000, 0b0000000],
            'V': [0b1000100, 0b1000100, 0b1000100, 0b1000100, 0b0101000, 0b0010000, 0b0000000],
            'W': [0b1000100, 0b1000100, 0b1000100, 0b1010100, 0b1101100, 0b1000100, 0b0000000],
            'X': [0b1000100, 0b1000100, 0b0101000, 0b0010000, 0b0101000, 0b1000100, 0b0000000],
            'Y': [0b1000100, 0b1000100, 0b0101000, 0b0010000, 0b0010000, 0b0010000, 0b0000000],
            'Z': [0b1111100, 0b0000100, 0b0001000, 0b0010000, 0b0100000, 0b1111100, 0b0000000],
            '0': [0b0111000, 0b1001100, 0b1010100, 0b1100100, 0b1000100, 0b0111000, 0b0000000],
            '1': [0b0010000, 0b0110000, 0b0010000, 0b0010000, 0b0010000, 0b0111000, 0b0000000],
            '2': [0b0111000, 0b1000100, 0b0001000, 0b0010000, 0b0100000, 0b1111100, 0b0000000],
            '3': [0b0111000, 0b1000100, 0b0011000, 0b0000100, 0b1000100, 0b0111000, 0b0000000],
            '4': [0b0001000, 0b0011000, 0b0101000, 0b1111100, 0b0001000, 0b0001000, 0b0000000],
            '5': [0b1111100, 0b1000000, 0b1111000, 0b0000100, 0b1000100, 0b0111000, 0b0000000],
            '6': [0b0111000, 0b1000000, 0b1111000, 0b1000100, 0b1000100, 0b0111000, 0b0000000],
            '7': [0b1111100, 0b0000100, 0b0001000, 0b0010000, 0b0010000, 0b0010000, 0b0000000],
            '8': [0b0111000, 0b1000100, 0b0111000, 0b1000100, 0b1000100, 0b0111000, 0b0000000],
            '9': [0b0111000, 0b1000100, 0b1000100, 0b0111100, 0b0000100, 0b0111000, 0b0000000],
            '.': [0b0000000, 0b0000000, 0b0000000, 0b0000000, 0b0110000, 0b0110000, 0b0000000],
            ',': [0b0000000, 0b0000000, 0b0000000, 0b0110000, 0b0110000, 0b0010000, 0b0100000],
            '!': [0b0010000, 0b0010000, 0b0010000, 0b0010000, 0b0000000, 0b0010000, 0b0000000],
            '?': [0b0111000, 0b1000100, 0b0001000, 0b0010000, 0b0000000, 0b0010000, 0b0000000],
            '-': [0b0000000, 0b0000000, 0b1111100, 0b0000000, 0b0000000, 0b0000000, 0b0000000],
            '+': [0b0000000, 0b0010000, 0b0010000, 0b1111100, 0b0010000, 0b0010000, 0b0000000],
            ':': [0b0000000, 0b0110000, 0b0110000, 0b0000000, 0b0110000, 0b0110000, 0b0000000],
            ' ': [0b0000000, 0b0000000, 0b0000000, 0b0000000, 0b0000000, 0b0000000, 0b0000000],
        }
        super().__init__(size=7, bitmap=FONT_7X7_BITMAP)
        
        
################################################################################
# region Font6x6 class
################################################################################
class Font6x6(FontBase):
    def __init__(self):
        FONT_6X6 = {
            'A': [0b011000, 0b100100, 0b111100, 0b100100, 0b100100, 0b000000],
            'B': [0b111000, 0b100100, 0b111000, 0b100100, 0b111000, 0b000000],
            'C': [0b011000, 0b100100, 0b100000, 0b100100, 0b011000, 0b000000],
            'D': [0b111000, 0b100100, 0b100100, 0b100100, 0b111000, 0b000000],
            'E': [0b111100, 0b100000, 0b111000, 0b100000, 0b111100, 0b000000],
            'F': [0b111100, 0b100000, 0b111000, 0b100000, 0b100000, 0b000000],
            'G': [0b011000, 0b100000, 0b101100, 0b100100, 0b011000, 0b000000],
            'H': [0b100100, 0b100100, 0b111100, 0b100100, 0b100100, 0b000000],
            'I': [0b011100, 0b001000, 0b001000, 0b001000, 0b011100, 0b000000],
            'J': [0b000100, 0b000100, 0b000100, 0b100100, 0b011000, 0b000000],
            'K': [0b100100, 0b101000, 0b110000, 0b101000, 0b100100, 0b000000],
            'L': [0b100000, 0b100000, 0b100000, 0b100000, 0b111100, 0b000000],
            'M': [0b100010, 0b110110, 0b101010, 0b100010, 0b100010, 0b000000],
            'N': [0b100010, 0b110010, 0b101010, 0b100110, 0b100010, 0b000000],
            'O': [0b011100, 0b100010, 0b100010, 0b100010, 0b011100, 0b000000],
            'P': [0b111000, 0b100100, 0b111000, 0b100000, 0b100000, 0b000000],
            'Q': [0b011100, 0b100010, 0b100010, 0b101010, 0b011100, 0b000010],
            'R': [0b111000, 0b100100, 0b111000, 0b101000, 0b100100, 0b000000],
            'S': [0b011100, 0b100000, 0b011000, 0b000100, 0b111000, 0b000000],
            'T': [0b111110, 0b001000, 0b001000, 0b001000, 0b001000, 0b000000],
            'U': [0b100010, 0b100010, 0b100010, 0b100010, 0b011100, 0b000000],
            'V': [0b100010, 0b100010, 0b100010, 0b010100, 0b001000, 0b000000],
            'W': [0b100010, 0b100010, 0b101010, 0b110110, 0b100010, 0b000000],
            'X': [0b100010, 0b010100, 0b001000, 0b010100, 0b100010, 0b000000],
            'Y': [0b100010, 0b010100, 0b001000, 0b001000, 0b001000, 0b000000],
            'Z': [0b111100, 0b000100, 0b001000, 0b010000, 0b111100, 0b000000],
            '0': [0b011100, 0b110010, 0b101010, 0b100110, 0b011100, 0b000000],
            '1': [0b001000, 0b011000, 0b001000, 0b001000, 0b011100, 0b000000],
            '2': [0b011000, 0b100100, 0b001000, 0b010000, 0b111100, 0b000000],
            '3': [0b111000, 0b000100, 0b011000, 0b000100, 0b111000, 0b000000],
            '4': [0b001000, 0b011000, 0b101000, 0b111100, 0b001000, 0b000000],
            '5': [0b111100, 0b100000, 0b111000, 0b000100, 0b111000, 0b000000],
            '6': [0b011000, 0b100000, 0b111000, 0b100100, 0b011000, 0b000000],
            '7': [0b111100, 0b000100, 0b001000, 0b010000, 0b010000, 0b000000],
            '8': [0b011000, 0b100100, 0b011000, 0b100100, 0b011000, 0b000000],
            '9': [0b011000, 0b100100, 0b011100, 0b000100, 0b011000, 0b000000],
            '.': [0b000000, 0b000000, 0b000000, 0b011000, 0b011000, 0b000000],
            ',': [0b000000, 0b000000, 0b011000, 0b011000, 0b001000, 0b010000],
            '!': [0b001000, 0b001000, 0b001000, 0b000000, 0b001000, 0b000000],
            '?': [0b011000, 0b100100, 0b001000, 0b000000, 0b001000, 0b000000],
            '-': [0b000000, 0b000000, 0b111100, 0b000000, 0b000000, 0b000000],
            '+': [0b000000, 0b001000, 0b111100, 0b001000, 0b000000, 0b000000],
            ':': [0b000000, 0b011000, 0b000000, 0b011000, 0b000000, 0b000000],
            ' ': [0b000000, 0b000000, 0b000000, 0b000000, 0b000000, 0b000000],
        }
        super().__init__(size=6, bitmap=FONT_6X6)


################################################################################
# region select_font
################################################################################
def select_font(size):
    if size == 9:
        return Font9x9()
    elif size == 8:
        return Font8x8()
    elif size == 7:
        return Font7x7()
    elif size <= 6:
        return Font6x6()
    else:
        assert False, "Unsupported font size"


################################################################################
# region draw_xmas_tree
################################################################################
def draw_xmas_tree(pixels):
    """
    Draw a Christmas tree on a 10x16 LED grid (portrait mode)
    Grid is 10 pixels wide, 16 pixels high
    """
    # Tree
    pixels[p2i(8, 4)] = LIGHT_GREEN
    pixels[p2i(8, 5)] = LIGHT_GREEN
    
    pixels[p2i(9, 3)] = DARK_GREEN
    pixels[p2i(9, 4)] = LIGHT_GREEN
    pixels[p2i(9, 5)] = RED
    pixels[p2i(9, 6)] = DARK_GREEN
    
    pixels[p2i(10, 2)] = DARK_GREEN
    pixels[p2i(10, 3)] = MAGENTA
    pixels[p2i(10, 4)] = LIGHT_GREEN
    pixels[p2i(10, 5)] = LIGHT_GREEN
    pixels[p2i(10, 6)] = DARK_GREEN
    pixels[p2i(10, 7)] = DARK_GREEN

    pixels[p2i(11, 3)] = DARK_GREEN
    pixels[p2i(11, 4)] = LIGHT_GREEN
    pixels[p2i(11, 5)] = LIGHT_GREEN
    pixels[p2i(11, 6)] = DARK_GREEN
    
    pixels[p2i(12, 2)] = DARK_GREEN
    pixels[p2i(12, 3)] = DARK_GREEN
    pixels[p2i(12, 4)] = MAGENTA
    pixels[p2i(12, 5)] = LIGHT_GREEN
    pixels[p2i(12, 6)] = RED
    pixels[p2i(12, 7)] = DARK_GREEN
    
    pixels[p2i(13, 1)] = DARK_GREEN
    pixels[p2i(13, 2)] = RED
    pixels[p2i(13, 3)] = DARK_GREEN
    pixels[p2i(13, 4)] = LIGHT_GREEN
    pixels[p2i(13, 5)] = LIGHT_GREEN
    pixels[p2i(13, 6)] = DARK_GREEN
    pixels[p2i(13, 7)] = DARK_GREEN
    pixels[p2i(13, 8)] = DARK_GREEN
    
    if False:
        # Snow line (right sides of tree)
        pixels[p2i(7, 4)] = YELLOW
        pixels[p2i(8, 5)] = WHITE
        pixels[p2i(9, 6)] = WHITE
        pixels[p2i(10, 7)] = WHITE
        pixels[p2i(11, 6)] = WHITE
        pixels[p2i(12, 7)] = WHITE
        pixels[p2i(13, 8)] = WHITE
    
    # Trunk
    pixels[p2i(14, 4)] = BROWN
    pixels[p2i(14, 5)] = BROWN
    pixels[p2i(15, 4)] = BROWN
    pixels[p2i(15, 5)] = BROWN
        
    return pixels


################################################################################
# region draw_star_of_bethlehem
################################################################################
def draw_star_of_bethlehem(pixels, position=(1, 4), size=1):
    """
    Draw the star of Bethlehem at given position with given size
    size=1: small star (single point)
    size=2: slightly larger
    size>=3: star shape
    """
    row, col = position
    
    if size == 1:
        # Single pixel star
        pixels[p2i(row, col)] = BRIGHT_YELLOW
    elif size == 2:
        # Small cross
        pixels[p2i(row, col)] = BRIGHT_YELLOW
        if row > 0:
            pixels[p2i(row-1, col)] = YELLOW
        if row < WIDTH-1:
            pixels[p2i(row+1, col)] = YELLOW
        if col > 0:
            pixels[p2i(row, col-1)] = YELLOW
        if col < HEIGHT-1:
            pixels[p2i(row, col+1)] = YELLOW
    elif size == 3:
        # Larger star shape
        pixels[p2i(row, col)] = BRIGHT_YELLOW
        if row > 0:
            pixels[p2i(row-1, col)] = YELLOW
        if row < WIDTH-1:
            pixels[p2i(row+1, col)] = YELLOW
        if col > 0:
            pixels[p2i(row, col-1)] = YELLOW
        if col < HEIGHT-1:
            pixels[p2i(row, col+1)] = YELLOW
        
        # Diagonal rays
        if row > 0 and col > 0:
            pixels[p2i(row-1, col-1)] = LIGHT_YELLOW
        if row > 0 and col < HEIGHT-1:
            pixels[p2i(row-1, col+1)] = LIGHT_YELLOW
        if row < WIDTH-1 and col > 0:
            pixels[p2i(row+1, col-1)] = LIGHT_YELLOW
        if row < WIDTH-1 and col < HEIGHT-1:
            pixels[p2i(row+1, col+1)] = LIGHT_YELLOW
            
    elif size >= 4:
        # Even larger star shape
        pixels[p2i(row, col)] = WHITE
        for dr in range(-size+1, size-1):
            for dc in range(-size+1, size-1):
                r = row + dr
                c = col + dc
                if 0 <= r < WIDTH and 0 <= c < HEIGHT:
                    distance = math.sqrt(dr**2 + dc**2)
                    if distance <= size/2:
                        if distance < size/4:
                            pixels[p2i(r, c)] = BRIGHT_YELLOW
                        elif distance < size/2 * 0.75:
                            pixels[p2i(r, c)] = YELLOW
                        else:
                            pixels[p2i(r, c)] = LIGHT_YELLOW
    
    return pixels


################################################################################
# region draw_expanding_sphere
################################################################################
def draw_expanding_sphere(pixels, center=(7, 4), radius=1.0, max_radius=12,
                          colors=(DARK_BLUE, WHITE, BRIGHT_YELLOW, YELLOW, ORANGE)):
    """
    Draw an expanding sphere/circle with gradient colors
    center: (row, col) center position
    radius: current radius of the sphere
    max_radius: maximum radius for color scaling
    """
    center_row, center_col = center
    # Iterate through all pixels
    for row in range(WIDTH):
        # Speed: skip rows outside bounding box
        if row < center[0] - radius - 1 or row > center[0] + radius + 1:
            continue
        
        for col in range(HEIGHT):
            # Speed: skip columns outside bounding box
            if col < center[1] - radius - 1 or col > center[1] + radius + 1:
                continue
            
            # Calculate distance from center
            distance = math.sqrt((row - center_row)**2 + (col - center_col)**2)
            
            # If within the current radius, color it based on distance
            if distance <= radius:
                # Normalize distance (0 at center, 1 at edge of sphere)
                norm_dist = distance / max(radius, 0.1)
                if norm_dist < 0.2:
                    # Very center: pure white
                    pixels[p2i(row, col)] = colors[0]
                elif norm_dist < 0.3:
                    # Center: bright white-yellow
                    pixels[p2i(row, col)] = colors[1]
                elif norm_dist < 0.6:
                    # Middle: bright yellow
                    pixels[p2i(row, col)] = colors[2]
                elif norm_dist < 0.8:
                    # Outer: yellow
                    pixels[p2i(row, col)] = colors[3]
                else:
                    # Edge: orange
                    pixels[p2i(row, col)] = colors[4]
    return pixels


################################################################################
# region Animation BaseClass
################################################################################
class Animation:
    """
    Base class for all animations.
    Provides interface for starting, stopping, resetting, and updating animations.
    
    States:
    - initialized: Animation created but not started
    - running: Animation is actively updating
    - stopped: Animation is paused/stopped
    - completed: Animation has finished (if applicable)
    """
    
    def __init__(self, name="BaseAnimation"):
        self.name = name
        self.state = "initialized"
        self.frame_count = 0
        self._background = None
        
    def start(self):
        """Start or resume the animation"""
        self.state = "running"
        
    def stop(self):
        """Stop/pause the animation"""
        self.state = "stopped"
        
    def reset(self):
        """Reset animation to initial state"""
        self.frame_count = 0
        self.state = "initialized"
        
    def update(self, pixels):
        """
        Update animation state and draw to pixels dict.
        Override this in subclasses.
        Returns modified pixels dict.
        """
        if self.state == "running":
            self.frame_count += 1
        return pixels
    
    def is_running(self):
        """Check if animation is currently running"""
        return self.state == "running"
    
    def get_state(self):
        """Get current status of the animation"""
        return self.state
    
    def set_frame(self, frame):
        """Set the current frame count"""
        self.frame_count = frame
    
    
################################################################################
# region AnimationManager
################################################################################
class AnimationManager:
    """
    Manages multiple animations with timing control.
    Allows scheduling animations to start/stop at specific frames.
    """
    
    def __init__(self, 
                 loop=True,
                 frames_between_loops=20):
        self.animations = []
        self.global_frame = 0
        self.loop = loop
        self.duration = -1  # Total duration in frames (None = infinite)
        self.frames_between_loops = frames_between_loops
        
    def add_animation(self, animation, start_frame=0, duration=None):
        """
        Add an animation to the manager.
        
        Parameters:
        - animation: Animation instance
        - start_frame: Frame number when animation should start (default: 0)
        - duration: How many frames the animation should run (None = infinite)
        """
        self.animations.append({
            'animation': animation,
            'start_frame': start_frame,
            'duration': duration,
            'end_frame': start_frame + duration if duration is not None else None
        })
        
        if duration is None:
            self.duration = None  # Infinite duration
        elif self.duration != None:
            self.duration = max(self.duration, start_frame + duration)
            
    def update(self, pixels):
        """
        Update all animations based on current global frame.
        Returns modified pixels dict.
        """
        if self.loop and self.duration is not None:
            if self.global_frame >= self.duration + self.frames_between_loops:
                self.global_frame = 0
                for anim_info in self.animations:
                    anim_info['animation'].reset()
        
        for anim_info in self.animations:
            animation = anim_info['animation']
            start_frame = anim_info['start_frame']
            end_frame = anim_info['end_frame']
            
            # Check if animation should start
            if self.global_frame >= start_frame:
                if animation.get_state() == "initialized":
                    animation.start()
                    if DEBUG:
                        msg = "Starting animation (%s) at frame %03d..."
                        print(msg % (animation.name, self.global_frame))
                    
            # Check if animation should stop
            if end_frame is not None and self.global_frame >= end_frame:
                if animation.get_state() == "running":
                    animation.stop()
                    if DEBUG:
                        msg = "Stopping animation (%s) at frame %03d..."
                        print(msg % (animation.name, self.global_frame))
            
            # Update animation if running
            if animation.get_state() == "running":
                pixels = animation.update(pixels)
        
        self.global_frame += 1
        return pixels
    
    def reset(self):
        """Reset manager and all animations"""
        self.global_frame = 0
        for anim_info in self.animations:
            anim_info['animation'].reset()
            
    def set_frame(self, frame):
        """Set the global frame counter"""
        self.global_frame = frame
        for anim_info in self.animations:
            anim_info['animation'].set_frame(frame - anim_info['start_frame'])
        
    def get_frame(self):
        """Get the current global frame counter"""
        return self.global_frame


################################################################################
# region ChristmasTreeAnimation
################################################################################
class ChristmasTreeAnimation(Animation):
    """Static Christmas tree display"""
    
    def __init__(self, name="Christmas tree"):
        super().__init__(name=name)
        
    def update(self, pixels):
        if self.is_running():
            pixels = draw_xmas_tree(pixels)
            self.frame_count += 1
        return pixels


################################################################################
# region SnowflakeAnimation
################################################################################
class SnowflakeAnimation(Animation):
    
    def __init__(self, n=25, 
                 speed=1,
                 melt_prob=0.05, 
                 name="Snowflake"):
        super().__init__(name=name)
        self.num_snowflakes = n
        self.snowflakes = []
        self.speed = speed
        self.melt_prob = melt_prob
        self.enable_melting = False
        
        random.seed(42)
        cols = []
        for _ in range(self.num_snowflakes):
            cols.append(self.sample_snowflake_cols(cols))
            
        for i in range(self.num_snowflakes):
            snowflake = {
                'row': self.sample_row(cols, i),
                'col': cols[i],
                'visible': True,
            }
            self.snowflakes.append(snowflake)
            
        max_row = max([flake['row'] for flake in self.snowflakes])
        self.max_snowflake_row = max_row + 2
        
    def reset(self):
        super().reset()
        for i, flake in enumerate(self.snowflakes):
            flake['row'] = float(i * 2)
            flake['visible'] = True
            
    def sample_snowflake_cols(self, cols):
        last_flakes = set(cols[-5:])
        candidates = set(range(HEIGHT))
        available = list(candidates - last_flakes)
        return random.choice(available)
    
    def sample_row(self, cols, i):
        return i * 2
    
    def update(self, pixels):
        pixels["background"] = DARK_BLUE
        if not self.is_running():
            return pixels
        
        for flake in self.snowflakes:
            # Move snowflake down every frame
            flake['row'] += self.speed
            # Randomly decide if snowflake disappears
            if random.random() < self.melt_prob and self.enable_melting:
                flake['visible'] = False
            
            # Reset to top if reached bottom
            if flake['row'] >= max(self.max_snowflake_row, WIDTH):
                flake['row'] = 0.0
                flake['visible'] = True
                
        self.frame_count += 1
        
        for flake in self.snowflakes:
            if flake['row'] < WIDTH and flake['visible']:
                row = int(flake['row'])
                col = int(flake['col'])
                pixels[p2i(row, col)] = WHITE
        
        return pixels
        
        
################################################################################
# region TextFlashAnimation
################################################################################
class TextFlashAnimation(Animation):
    """Text Flash Animation.
    Displays one character for a set period before moving to the next.
    Loops back to start when reaching the end of the text, unless loop=False.
    
    Parameters:
    - text: Text string to scroll
    - color: RGB tuple for text color
    - offset: (row, col) tuple for text position
    - font_size: Font size (6, 7, or 8)
    - period: Number of frames to display each character
    - loop: Whether to loop back to start after reaching end of text
    """
    
    def __init__(self, text, 
                 color=(5, 0, 5), 
                 background_color=None,
                 box_color=None,
                 box_margins=None,
                 variable_box=True,
                 offset=(4, 1),
                 font_size=6, 
                 frames_on=10,
                 frames_off=1,
                 loop=True,
                 name="Text flash"):
        super().__init__(name=name)
        self.text = text.replace(' ', '')  # Remove spaces for scrolling
        self.color = color
        self.background_color = background_color
        self.box_color = box_color
        self.box_margins = box_margins
        self.variable_box = variable_box
        self.offset = offset
        self.font_size = font_size
        self.frames_on = frames_on
        self.frames_off = frames_off
        self.char_index = 0
        self.loop = loop
        self.font = select_font(font_size)
        
    def reset(self):
        super().reset()
        self.char_index = 0
        
    def set_frame(self, frame):
        if frame < 0:
            return
        total_period = self.frames_on + self.frames_off
        char_index = frame // total_period
        if not self.loop and char_index >= len(self.text):
            self.stop()
            if DEBUG:
                msg = "Stopping animation (%s) at frame %03d..."
                print(msg % (self.name, frame))
        else:
            self.char_index = char_index % len(self.text)
        
    def update(self, pixels):
        if not self.is_running():
            return pixels
        
        if self.background_color is not None:
            pixels["background"] = self.background_color
        
        self.frame_count += 1
        if (self.frame_count < self.frames_on):
            pixels = self.font.draw(pixels, 
                                    self.text[self.char_index],
                                    row_offset=self.offset[0], 
                                    col_offset=self.offset[1],
                                    color=self.color,
                                    bg_color=self.box_color,
                                    margins=self.box_margins,
                                    variable_box=self.variable_box)
        elif self.frame_count >= self.frames_on + self.frames_off:
            self.frame_count = 0
            new_char_index = (self.char_index + 1)
            self.char_index = new_char_index % len(self.text)
            if not self.loop and new_char_index >= len(self.text):
                self.stop()
                if DEBUG:
                    msg = "Stopping animation (%s) at frame %03d..."
                    print(msg % (self.name, self.frame_count))
                return pixels
            
        return pixels


################################################################################
# region TextScrollAnimation
################################################################################
class TextScrollAnimation(Animation):
    
    def __init__(self, text, 
                 color=(5, 0, 5), 
                 background_color=None,
                 offset=(4, 1),
                 speed=2,
                 font_size=6,
                 loop=True,
                 name="Text scroll"):
        super().__init__(name=name)
        
        self.text = text
        self.color = color
        self.background_color = background_color
        self.offset = offset
        self.font_size = font_size
        self.scroll_offset = 0
        self.scroll_speed = speed
        self.loop = loop
        self.font = select_font(font_size)
        
        # Compute variable widths of characters
        self.widths = []
        self.offsets = []
        for char in self.text:
            char_width = self.font.get_char_width(char)
            char_bounds = self.font.get_char_bounds(char)
            self.offsets.append(char_bounds[0])
            self.widths.append(char_width + 2)  # Add 2 pixels spacing
            
    def reset(self):
        super().reset()
        self.scroll_offset = 0
        
    def set_frame(self, frame):
        if frame < 0:
            return
        total_width = sum(self.widths)
        scroll_offset = frame * self.scroll_speed
        if not self.loop and scroll_offset > total_width:
            self.stop()
            if DEBUG:
                msg = "Stopping animation (%s) at frame %03d..."
                print(msg % (self.name, frame))
        self.scroll_offset = scroll_offset
        
    def update(self, pixels):
        if not self.is_running():
            return pixels
        
        if self.background_color is not None:
            pixels["background"] = self.background_color
        
        self.frame_count += 1
        for i, char in enumerate(self.text):
            scroll_offset = int(self.scroll_offset)
            col_offset = (self.offset[1] + sum(self.widths[:i]) 
                          - scroll_offset - self.offsets[i])
            # Only draw character if within visible area
            if -self.widths[i] < col_offset < WIDTH:
                pixels = self.font.draw(pixels, 
                                        char,
                                        row_offset=self.offset[0], 
                                        col_offset=col_offset,
                                        color=self.color)
        self.scroll_offset += self.scroll_speed
        if self.scroll_offset > sum(self.widths) + self.offset[1]:
            self.scroll_offset = 0
            if not self.loop:
                self.stop()
                if DEBUG:
                    msg = "Stopping animation (%s) at frame %03d..."
                    print(msg % (self.name, self.frame_count))
        return pixels


################################################################################
# region StarAnimation
################################################################################
class StarOfBethlehemAnimation(Animation):
    """
    Manages the star of Bethlehem animation sequence:
    1. Small star above tree (static)
    2. Star begins to grow
    3. Star expands into sphere
    4. Sphere takes over entire screen
    5. Fade to yellow screen
    """
    
    def __init__(self, 
                 start_pos=(1, 4),
                 end_pos=(7, 4),
                 wait_frames=100, 
                 growth_frames=50, 
                 explosion_frames=30,
                 name="Star of Bethlehem"):
        super().__init__(name=name)
        
        self.wait_frames = wait_frames
        self.growth_frames = growth_frames
        self.explosion_frames = explosion_frames
        self.explosion_colors = (DARK_BLUE, WHITE, BRIGHT_YELLOW, YELLOW, ORANGE)
        
        self.start_pos = start_pos
        self.end_pos = end_pos
        
        self.phase = 'waiting'  # waiting, growing, exploding, uniform_screen
        self.phase_starts = dict(waiting=0, 
                                 growing=wait_frames,
                                 exploding=wait_frames+growth_frames,
                                 uniform_screen=wait_frames+growth_frames+explosion_frames)
        self.star_size = 1
        self.sphere_radius = 0
        self.phase_frame = 0
        
    def reset(self):
        super().reset()
        self.phase = 'waiting'
        self.star_size = 1
        self.sphere_radius = 0
        self.phase_frame = 0
        
    def set_frame(self, frame):
        """Set the current frame count and phase based on frame number"""
        self.frame_count = frame
        if frame < self.phase_starts['growing']:
            self.phase = 'waiting'
            self.phase_frame = frame - self.phase_starts['waiting']
        elif frame < self.phase_starts['exploding']:
            self.phase = 'growing'
            self.phase_frame = frame - self.phase_starts['growing']
        elif frame < self.phase_starts['uniform_screen']:
            self.phase = 'exploding'
            self.phase_frame = frame - self.phase_starts['exploding']
        else:
            self.phase = 'uniform_screen'
            self.phase_frame = frame - self.phase_starts['uniform_screen']
        
    def update(self, pixels):
        if not self.is_running():
            return pixels
        
        self.frame_count += 1
        self.phase_frame += 1
        
        if self.phase == 'waiting':
            # Draw small star above tree
            pixels = draw_star_of_bethlehem(pixels, 
                                            position=self.start_pos, 
                                            size=1)
            
            if self.phase_frame >= self.wait_frames:
                self.phase = 'growing'
                self.phase_frame = 0
                if DEBUG:
                    msg = "Star: Starting growth phase at frame %03d..."
                    print(msg % (self.frame_count))
                
        elif self.phase == 'growing':
            # Star grows from size 1 to 4
            progress = self.phase_frame / self.growth_frames
            self.star_size = 1 + int(progress**2 * 4)
            pos = (
                int(self.start_pos[0] + (self.end_pos[0] - self.start_pos[0]) * progress),
                int(self.start_pos[1] + (self.end_pos[1] - self.start_pos[1]) * progress)
            )
            
            pixels = draw_star_of_bethlehem(pixels, 
                                            position=pos, 
                                            size=self.star_size)
            
            if self.phase_frame >= self.growth_frames:
                self.phase = 'exploding'
                self.phase_frame = 0
                if DEBUG:
                    msg = "Star: Starting explosion phase at frame %03d..."
                    print(msg % (self.frame_count))
                
        elif self.phase == 'exploding':
            # Star transforms into expanding sphere
            progress = self.phase_frame / self.explosion_frames
            self.sphere_radius = 2 + (progress * 50)
            pixels = draw_expanding_sphere(pixels, 
                                           center=self.end_pos, 
                                           radius=self.sphere_radius,
                                           colors=self.explosion_colors)
            
            if self.phase_frame >= self.explosion_frames:
                self.phase = 'uniform_screen'
                self.phase_frame = 0
                if DEBUG:
                    msg = "Star: Reached uniform screen phase at frame %03d..."
                    print(msg % (self.frame_count))
                
        elif self.phase == 'uniform_screen':
            pixels["background"] = self.explosion_colors[0]
        else:
            assert False, "Unknown phase in StarOfBethlehemAnimation"
        return pixels
    
    
################################################################################
# region Firework Animation
################################################################################
class FireworkAnimation(Animation):
    def __init__(self, 
                 initial_spawn_rate=0.05,  # probability per pixel per frame
                 final_spawn_rate=0.3,
                 spawn_ramp_duration=100,  # frames over which spawn rate increases
                 particle_lifetime=5,      # frames before particle vanishes
                 colors=None,              # list of confetti colors
                 background_color=WHITE,
                 name="Firework"
                 ):             
        super().__init__(name=name)
        
        self.initial_spawn_rate = initial_spawn_rate
        self.final_spawn_rate = final_spawn_rate
        self.spawn_ramp_duration = spawn_ramp_duration
        self.particle_lifetime = particle_lifetime
        if colors is None:
            colors = [RED, GREEN, BLUE, YELLOW, MAGENTA]
        self.colors = colors
        self.background_color = background_color
        self.particles = []  # List of active particles
        
    def reset(self):
        super().reset()
        self.particles = []
        
    def set_frame(self, frame):
        if frame < 0:
            return
        self.frame_count = frame
        
    def update(self, pixels):
        if not self.is_running():
            return pixels
        
        self.frame_count += 1
        pixels["background"] = self.background_color
        
        # Calculate current spawn rate based on progress
        progress = self.frame_count / self.spawn_ramp_duration
        progress = min(max(progress, 0.0), 1.0)
        current_spawn_rate = (self.initial_spawn_rate + 
                              (self.final_spawn_rate - self.initial_spawn_rate) * progress)
        
        # Spawn new particles
        for row in range(0, WIDTH, 2):
            for col in range(0, HEIGHT, 2):
                if random.random() < current_spawn_rate:
                    particle = {
                        'row': row,
                        'col': col,
                        'lifetime': self.particle_lifetime,
                        'color': random.choice(self.colors)
                    }
                    self.particles.append(particle)
        
        # Update and draw particles
        new_particles = []
        for particle in self.particles:
            if particle['lifetime'] > 0:
                pixels[p2i(particle['row'], particle['col'])] = particle['color']
                particle['lifetime'] -= 1
                new_particles.append(particle)
        
        self.particles = new_particles
        
        return pixels
    
    
################################################################################
# region Main Animation Loop
################################################################################
def render(strip, pixels):
    """Render pixel dictionary to LED strip"""
    background = pixels.pop('background', DARK_BLUE)
    strip.pixels_fill(background)
    
    for idx, color in pixels.items():
        if isinstance(idx, str):  # Skip special keys like "background"
            continue
        if 0 <= idx < 160:
            strip.pixels_set(idx, color)
    
    strip.pixels_show()
    

def animate_xmas_tree():
    strip = NeoPixel()
    strip.brightness = 1.8
    
    # Create animation manager
    manager = AnimationManager(frames_between_loops=20)
    
    # Create animation instances
    tree_anim = ChristmasTreeAnimation()
    snow_anim = SnowflakeAnimation(n=25, 
                                   speed=0.5,
                                   melt_prob=0.05)
    xmas_text_anim = TextScrollAnimation(
        text="MERRY CHRISTMAS! ",
        color=(5, 0, 5),
        speed=1,
        offset=(1, HEIGHT+1),
        font_size=6,
        loop=False
    )
    star_anim = StarOfBethlehemAnimation(
        wait_frames=20,
        growth_frames=50,
        explosion_frames=50
    )
    firework_anim = FireworkAnimation(
        initial_spawn_rate=0.02,
        final_spawn_rate=0.08,
        spawn_ramp_duration=100,  # frames over which spawn rate increases
        particle_lifetime=5,
        background_color=DARK_BLUE
    )
    newyear_text_anim = TextFlashAnimation(
        text="AND HAPPY NEW YEAR! ",
        color=WHITE,
        box_color=DARK_BLUE,
        box_margins=(1, 0, 0, 0),
        offset=(4, 1),
        font_size=9,
        frames_on=9,
        frames_off=1,
        loop=False
    )
    
    if False:
        # Debug fonts rendering    
        test = TextFlashAnimation(
            text="0123456789",
            color=WHITE,
            box_color=BLACK,
            box_margins=(1, 3, 2, 1),
            offset=(2, 1),
            font_size=9,
            loop=True,
        )

        test.start()
        while True:
            pixels = {}
            pixels = test.update(pixels)
            render(strip, pixels)
            time.sleep(0.1)
        return
    
    # Add animations to manager with timing
    # Phase 1: Tree with snow and Christmas text
    manager.add_animation(tree_anim, start_frame=0, duration=210)
    manager.add_animation(snow_anim, start_frame=0, duration=200)
    manager.add_animation(xmas_text_anim, start_frame=30, duration=150)
    
    # Phase 2: Star animation
    manager.add_animation(star_anim, start_frame=140, duration=200)
    
    # Phase 3: Fireworks
    manager.add_animation(firework_anim, start_frame=220, duration=210)
    
    # Phase 4: New Year text
    manager.add_animation(newyear_text_anim, start_frame=250, duration=150)
    
    # Target frame rate
    FRAME_RATE = 10  # frames per second
    
    #manager.set_frame(150)
    
    # Main loop
    while True:
        start_time = time.ticks_ms()
        pixels = {}
        pixels["background"] = DARK_BLUE  # Default background
        pixels = manager.update(pixels)
        render(strip, pixels)
        elapsed = time.ticks_ms() - start_time
        sleep_time = max(0, int(1000 / FRAME_RATE) - elapsed)
        time.sleep(sleep_time / 1000.0)
        if DEBUG:
            print("Frame:", manager.get_frame())

if __name__=='__main__':
    animate_xmas_tree()