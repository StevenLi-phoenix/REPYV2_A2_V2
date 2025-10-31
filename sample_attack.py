# def yes(data, offset):
#     log("defence penetrated")

f1 = openfile("testfile1", True)
f1.writeat("HelloWorld", 0)
# f1.readat = yes
log(f1.filename)
f1.readat(10, 0)
log(f1.filename)
f1.filename = "retrieved!!!"
log(f1.filename)
f1.close()

