with open('./game-state.txt', 'r') as f:
    polygons = f.readline().split()
    camera = f.readline().split()
    f.close()

for p in polygons:
    for point in p:
        print(str(p[0]) + "," + str(p[1]))
print()
print(str(camera[0]))