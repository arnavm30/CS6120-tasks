from random import seed, randint
import subprocess
import sys

seed(42)

for i in range(500):
  x = randint(-3e9, 3e9)
  y = randint(-3e9, 3e9)
  python_res = x*y

  f = open('./karatsuba.bril')
  first_line, remainder = f.readline(), f.read()
  t = open('./karatsuba.bril',"w")
  t.write(f'# ARGS: {x} {y}' + "\n")
  t.write(remainder)
  t.close()

  bril_res = int(
    subprocess.check_output(f'bril2json < ./karatsuba.bril | brili {x} {y}', shell=True).strip()
    )
  
  print(f'{python_res=}, {bril_res=}')
  assert python_res == bril_res, f'ASSERTION ERROR: {python_res=}, {bril_res=}'