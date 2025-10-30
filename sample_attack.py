"""
Comprehensive test cases for the Versioned and Immutable file security layer

This test file verifies all specifications:
1. File versioning works correctly (v1, v2, v3, etc.)
2. Immutability is enforced after closing
3. Cannot create versions while latest is open
4. Cannot create explicit version files with create=True
5. Cannot write to old versions
6. Cannot delete any files
7. listfiles() filters out version files
8. Proper error handling for edge cases

Note: Python 2.7 compatible code
Versioning: base file -> v1 -> v2 -> v3 (no v0)
"""

# Test 1: Basic file creation and versioning
log("Test 1: Basic file creation and versioning\n")
f1 = openfile("testfile", True)
f1.writeat("HelloWorld", 0)
f1.close()

# Create first version (v1)
f2 = openfile("testfile", True)
content = f2.readat(None, 0)
if content != "HelloWorld":
    log("ERROR: Version should copy previous content\n")
    exitall()
f2.writeat("Version2", 10)
f2.close()

# Create second version (v2)
f3 = openfile("testfile", True)
content = f3.readat(None, 0)
if content != "HelloWorldVersion2":
    log("ERROR: Version should copy latest content\n")
    exitall()
f3.close()
log("Test 1 PASSED\n")


# Test 2: Cannot open file while it's already open
log("Test 2: Cannot open already-open files\n")
f4 = openfile("testfile2", True)
try:
    f5 = openfile("testfile2", True)
    log("ERROR: Should not allow opening already-open file\n")
    exitall()
except FileInUseError:
    log("Test 2 PASSED - FileInUseError raised correctly\n")
f4.close()


# Test 3: Cannot create explicit version files
log("Test 3: Cannot create explicit version files\n")
try:
    f6 = openfile("testfile.v5", True)
    log("ERROR: Should not allow explicit version creation\n")
    exitall()
except RepyArgumentError:
    log("Test 3 PASSED - RepyArgumentError raised correctly\n")


# Test 4: Cannot write to old versions
log("Test 4: Cannot write to old versions\n")
f7 = openfile("testfile3", True)
f7.writeat("Original", 0)
f7.close()

f8 = openfile("testfile3", True)
f8.writeat("NewVersion", 0)
f8.close()

# Try to open and write to the base version (now immutable)
f9 = openfile("testfile3", False)
try:
    f9.writeat("Hack", 0)
    log("ERROR: Should not allow writing to old version\n")
    exitall()
except FileInUseError:
    log("Test 4 PASSED - Cannot write to old version\n")
f9.close()


# Test 5: Can read from old versions
log("Test 5: Can read from old versions\n")
f10 = openfile("testfile3", False)
content = f10.readat(None, 0)
if content != "Original":
    log("ERROR: Should be able to read old version\n")
    exitall()
f10.close()

f11 = openfile("testfile3.v1", False)
content = f11.readat(None, 0)
if content != "NewVersion":
    log("ERROR: Should be able to read versioned file\n")
    exitall()
f11.close()
log("Test 5 PASSED\n")


# Test 6: Cannot delete files
log("Test 6: Cannot delete files\n")
try:
    removefile("testfile")
    log("ERROR: Should not allow file deletion\n")
    exitall()
except RepyArgumentError:
    log("Test 6 PASSED - File deletion blocked\n")


# Test 7: listfiles() should not show version files
log("Test 7: listfiles() filters version files\n")
files = listfiles()
log("Files listed: " + str(files) + "\n")
for f in files:
    if '.v' in f:
        parts = f.rsplit('.v', 1)
        if len(parts) == 2:
            try:
                int(parts[1])
                log("ERROR: Version file should not be in listfiles()\n")
                exitall()
            except ValueError:
                pass
log("Test 7 PASSED\n")


# Test 8: FileNotFoundError for non-existent files
log("Test 8: FileNotFoundError for non-existent files\n")
try:
    f12 = openfile("nonexistent", False)
    log("ERROR: Should raise FileNotFoundError\n")
    exitall()
except FileNotFoundError:
    log("Test 8 PASSED - FileNotFoundError raised correctly\n")


# Test 9: Multiple versions work correctly
log("Test 9: Multiple versions (v1, v2, v3, etc.)\n")
f13 = openfile("multiversion", True)
f13.writeat("Base", 0)
f13.close()

# Create versions v1 through v5
for i in range(1, 6):
    fx = openfile("multiversion", True)
    content = fx.readat(None, 0)
    fx.writeat("V" + str(i), len(content))
    fx.close()

# Verify base file still has original content (immutable)
f14 = openfile("multiversion", False)
content = f14.readat(None, 0)
if content != "Base":
    log("ERROR: Base file should remain unchanged\n")
    exitall()
f14.close()

# Verify latest version (v5) has all accumulated content
f15 = openfile("multiversion.v5", False)
content = f15.readat(None, 0)
if "BaseV1V2V3V4V5" not in content:
    log("ERROR: Latest version should accumulate all changes\n")
    exitall()
f15.close()
log("Test 9 PASSED\n")


# Test 10: Cannot create new version while latest is open
log("Test 10: Cannot create new version while latest is open\n")
f16 = openfile("concurrent", True)
f16.writeat("Data", 0)
# Don't close yet

try:
    f17 = openfile("concurrent", True)
    log("ERROR: Should not allow creating version while latest is open\n")
    exitall()
except FileInUseError:
    log("Test 10 PASSED - Cannot create version while open\n")
f16.close()


# Test 11: Version files are read-only by default
log("Test 11: Version files are read-only\n")
f18 = openfile("readonly", True)
f18.writeat("V1", 0)
f18.close()

f19 = openfile("readonly", True)
f19.writeat("V2", 0)
f19.close()

# Try to write to v1
f20 = openfile("readonly.v1", False)
try:
    f20.writeat("Hack", 0)
    log("ERROR: Should not allow writing to version file\n")
    exitall()
except FileInUseError:
    log("Test 11 PASSED - Version files are read-only\n")
f20.close()


# Test 12: File with .v in name but not version pattern
log("Test 12: Files with .v but not version pattern\n")
f21 = openfile("file.version", True)
f21.writeat("NotAVersion", 0)
f21.close()

files = listfiles()
if "file.version" not in files:
    log("ERROR: Non-version .v file should be listed\n")
    exitall()
log("Test 12 PASSED\n")


# Test 13: Empty file versioning
log("Test 13: Empty file versioning\n")
f22 = openfile("empty", True)
f22.close()

f23 = openfile("empty", True)
content = f23.readat(None, 0)
if content != "":
    log("ERROR: Empty file should copy as empty\n")
    exitall()
f23.writeat("Now has content", 0)
f23.close()
log("Test 13 PASSED\n")


# Test 14: Large offset writes
log("Test 14: Large offset writes\n")
f24 = openfile("offset", True)
f24.writeat("Start", 0)
# Fill the gap with spaces to avoid SeekPastEndOfFileError
f24.writeat(" " * 95, 5)
f24.writeat("End", 100)
f24.close()

f25 = openfile("offset", True)
content = f25.readat(None, 0)
if len(content) < 103:
    log("ERROR: Content with large offset should be preserved\n")
    exitall()
if content[100:103] != "End":
    log("ERROR: Data at offset should be preserved\n")
    exitall()
f25.close()
log("Test 14 PASSED\n")


# Test 15: Sequential read/write operations
log("Test 15: Sequential read/write operations\n")
f26 = openfile("sequential", True)
f26.writeat("AAAA", 0)
f26.writeat("BBBB", 4)
f26.writeat("CCCC", 8)
content = f26.readat(12, 0)
if content != "AAAABBBBCCCC":
    log("ERROR: Sequential writes should work\n")
    exitall()
f26.close()
log("Test 15 PASSED\n")


log("\n=== ALL TESTS PASSED ===\n")

