#!/usr/bin/env python3
"""
Barcode to Guitar Tab Converter
Translates product barcodes into metal riffs
"""

import sys
from typing import List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

try:
    from PIL import Image
    from pyzbar.pyzbar import decode
    BARCODE_SUPPORT = True
except ImportError:
    BARCODE_SUPPORT = False
    print("Note: Install 'pillow' and 'pyzbar' for image barcode scanning")
    print("pip install pillow pyzbar")


class ScaleMode(Enum):
    """Different scale modes for mapping"""
    MINOR_PENTATONIC = "minor_pentatonic"  # Classic metal sound
    NATURAL_MINOR = "natural_minor"
    HARMONIC_MINOR = "harmonic_minor"
    CHROMATIC = "chromatic"
    POWER_CHORD = "power_chord"  # Root and fifth only


@dataclass
class GuitarNote:
    """Represents a note on guitar"""
    string: int  # 0-5 (low E to high E)
    fret: int    # 0-24
    duration: int = 1  # In 16th notes


class BarcodeToTab:
    """Convert barcodes to guitar tablature"""
    
    # Standard tuning (low to high): E A D G B E
    STANDARD_TUNING = ['E', 'A', 'D', 'G', 'B', 'E']
    
    # Scale patterns (intervals from root)
    SCALES = {
        ScaleMode.MINOR_PENTATONIC: [0, 3, 5, 7, 10],  # Root, m3, P4, P5, m7
        ScaleMode.NATURAL_MINOR: [0, 2, 3, 5, 7, 8, 10],  # Natural minor
        ScaleMode.HARMONIC_MINOR: [0, 2, 3, 5, 7, 8, 11],  # Harmonic minor
        ScaleMode.CHROMATIC: list(range(13)),  # All semitones
        ScaleMode.POWER_CHORD: [0, 7],  # Root and fifth only
    }
    
    def __init__(self, root_note: str = 'E', root_fret: int = 0, 
                 scale_mode: ScaleMode = ScaleMode.MINOR_PENTATONIC):
        """
        Initialize converter
        
        Args:
            root_note: Root note/string (E, A, D, G, B)
            root_fret: Starting fret position (0-12)
            scale_mode: Musical scale to use
        """
        self.root_note = root_note
        self.root_fret = root_fret
        self.scale_mode = scale_mode
        self.scale = self.SCALES[scale_mode]
    
    def read_barcode_from_image(self, image_path: str) -> Optional[str]:
        """Read barcode from image file"""
        if not BARCODE_SUPPORT:
            print("Error: Barcode scanning requires 'pillow' and 'pyzbar'")
            return None
        
        try:
            img = Image.open(image_path)
            barcodes = decode(img)
            
            if not barcodes:
                print(f"No barcode found in {image_path}")
                return None
            
            # Return first barcode found
            barcode_data = barcodes[0].data.decode('utf-8')
            barcode_type = barcodes[0].type
            print(f"Found {barcode_type}: {barcode_data}")
            return barcode_data
            
        except Exception as e:
            print(f"Error reading barcode: {e}")
            return None
    
    def barcode_to_notes(self, barcode: str) -> List[GuitarNote]:
        """
        Convert barcode string to guitar notes
        
        Maps digits to scale degrees and creates a riff pattern
        """
        notes = []
        
        # Extract just the digits
        digits = [int(c) for c in barcode if c.isdigit()]
        
        if not digits:
            print("No digits found in barcode")
            return notes
        
        # Start on low E string
        current_string = 0
        
        for i, digit in enumerate(digits):
            # Map digit to scale degree
            scale_degree = digit % len(self.scale)
            fret = self.root_fret + self.scale[scale_degree]
            
            # Keep frets reasonable (0-19)
            while fret > 19:
                fret -= 12
            
            # Occasionally move to different string for variety
            if i > 0 and i % 4 == 0:
                current_string = (current_string + 1) % 6
            
            # Add some rhythmic variety based on digit value
            duration = 2 if digit in [0, 5] else 1  # Longer notes on 0s and 5s
            
            notes.append(GuitarNote(current_string, fret, duration))
        
        return notes
    
    def generate_power_chord_riff(self, barcode: str) -> List[GuitarNote]:
        """
        Generate a power chord based riff
        Perfect for metal!
        """
        notes = []
        digits = [int(c) for c in barcode if c.isdigit()]
        
        if not digits:
            return notes
        
        # Use low E and A strings for power chords
        for i, digit in enumerate(digits):
            # Map to frets (0-12 range)
            root_fret = (digit % 13)
            
            # Power chord: root on E string, fifth on A string
            notes.append(GuitarNote(0, root_fret, 2))  # Root
            notes.append(GuitarNote(1, root_fret + 2, 2))  # Fifth (2 frets up on A string)

            # Add some palm muted hits
            if digit in [0, 5]:
                notes.append(GuitarNote(0, root_fret, 1))
                notes.append(GuitarNote(1, root_fret + 2, 1))
        
        return notes
    
    def notes_to_tab(self, notes: List[GuitarNote], title: str = "Barcode Riff") -> str:
        """
        Convert notes to ASCII guitar tablature
        """
        if not notes:
            return "No notes to display"
        
        # Calculate total length needed
        total_length = sum(note.duration * 2 for note in notes) + 2
        
        # Initialize tab lines
        tab_lines = [
            ['-' for _ in range(total_length)]
            for _ in range(6)
        ]
        
        # Place notes on tab
        position = 1
        for note in notes:
            string_idx = 5 - note.string  # Reverse for display (high E on top)
            fret_str = str(note.fret)
            
            # Place fret number
            for char_idx, char in enumerate(fret_str):
                if position + char_idx < total_length:
                    tab_lines[string_idx][position + char_idx] = char
            
            # Move position based on duration
            position += note.duration * 2
        
        # Build output
        output = []
        output.append(f"\n{title}")
        output.append(f"Scale: {self.scale_mode.value} in {self.root_note}")
        output.append("=" * 60)
        
        tuning_labels = ['e|', 'B|', 'G|', 'D|', 'A|', 'E|']
        for i, (label, line) in enumerate(zip(tuning_labels, tab_lines)):
            output.append(f"{label}{''.join(line)}|")
        
        output.append("=" * 60)
        
        return '\n'.join(output)
    
    def convert(self, barcode: str, use_power_chords: bool = False) -> str:
        """
        Main conversion function
        
        Args:
            barcode: Barcode string (numbers or full code)
            use_power_chords: Use power chord mode for heavier sound
        """
        if use_power_chords:
            notes = self.generate_power_chord_riff(barcode)
            title = f"Power Chord Riff - {barcode}"
        else:
            notes = self.barcode_to_notes(barcode)
            title = f"Barcode Riff - {barcode}"
        
        return self.notes_to_tab(notes, title)


def main():
    """Main CLI interface"""
    print("🎸 Barcode to Guitar Tab Converter 🎸")
    print("=" * 60)
    
    # Parse arguments
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python barcode_to_tab.py <barcode_number>")
        print("  python barcode_to_tab.py <image_path>")
        print("\nExamples:")
        print("  python barcode_to_tab.py 012345678905")
        print("  python barcode_to_tab.py product.jpg")
        print("\nOptions:")
        print("  Add '--power' for power chord mode")
        print("  Add '--harmonic' for harmonic minor scale")
        return
    
    input_arg = sys.argv[1]
    use_power = '--power' in sys.argv
    use_harmonic = '--harmonic' in sys.argv
    
    # Determine scale mode
    scale_mode = ScaleMode.HARMONIC_MINOR if use_harmonic else ScaleMode.MINOR_PENTATONIC
    
    # Create converter
    converter = BarcodeToTab(root_note='E', root_fret=0, scale_mode=scale_mode)
    
    # Check if input is an image file
    if input_arg.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
        barcode = converter.read_barcode_from_image(input_arg)
        if not barcode:
            return
    else:
        barcode = input_arg
    
    # Generate tablature
    print(f"\nProcessing barcode: {barcode}")
    tab = converter.convert(barcode, use_power_chords=use_power)
    print(tab)
    
    # Show different variations
    if not use_power:
        print("\n" + "=" * 60)
        print("POWER CHORD VERSION (heavier!):")
        tab_power = converter.convert(barcode, use_power_chords=True)
        print(tab_power)
    
    # Suggestions
    print("\n💡 Tips:")
    print("  - Try different products to find cool riffs!")
    print("  - Use --power for heavy palm-muted power chords")
    print("  - Use --harmonic for that neoclassical metal sound")
    print("  - Barcodes with repeating digits make interesting patterns")


if __name__ == '__main__':
    main()
