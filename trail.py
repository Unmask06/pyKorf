KORF_FILE = r"pykorf/trail_files/Cooling Water Circuit-EES-IT-LT-00141.kdf"
from pykorf import Model

model = Model(KORF_FILE)
model.set_params(ename="L5", params={"NAME": ["L5"]})
model.save()
