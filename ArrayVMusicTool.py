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

# install the patch for more accurate timings overall and better sounds with this program
ARRAYV_PATCH = False 
# if you use ArrayV 4.0
ARRAYV_4_0 = False
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

class MidiEvent:
    def __init__(self, type, note, channel, sleep):
        self.type    = type
        self.note    = note
        self.channel = channel
        self.time    = sleep

    def __repr__(self):
        return "[" + str(self.channel) + "] " + self.type + " " + str(self.note) + " sleep: " + str(self.time)

class ArrayVEvent:
    def __init__(self, type, value, index = None):
        self.type  = type
        self.value = value
        self.index = index

    def compile(self):
        match self.type:
            case "mark":
                return INDENT * 2 + f"a[{self.index}] = (int)(l * {self.value});\n" + \
                       INDENT * 2 + f"Highlights.markArray({self.index}, {self.index});\n", 2
            case "clear":
                return INDENT * 2 + f"Highlights.clearMark({self.value});\n", 1
            case "wait":
                if ARRAYV_PATCH:
                    return INDENT * 2 + f"Delays.sleep({round(self.value * 1000, 4)});\n", 1
                else:
                    return INDENT * 2 + f"Thread.sleep({round(self.value * 1000)});\n", 1 

class ArrayVMusicTool:
    def readMidi(self, fileName):
        mid = MidiFile(fileName)

        events = []
        for message in mid:
            if message.type in ("note_on", "note_off"):
                if message.type == "note_on" and message.velocity == 0:
                    type_ = "note_off"
                else: type_ = message.type

                events.append(MidiEvent(
                    type_, message.note, 
                    message.channel, message.time
                ))
            elif message.type == "end_of_track":
                events.append(MidiEvent("", 0, 0, message.time))
                break
            elif len(events) != 0:
                events[-1].time += message.time

        for i in range(len(events) - 1):
            events[i].time = events[i + 1].time
        events.pop(-1)

        return events
    
    def mergeDelays(self, events):
        tmp = []
        i = 0
        while i < len(events):
            while i < len(events) and events[i].type != "wait": 
                tmp.append(events[i])
                i += 1

            time = 0
            while i < len(events) and events[i].type == "wait":
                time += events[i].value
                i += 1

            if time != 0:
                tmp.append(ArrayVEvent("wait", time))
            
        return tmp

    def convert(self, fileName):
        events    = []
        playing   = {}
        discarded = []

        for i in range(MAX_NOTES):
            playing[i] = None

        for event in self.readMidi(fileName):
            print(event)

            pair  = (event.note, event.channel)
            sound = (event.note - 25) / 80
            if event.type == "note_on":
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

                            if playing[i][2] > playing[mx][2]:
                                mx = i

                        idx = mx
                        oldPlayingPairs = playing[mx][1]
                        discarded += oldPlayingPairs
                        playing[mx] = [sound, [pair], 0]
                            
                    events.append(ArrayVEvent("mark", sound, idx))
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
                            events.append(ArrayVEvent("clear", i))

                        break

            # update time each note has been playing. needed for cleanup
            for i in range(MAX_NOTES):
                if playing[i] is None: continue
                playing[i][2] += event.time

            # delay
            if event.time != 0: events.append(ArrayVEvent("wait", event.time))

        # merge delays for better quality sound and more compact output
        events = self.mergeDelays(events)

        # code is split into methods cause java limits the amount of code in same method
        methodsCode = INDENT + "private void m0() " + ("" if ARRAYV_PATCH else "throws Exception ") + "{\n"
        cnt = 0
        mId = 1
        for event in events:
            closed = False
            t0, t1 = event.compile()
            methodsCode += t0
            cnt         += t1

            if cnt >= MAX_LINES:
                methodsCode += INDENT + "}\n\n" + INDENT + "private void " + f"m{mId}() " + ("" if ARRAYV_PATCH else "throws Exception ") + "{\n"
                closed = True
                mId += 1
                cnt = 0

        if not closed: methodsCode += INDENT + "}\n\n"

        code = ""
        for i in range(mId):
            code += INDENT * 2 + f"m{i}();\n"

        with open("MusicSort.java", "w") as java:
            res = CODE.replace("CODE", code).replace("METHODS", methodsCode)
            if ARRAYV_4_0: res.replace("io.github.arrayv.", "")
            java.write(res)

if __name__ == "__main__":
    if len(argv) == 1:
        print("ArrayV music tool - thatsOven")
    else:   
        if "--patched" in argv:
            argv.remove("--patched")
            ARRAYV_PATCH = True

        if "--v4" in argv:
            argv.remove("--v4")
            ARRAYV_4_0 = True

        ArrayVMusicTool().convert(argv[1])
