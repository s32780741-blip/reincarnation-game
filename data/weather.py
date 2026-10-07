{
  "weathers": [
    {"id":"clear","name":"Clear","icon":"☀","desc":"Langit cerah. Perjalanan lancar.","encounter_mult":1.0,"gather_mult":1.0,"mining_mult":1.0,"fire_mult":1.0,"water_mult":1.0,"color":"yellow"},
    {"id":"cloudy","name":"Cloudy","icon":"☁","desc":"Berawan. Suasana tenang.","encounter_mult":0.9,"gather_mult":1.1,"mining_mult":1.0,"fire_mult":1.0,"water_mult":1.0,"color":"gray"},
    {"id":"rain","name":"Rain","icon":"☂","desc":"Hujan turun. Beberapa monster suka.","encounter_mult":1.1,"gather_mult":1.3,"mining_mult":0.7,"fire_mult":0.6,"water_mult":1.3,"color":"blue"},
    {"id":"storm","name":"Storm","icon":"⚡","desc":"Badai! Perjalanan berbahaya.","encounter_mult":1.5,"gather_mult":0.6,"mining_mult":0.5,"fire_mult":0.5,"water_mult":1.5,"lightning_mult":1.5,"color":"cyan"},
    {"id":"snow","name":"Snow","icon":"❄","desc":"Salju turun. Dingin menusuk.","encounter_mult":1.1,"gather_mult":0.6,"mining_mult":0.8,"fire_mult":0.7,"ice_mult":1.5,"color":"white"},
    {"id":"fog","name":"Fog","icon":"🌫","desc":"Kabut tebal. Visibility rendah.","encounter_mult":1.3,"gather_mult":0.9,"mining_mult":0.9,"color":"gray"},
    {"id":"heatwave","name":"Heatwave","icon":"🔥","desc":"Panas ekstrem. Stamina terkuras.","encounter_mult":1.0,"gather_mult":0.7,"mining_mult":0.9,"fire_mult":1.5,"ice_mult":0.5,"stamina_mult":1.3,"color":"red"},
    {"id":"sandstorm","name":"Sandstorm","icon":"🌪","desc":"Badai pasir. Berbahaya.","encounter_mult":1.4,"gather_mult":0.5,"mining_mult":0.6,"wind_mult":1.5,"color":"yellow"},
    {"id":"mist","name":"Mystic Mist","icon":"☁","desc":"Kabut mistis. Sihir menguat.","encounter_mult":1.2,"gather_mult":1.0,"mining_mult":1.0,"magic_mult":1.3,"color":"magenta"},
    {"id":"bloodmoon","name":"Blood Moon","icon":"🌑","desc":"Bulan darah. Monster sangat kuat!","encounter_mult":2.0,"monster_level_bonus":10,"monster_hp_mult":1.5,"drop_mult":2.0,"color":"red"}
  ],
  "biome_weather": {
    "plains": ["clear","clear","cloudy","rain","fog"],
    "road": ["clear","cloudy","rain","fog"],
    "forest": ["clear","cloudy","rain","fog","mist"],
    "lake": ["clear","cloudy","rain","fog"],
    "cave": ["fog","clear"],
    "mountain": ["clear","cloudy","snow","storm","fog"],
    "snow": ["snow","snow","storm","fog","clear"],
    "swamp": ["fog","rain","mist","cloudy"],
    "ruins": ["fog","cloudy","mist","clear"],
    "underground": ["fog","mist"],
    "desert": ["clear","heatwave","sandstorm","clear"],
    "sea": ["clear","cloudy","rain","storm"],
    "wilderness": ["clear","cloudy","fog","rain","storm","mist"]
  }
}
