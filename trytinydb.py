from tinydb import TinyDB, Query

db = TinyDB('db.json')

db.insert({
		"id": 4,
		"date": "11.3.2023",
		"result_link": "data/ekg_data/03_Ruhe.txt"
	})


