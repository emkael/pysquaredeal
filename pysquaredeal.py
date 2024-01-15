import sys

from squaredeal import SquareDeal


sd = SquareDeal()
sd.fromfile(sys.argv[1], encoding=sys.argv[2] if len(sys.argv) > 2 else 'utf-8')
print(sd.__dict__)
for phase in sd.phases:
    print(phase.__dict__)
