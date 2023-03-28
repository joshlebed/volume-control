c = (NameError, TypeError)
try:
    name = 'Bob'
    name += 5
except c as error:
    print(error)
