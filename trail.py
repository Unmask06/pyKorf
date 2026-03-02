KORF_FILE = r"pykorf/trail_files/Cooling Water Circuit-EES-IT-LT-00141.kdf"
from pykorf import Model

model = Model(KORF_FILE)

# model.to_excel("Cooling Water Circuit-EES-IT-LT-00141.xlsx")

model.from_excel("Cooling Water Circuit-EES-IT-LT-00141.xlsx")

model.save()