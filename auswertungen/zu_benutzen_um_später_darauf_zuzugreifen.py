import os
import sys
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

# --- Import your Person class (ensure it handles 'age' property correctly) ---
# Assuming Person.Personenklasse.Person has a property or method to calculate age
from auswertungen.hierdateiname import zuimportierendes


