import json

with open('main/temp_voices/icons.json', 'r', encoding='utf-8') as f:
    icons = json.load(f)

color = 'orange-yellow' # пока доступно только orange-yellow

arrowup = icons[color][0]
arrowdown = icons[color][1]
show = icons[color][2]
unlock = icons[color][3]
voice = icons[color][4]
login = icons[color][5]
limit = icons[color][6]
edit = icons[color][7]
star = icons[color][8]
settings = icons[color][9]
filter = icons[color][10]
clock = icons[color][11]
folder = icons[color][12]