"""
Attack test cases designed to expose flaws in the incorrect monitor.

These attacks should FAIL on the correct monitor (sample_monitor.py)
but SUCCEED on the incorrect monitor (sample_incorrect_monitor.py)
"""

log("=== Testing Incorrect Monitor - These attacks should succeed ===\n\n")

# Attack 1: Open file twice (should fail on correct monitor)
log("Attack 1: Opening already-open file\n")
f1 = openfile("attack1", True)
f1.writeat("Data", 0)
try:
    f2 = openfile("attack1", True)
    log("SUCCESS - Incorrect monitor allows opening already-open file (SECURITY FLAW)\n")
    f2.close()
except FileInUseError:
    log("BLOCKED - Correct monitor prevents this\n")
f1.close()


# Attack 2: Write to old version (should fail on correct monitor)
log("\nAttack 2: Writing to old version\n")
f3 = openfile("attack2", True)
f3.writeat("Original", 0)
f3.close()

f4 = openfile("attack2", True)
f4.writeat("Version2", 0)
f4.close()

# Try to modify the old version
f5 = openfile("attack2", False)
try:
    f5.writeat("HACKED", 0)
    log("SUCCESS - Incorrect monitor allows writing to old version (IMMUTABILITY BROKEN)\n")
except FileInUseError:
    log("BLOCKED - Correct monitor prevents this\n")
f5.close()


# Attack 3: Delete file (should fail on correct monitor)
log("\nAttack 3: Deleting file\n")
f6 = openfile("attack3", True)
f6.writeat("Delete me", 0)
f6.close()

try:
    removefile("attack3")
    log("SUCCESS - Incorrect monitor allows file deletion (AUDIT TRAIL DESTROYED)\n")
except RepyArgumentError:
    log("BLOCKED - Correct monitor prevents this\n")


# Attack 4: Version files visible in listfiles (should be hidden on correct monitor)
log("\nAttack 4: Version files in listfiles()\n")
f7 = openfile("attack4", True)
f7.writeat("V0", 0)
f7.close()

f8 = openfile("attack4", True)
f8.writeat("V1", 0)
f8.close()

files = listfiles()
version_found = False
for fname in files:
    if '.v' in fname and fname.startswith("attack4.v"):
        try:
            int(fname.split('.v')[1])
            version_found = True
            break
        except:
            pass

if version_found:
    log("SUCCESS - Incorrect monitor exposes version files (INFORMATION LEAK)\n")
else:
    log("BLOCKED - Correct monitor hides version files\n")


# Attack 5: Create explicit version file (should fail on correct monitor)
log("\nAttack 5: Creating explicit version file\n")
try:
    f9 = openfile("attack5.v99", True)
    f9.writeat("Fake version", 0)
    f9.close()
    log("SUCCESS - Incorrect monitor allows explicit version creation (VERSION CONFUSION)\n")
except RepyArgumentError:
    log("BLOCKED - Correct monitor prevents this\n")


# Attack 6: Multiple versions beyond v1 (incorrect monitor only handles v1)
log("\nAttack 6: Creating multiple versions (v2, v3, etc.)\n")
f10 = openfile("attack6", True)
f10.writeat("V0", 0)
f10.close()

f11 = openfile("attack6", True)
f11.close()

# Incorrect monitor will overwrite attack6.v1 instead of creating attack6.v2
f12 = openfile("attack6", True)
f12.close()

try:
    # Check if v2 exists (correct monitor should create it)
    f13 = openfile("attack6.v2", False)
    f13.close()
    log("BLOCKED - Correct monitor creates v2\n")
except FileNotFoundError:
    log("SUCCESS - Incorrect monitor fails to create v2 (VERSION TRACKING BROKEN)\n")


# Attack 7: Race condition with version creation
log("\nAttack 7: Creating version while latest is open\n")
f14 = openfile("attack7", True)
f14.writeat("Base", 0)
# Don't close yet

try:
    # Try to create another version while base is still open
    f15 = openfile("attack7", True)
    log("SUCCESS - Incorrect monitor allows version creation while file is open (RACE CONDITION)\n")
    f15.close()
except FileInUseError:
    log("BLOCKED - Correct monitor prevents this\n")
f14.close()


# Attack 8: Tamper with version file directly
log("\nAttack 8: Tampering with version file\n")
f16 = openfile("attack8", True)
f16.writeat("Original content", 0)
f16.close()

f17 = openfile("attack8", True)
f17.writeat("New version", 0)
f17.close()

# Try to open and modify the version file
try:
    f18 = openfile("attack8.v1", False)
    f18.writeat("TAMPERED", 0)
    log("SUCCESS - Incorrect monitor allows tampering with version files (HISTORY REWRITE)\n")
    f18.close()
except FileInUseError:
    log("BLOCKED - Correct monitor prevents this\n")


# Attack 9: Open non-existent file without proper error
log("\nAttack 9: Opening non-existent file with create=False\n")
try:
    f19 = openfile("doesnotexist", False)
    log("SUCCESS - Incorrect monitor has poor error handling (CONFUSION)\n")
    f19.close()
except:
    log("BLOCKED - Correct monitor raises FileNotFoundError\n")


log("\n=== Attack Testing Complete ===\n")
log("The more 'SUCCESS' messages above, the more flawed the monitor is.\n")
log("A correct monitor should BLOCK all these attacks.\n")

