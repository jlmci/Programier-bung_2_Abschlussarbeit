from tinydb import TinyDB, Query

db = TinyDB('dbtests.json')
df = TinyDB('dbperson.json')

data = db.get(doc_ids = "1")
print(data)

#genaue Ausgabe
datagenau = data[0]["date"]
#print(datagenau)

#update werte
#db.update({"date": "2023-10-01"}, Query().id == 1)


#neuer Parameter
db.update({'sportart': 'skifahren'}, doc_ids=[3])


#update testliste
#update_liste = df.search(Query().id == 1)[0]["ekg_tests"]
#update_liste.append(6)
#df.update({"ekg_tests": update_liste}, doc_ids=[1])



