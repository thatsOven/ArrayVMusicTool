# ArrayV Music Tool
A tool used to convert MIDI files in Java code that plays music using the ArrayV API.

The program will produce a file called `MusicSort.java` that can be added in ArrayV's miscellaneous sorts.

# Usage
`ArrayVMusicTool.py input_file.midi`

# Command line arguments
- `--patched`
    - Tells the program that the target uses a patched ArrayV sound system (from [patches](https://github.com/thatsOven/ArrayVMusicTool/tree/main/patches). Credits to PCBoyGames for 4.0 compatibility).
    - **Usage:** --patched
- `-v4`
    - Tells the program that the taget uses ArrayV version 4. The generated code will be slightly different to account for that.
    - **Usage:** --v4
