import os
import sys


class DataBlock:
    class error:
        class FileError(Exception): pass
    def __init__(self, filename: str):
        if os.path.exists(filename) and os.path.isfile(filename):
            self.file = filename
        else:
            raise DataBlock.error.FileError("the file provided doesn't exist")
    
    def format(self):
        with open(self.file, "wb") as file:
            file.write(b"")
    
    def _createFilePointer(self, deltaFilename: str, address: int = 0x0, end: int = 0x1E) -> bytes:
        """Returns a file pointer that can be used to access a file's content.
        The code `0x1E` (the default) is `Record Separator` or `RS` (it means there are more pointers after this one) but you can also put `0x02` "`Start of Text` or `SOH`" if this is the last pointer. Example:
        ```py3
        _makeFilePointer(self, "hello.txt", 0xDEADC0DE, 0x02)
        ```"""
        return bytearray(bytes(deltaFilename[0:27], "utf-8") + (b"\x00" * (27 - len(deltaFilename))) + address.to_bytes(4, "big") + end.to_bytes(1, "big"))
    
    def _splitPointersAndText(self, data: bytes) -> tuple[list[bytes], bytes]:
        """Splits the pointer and the text section apart, then it divides the individual pointers and finally it returns the result."""
        sections = data.split(b"\x02", 1)
        sections[0] += b"\x02"
        sections[0] = sections[0].split(b"\x1E")
        i = 0
        for i in range(len(sections[0][:-1])):
            sections[0][i] += b"\x1E"
        return (sections[0], sections[1])

    def createFile(self, deltaFilename: str, content: str):
        """Creates a file in the virtual Delta Filesystem. `deltaFilename` must not be longer than 27 characters."""
        with open(self.file, "rb") as file:
            fs = file.read()
            oldfs = fs
        with open(self.file, "wb") as file:
            parts = [[], 0]
            if len(fs) != 0:
                parts = self._splitPointersAndText(fs)
                for pt in parts[0]:
                    buf = pt[:-1] + b"\x1E"
                    file.write(buf)
            file.write(self._createFilePointer(deltaFilename, len(fs) - (0x20 * len(parts[0])), 0x02))
            if len(fs) != 0: file.write(parts[1])
            file.write(bytes(content, "utf8") + b"\x1C") # 0x1C = File Separator FS

    def _getFilePointer(self, deltaFilename: str) -> tuple[bytes]:
        with open(self.file, "rb") as file:
            fs = file.read()
            if len(fs) == 0:
                raise DataBlock.error.FileError("this block is empty")
            parts = self._splitPointersAndText(fs)
            deltaFilename += "\x00" * 27
            for pt in parts[0]:
                if pt[0:27] == bytes(deltaFilename[0:27], "utf-8"):
                    print("found")
                    return (pt, parts[1])
                print("not found")
                raise DataBlock.error.FileError("the specified file doesn't exist")
    def getFileContents(self, deltaFilename: str) -> str:
        data = self._getFilePointer(deltaFilename)
        return str(data[1][int.from_bytes(data[0][0x1B:0x1F], "big"):].split(b"\x1C")[0], "utf-8")