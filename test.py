import  json
strg = {"message": 'hello',}
strg = json.dumps(strg)
print(strg)
strg = json.loads(strg)
print(strg)
print(strg['message'])