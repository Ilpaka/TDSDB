# Слайд 11 «Измеряйте нужную операцию»: два фрагмента из презентации
# (boundary_with_setup.py и boundary_search_only.py), собранные в одну программу.
from time import perf_counter

# Создание списка + поиск
start = perf_counter()
numbers = list(range(1_000_000))
result = -1 in numbers
elapsed = perf_counter() - start
print(f"setup + search: {elapsed:.6f} sec")

# Только поиск
numbers = list(range(1_000_000))
start = perf_counter()
result = -1 in numbers
elapsed = perf_counter() - start
print(f"search only:    {elapsed:.6f} sec")
