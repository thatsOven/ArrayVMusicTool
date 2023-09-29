# Copyright (c) 2023 thatsOven
# 
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

from sys  import argv
from mido import MidiFile

# max is 15, but ArrayV sometimes doesn't handle clearMark calls in time, 
# so this is a precaution to avoid ArrayIndexOutOfBoundsException
MAX_NOTES = 14 
MAX_LINES = 256
INDENT = " " * 4
CODE = """
package io.github.arrayv.sorts.misc;

import io.github.arrayv.main.ArrayVisualizer;
import io.github.arrayv.sorts.templates.Sort;

public final class MusicSort extends Sort {
    public MusicSort(ArrayVisualizer arrayVisualizer) {
        super(arrayVisualizer);

        this.setSortListName("Music");
        this.setRunAllSortsName("Music Sort");
        this.setRunSortName("Music Sort");
        this.setCategory("Miscellaneous Sorts");
        this.setBucketSort(false);
        this.setRadixSort(false);
        this.setUnreasonablySlow(false);
        this.setUnreasonableLimit(0);
        this.setBogoSort(false);
    }

    private int[] a;
    private int   l;

METHODS    @Override
    public void runSort(int[] array, int length, int bucketCount) throws Exception {
        a = array;
        l = length;
CODE    }
}
"""

class Event:
    def __init__(self, type, note, channel, sleep):
        self.type    = type
        self.note    = note
        self.channel = channel
        self.time    = sleep

    def __repr__(self):
        return "[" + str(self.channel) + "] " + self.type + " " + str(self.note) + " sleep: " + str(self.time)

class ArrayVMusicTool:
    def readMidi(self, fileName):
        mid = MidiFile(fileName)

        events = []
        for message in mid:
            if message.type in ("note_on", "note_off"):
                if message.type == "note_on" and message.velocity == 0:
                    type_ = "note_off"
                else: type_ = message.type

                events.append(Event(
                    type_, message.note, 
                    message.channel, message.time
                ))
            elif message.type == "end_of_track":
                events.append(Event("", 0, 0, message.time))
                break
            elif len(events) != 0:
                events[-1].time += message.time

        for i in range(len(events) - 1):
            events[i].time = events[i + 1].time
        events.pop(-1)

        return events

    def convert(self, fileName):
        methods = [""]
        playing   = {}
        discarded = []
        for i in range(MAX_NOTES):
            playing[i] = None

        cnt = 0
        for event in self.readMidi(fileName):
            print(event)

            pair  = (event.note, event.channel)
            sound = (event.note - 25) / 80
            if event.type == "note_on":
                idx = -1
                # check if same sound is already playing
                for i in range(MAX_NOTES):
                    if playing[i] is None: continue

                    if playing[i][0] == sound:
                        playing[i][1].append(pair)
                        break
                else:
                    # it's not, find free channel
                    for i in range(MAX_NOTES):
                        if playing[i] is None:
                            playing[i] = [sound, [pair], 0]
                            idx = i
                            break
                    else:
                        # no free index. find sound used for longest and free its allocated index for usage
                        mx = 0
                        for i in range(MAX_NOTES):
                            if playing[i] is None: continue

                            if playing[i][2] > mx:
                                mx = playing[i][2]

                        for i in range(MAX_NOTES):
                            if playing[i] is None: continue

                            if playing[i][2] == mx:
                                idx = i
                                oldPlayingPairs = playing[i][1]
                                discarded += oldPlayingPairs
                                playing[i] = [sound, [pair], 0]
                                
                                # dictionary so each key is unique and same sound 
                                # doesn't cleaned up more than once. unlikely, but midi is weird
                                indices = {}
                                for p in oldPlayingPairs:
                                    indices[(p[0] + 1) * (p[1] + 1)] = p

                                for key in indices:
                                    methods[-1] += INDENT * 2 + f"Highlights.clearMark({key});\n"
                                    cnt += 1

                                break
                
                if idx != -1:
                    # make sound
                    methods[-1] += INDENT * 2 + f"a[{idx}] = (int)(l * {sound});\n"
                    methods[-1] += INDENT * 2 + f"Highlights.markArray({idx}, {idx});\n"
                    cnt += 2
            elif pair in discarded: 
                # if note to turn off was already discarded, ignore
                discarded.remove(pair)
            else:
                # look for note to turn off in playing indices and update dictionary
                for i in range(MAX_NOTES):
                    if playing[i] is None: continue

                    if pair in playing[i][1]:
                        playing[i][1].remove(pair)

                        if len(playing[i][1]) == 0:
                            # every instance of this same sound has turned off. disable highlight
                            playing[i] = None
                            methods[-1] += INDENT * 2 + f"Highlights.clearMark({i});\n"
                            cnt += 1

                        break

            # update time each note has been playing. needed for cleanup
            for i in range(MAX_NOTES):
                if playing[i] is None: continue
                playing[i][2] += event.time

            # delay
            if event.time != 0:
                # Thread.sleep guarantees more precise and consistent timings than ArrayV's Delays.sleep
                # at the cost of sound quality, because ArrayV will play multiple short notes instead of one long note.
                # overall, i've observed that Thread.sleep results in a better output
                methods[-1] += INDENT * 2 + f"Thread.sleep({round(event.time * 1000)});\n" 
                cnt += 1

            if cnt >= MAX_LINES:
                cnt = 0
                methods.append("")

        # code is split into methods cause java limits the amount of code in same method
        methodsCode = ""
        for i, method in enumerate(methods):
            methodsCode += INDENT + f"private void m{i}() throws Exception "
            methodsCode += "{\n" + method + INDENT + "}\n\n"

        code = ""
        for i in range(len(methods)):
            code += INDENT * 2 + f"m{i}();\n"

        with open("MusicSort.java", "w") as java:
            java.write(CODE.replace("CODE", code).replace("METHODS", methodsCode))

if __name__ == "__main__":
    if len(argv) == 1:
        print("ArrayV music tool - thatsOven")
    else:   
        ArrayVMusicTool().convert(argv[1])