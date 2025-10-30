"""
This is an INTENTIONALLY FLAWED security layer for testing purposes.
It demonstrates common mistakes and specification violations.

DO NOT USE THIS AS A REFERENCE - This is for testing error detection only.

Flaws included:
1. Does not track open files properly
2. Allows writing to old versions
3. Does not prevent file deletion
4. Shows version files in listfiles()
5. Does not properly handle version numbering
6. Allows explicit version file creation
"""
TYPE = "type"
ARGS = "args"
RETURN = "return"
EXCP = "exceptions"
TARGET = "target"
FUNC = "func"  
OBJC = "objc"


class VMFile():
    def __init__(self, filename, create):
        self.filename = filename
        
        if create:
            # FLAW 1: Does not check if file is already open
            # FLAW 2: Only creates v1, doesn't handle v2, v3, etc.
            if filename in listfiles():
                prev_file = openfile(filename, False)
                content = prev_file.readat(None, 0)
                prev_file.close()
                
                # Always creates .v1 regardless of existing versions
                new_name = filename + ".v1"
                self.VMfile = openfile(new_name, True)
                self.VMfile.writeat(content, 0)
            else:
                self.VMfile = openfile(filename, True)
        else:
            # FLAW 3: Does not check if file exists before opening
            self.VMfile = openfile(filename, False)

    def readat(self, num_bytes, offset):
        return self.VMfile.readat(num_bytes, offset)

    def writeat(self, data, offset):
        # FLAW 4: Allows writing to any file, including old versions
        return self.VMfile.writeat(data, offset)

    def close(self):
        # FLAW 5: Does not track closed files for immutability
        return self.VMfile.close()


def LPopenfile(filename, create):
    # FLAW 6: Allows explicit version file creation
    return VMFile(filename, create)

def LPremovefile(filename):
    # FLAW 7: Allows file deletion
    removefile(filename)

def LPlistfiles():
    # FLAW 8: Shows all files including version files
    return listfiles()


# The code below sets up type checking and variable hiding for you.
# You should not change anything below this point.
sec_file_def = {
    "obj-type": VMFile,
    "name": "VMFile",
    "writeat": {"type": "func", "args": (str, (int, long)), "exceptions": Exception, "return": (int, type(None)), "target": VMFile.writeat},
    "readat": {"type": "func", "args": ((int, long, type(None)), (int, long)), "exceptions": Exception, "return": str, "target": VMFile.readat},
    "close": {"type": "func", "args": None, "exceptions": Exception, "return": (bool, type(None)), "target": VMFile.close}
}

CHILD_CONTEXT_DEF["openfile"] = {
    TYPE: OBJC,
    ARGS: (str, bool),
    EXCP: Exception,
    RETURN: sec_file_def,
    TARGET: LPopenfile
}

CHILD_CONTEXT_DEF["removefile"] = {
    TYPE: FUNC,
    ARGS: (str,),
    EXCP: Exception,
    RETURN: type(None),
    TARGET: LPremovefile
}

CHILD_CONTEXT_DEF["listfiles"] = {
    TYPE: FUNC,
    ARGS: None,
    EXCP: Exception,
    RETURN: list,
    TARGET: LPlistfiles
}

# Execute the user code
secure_dispatch_module()

