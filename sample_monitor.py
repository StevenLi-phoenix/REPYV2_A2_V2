"""
This security layer handles the Versioned and Immutable functionality

Note:
    This security layer uses encasementlib.r2py, restrictions.default, repy.py and Python
    Also you need to give it an application to run.
    python repy.py restrictions.default encasementlib.r2py [security_layer].r2py [attack_program].r2py 
    
"""
TYPE = "type"
ARGS = "args"
RETURN = "return"
EXCP = "exceptions"
TARGET = "target"
FUNC = "func"  
OBJC = "objc"

# Global state tracking
open_files = {}  # Maps filename -> True if currently open
closed_files = {}  # Maps filename -> True if it has been closed (immutable)


class VMFile():
    def __init__(self, filename, create):
        self.filename = filename
        self.is_writable = False
        
        # Check if trying to explicitly create a versioned file
        if create and '.v' in filename:
            # Parse to see if it's a version pattern like "file.v1"
            parts = filename.rsplit('.v', 1)
            if len(parts) == 2:
                try:
                    int(parts[1])
                    raise RepyArgumentError("Cannot create explicit version files")
                except ValueError:
                    pass
        
        if create:
            # Check if file is already open
            if filename in open_files and open_files[filename]:
                raise FileInUseError("File is already open")
            
            # Find the latest version of this file
            base_name = filename
            all_files = listfiles()
            
            # Check if base file exists
            if base_name in all_files:
                # Find the highest version number
                highest_version = 0
                for f in all_files:
                    if f.startswith(base_name + '.v'):
                        version_str = f[len(base_name) + 2:]
                        try:
                            version_num = int(version_str)
                            if version_num > highest_version:
                                highest_version = version_num
                        except ValueError:
                            pass
                
                # Determine the name of the latest version
                if highest_version > 0:
                    latest_file = base_name + '.v' + str(highest_version)
                else:
                    latest_file = base_name
                
                # Check if latest version is open
                if latest_file in open_files and open_files[latest_file]:
                    raise FileInUseError("File is already open")
                
                # Read content from latest version
                prev_file = openfile(latest_file, False)
                content = prev_file.readat(None, 0)
                prev_file.close()
                
                # Create new version
                new_version = highest_version + 1
                new_name = base_name + '.v' + str(new_version)
                self.VMfile = openfile(new_name, True)
                self.VMfile.writeat(content, 0)
                self.actual_filename = new_name
                self.is_writable = True
            else:
                # File doesn't exist, create base file
                self.VMfile = openfile(base_name, True)
                self.actual_filename = base_name
                self.is_writable = True
            
            # Mark as open
            open_files[filename] = True
            open_files[self.actual_filename] = True
            
        else:
            # Opening existing file for reading
            if filename not in listfiles():
                raise FileNotFoundError("File not found")
            
            # Check if file is already open
            if filename in open_files and open_files[filename]:
                raise FileInUseError("File is already open")
            
            self.VMfile = openfile(filename, False)
            self.actual_filename = filename
            
            # Check if this is an old version (closed file) - only allow reading
            if filename in closed_files and closed_files[filename]:
                self.is_writable = False
            else:
                # Check if it's a version file
                if '.v' in filename:
                    parts = filename.rsplit('.v', 1)
                    if len(parts) == 2:
                        try:
                            int(parts[1])
                            # It's a version file, mark as read-only
                            self.is_writable = False
                        except ValueError:
                            pass
                else:
                    # Base file that hasn't been closed yet
                    self.is_writable = True
            
            # Mark as open
            open_files[filename] = True

    def readat(self, num_bytes, offset):
        return self.VMfile.readat(num_bytes, offset)

    def writeat(self, data, offset):
        # Check if writing is allowed
        if not self.is_writable:
            raise FileInUseError("Cannot write to an old version")
        return self.VMfile.writeat(data, offset)

    def close(self):
        result = self.VMfile.close()
        
        # Mark file as closed (immutable)
        closed_files[self.actual_filename] = True
        if self.filename != self.actual_filename:
            closed_files[self.filename] = True
        
        # Mark as no longer open
        if self.filename in open_files:
            open_files[self.filename] = False
        if self.actual_filename in open_files:
            open_files[self.actual_filename] = False
        
        return result


def LPopenfile(filename, create):
    return VMFile(filename, create)

def LPremovefile(filename):
    # File deletion is not allowed for any file
    raise RepyArgumentError("File removal is not allowed")

def LPlistfiles():
    # Filter out versioned files from the listing
    all_files = listfiles()
    base_files = []
    
    for filename in all_files:
        # Check if this is a versioned file (e.g., "file.v1")
        if '.v' in filename:
            parts = filename.rsplit('.v', 1)
            if len(parts) == 2:
                try:
                    int(parts[1])
                    # It's a version file, skip it
                    continue
                except ValueError:
                    # Not a version pattern, include it
                    pass
        base_files.append(filename)
    
    return base_files

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