from datetime import datetime, date

DEFAULT_CHARACTER = {
    "name": "", "real_name": "", "gender": "", "age": 0,
    "weight": 0, "height": 0, "body_type": "", "goal": "",
    "activity_level": "low",
    "level": 1, "xp": 0, "coins": 0,
    "energy": 50, "strength": 10, "intellect": 10, "mood": 50,
    "inventory": [],
    "today": "", "calories_today": 0, "protein_today": 0,
    "fat_today": 0, "carbs_today": 0,
    "meals_today": 0, "workouts_today": 0, "rests_today": 0,
    "total_meals": 0, "total_workouts": 0, "total_rests": 0,
    "healthy_meals": 0, "junk_meals": 0,
    "measurements": {}, "measurements_history": [],
    "last_measurement_date": "", "food_log_today": [],
    "created_at": "", "last_action": "",
}

XP_PER_LEVEL = 100

def _clamp(v, lo=0, hi=100): return max(lo, min(hi, v))
def today_str(): return date.today().isoformat()

def reset_daily_if_needed(char):
    if char.get("today") != today_str():
        char.update({
            "today": today_str(), "calories_today": 0,
            "protein_today": 0, "fat_today": 0, "carbs_today": 0,
            "meals_today": 0, "workouts_today": 0, "rests_today": 0,
            "food_log_today": [], "activity_level": "low",
        })
    return char

ACTIVITY_COEFF = {"low":1.2,"light":1.375,"medium":1.55,"high":1.725}
GOAL_COEFF     = {"lose":0.85,"maintain":1.0,"gain":1.15}

def calculate_daily_kbzhu(char):
    w,h,a,g = char.get("weight",70), char.get("height",170), char.get("age",25), char.get("gender","female")
    bmr = (10*w + 6.25*h - 5*a + 5) if g=="male" else (10*w + 6.25*h - 5*a - 161)
    tdee = bmr * ACTIVITY_COEFF.get(char.get("activity_level","low"), 1.2)
    cal  = tdee * GOAL_COEFF.get(char.get("goal","maintain"), 1.0)
    prot = w * 1.8
    fat  = max(60, w * 0.8)
    carb = max(50, (cal - prot*4 - fat*9) / 4)
    return {"calories":round(cal),"protein":round(prot),"fat":round(fat),"carbs":round(carb)}

def calculate_bmi(char):
    h = char.get("height",170)/100
    return round(char.get("weight",70)/(h*h),1)

def bmi_category(bmi):
    if bmi<18.5: return "Дефицит веса"
    if bmi<25:   return "Норма ✅"
    if bmi<30:   return "Избыточный вес"
    return "Ожирение"

def get_avatar(char):
    g,bt,lv = char.get("gender","female"), char.get("body_type","normal"), char.get("level",1)
    if lv>=15: return "🦸‍♀️" if g=="female" else "🦸‍♂️"
    if lv>=10: return "💃"  if g=="female" else "🕺"
    if lv>=5:  return "🏃‍♀️" if g=="female" else "🏃‍♂️"
    avatars = {
        ("female","slim"):"🧘‍♀️",("female","normal"):"👩",
        ("female","thick"):"👩‍🦱",("female","heavy"):"👩‍🦳",
        ("male","slim"):"🧘‍♂️",("male","normal"):"👨",
        ("male","thick"):"👨‍🦱",("male","heavy"):"👨‍🦳",
    }
    return avatars.get((g,bt),"🧑")

def level_title(level):
    for t,title in [(20,"⚡ Бог Симуляции"),(15,"🏆 Легенда"),(10,"🔥 Машина"),(7,"💪 Атлет"),(4,"🐣 Начинающий"),(1,"🥚 Новичок")]:
        if level>=t: return title
    return "🥚 Новичок"

def add_food(char, food_name, kcal, protein, fat, carbs):
    char = reset_daily_if_needed(char)
    char["calories_today"] += kcal
    char["protein_today"]  += protein
    char["fat_today"]      += fat
    char["carbs_today"]    += carbs
    char["meals_today"]    += 1
    char["total_meals"]    += 1
    char.setdefault("food_log_today",[]).append({
        "name":food_name,"kcal":kcal,"p":protein,"f":fat,"c":carbs,
        "time":datetime.now().strftime("%H:%M")
    })
    norm = calculate_daily_kbzhu(char)
    ratio = char["calories_today"] / max(norm["calories"],1)
    if ratio <= 1.1:
        char["energy"]=_clamp(char["energy"]+15); char["mood"]=_clamp(char["mood"]+5)
        char["xp"]+=25; char["coins"]+=5; char["healthy_meals"]=char.get("healthy_meals",0)+1
    else:
        char["energy"]=_clamp(char["energy"]+5); char["mood"]=_clamp(char["mood"]-5)
        char["xp"]+=10; char["junk_meals"]=char.get("junk_meals",0)+1
    char["last_action"]=datetime.now().isoformat()
    return _check_level_up(char)

def do_workout(char, workout_type, intensity, duration_min):
    char = reset_daily_if_needed(char)
    k = {"light":1,"medium":2,"hard":3}.get(intensity,1)
    xp_g=30*k+duration_min//5; coin_g=10*k
    char["strength"]=_clamp(char["strength"]+5*k)
    char["energy"]=_clamp(char["energy"]-10*k)
    char["mood"]=_clamp(char["mood"]+10)
    char["xp"]+=xp_g; char["coins"]+=coin_g
    char["workouts_today"]+=1; char["total_workouts"]+=1
    if char["workouts_today"]>=2: char["activity_level"]="high"
    elif intensity=="hard": char["activity_level"]="medium"
    else: char["activity_level"]="light"
    char["last_action"]=datetime.now().isoformat()
    return _check_level_up(char), xp_g, coin_g

def do_rest(char, rest_type, hours=0):
    char = reset_daily_if_needed(char)
    effects = {
        "sleep":    {"energy":35,"mood":15,"intellect":3,"xp":15,"coins":5},
        "book":     {"energy":10,"mood":10,"intellect":10,"xp":20,"coins":8},
        "phone":    {"energy":5,"mood":5,"intellect":-5,"xp":5,"coins":2},
        "activity": {"energy":20,"mood":20,"intellect":5,"xp":25,"coins":10},
    }
    e = effects.get(rest_type, effects["activity"])
    if rest_type=="sleep" and 7<=hours<=9:
        e = {k:int(v*1.3) for k,v in e.items()}
    char["energy"]=_clamp(char["energy"]+e["energy"])
    char["mood"]=_clamp(char["mood"]+e["mood"])
    char["intellect"]=_clamp(char["intellect"]+e["intellect"])
    char["xp"]+=e["xp"]; char["coins"]+=e["coins"]
    char["rests_today"]=char.get("rests_today",0)+1
    char["total_rests"]=char.get("total_rests",0)+1
    char["last_action"]=datetime.now().isoformat()
    return _check_level_up(char)

def save_measurements(char, data):
    char["measurements"]=data
    char["last_measurement_date"]=today_str()
    char.setdefault("measurements_history",[]).append({"date":today_str(),**data})
    char["xp"]+=30; char["coins"]+=15
    return _check_level_up(char)

def _check_level_up(char):
    prev=char["level"]
    while char["xp"]>=char["level"]*XP_PER_LEVEL:
        char["xp"]-=char["level"]*XP_PER_LEVEL; char["level"]+=1
        char["energy"]=_clamp(char["energy"]+20)
        char["mood"]=_clamp(char["mood"]+20)
        char["intellect"]=_clamp(char["intellect"]+5)
        char["coins"]+=50
    char["_leveled_up"]=char["level"]>prev
    return char

SHOP_ITEMS = {
    "protein":  {"name":"🥤 Протеин",    "price":50,"desc":"+20% к росту силы"},
    "sneakers": {"name":"👟 Кроссовки",  "price":80,"desc":"+15% XP за тренировки"},
    "vitamins": {"name":"💊 Витамины",   "price":40,"desc":"+5 энергии каждый день"},
    "outfit":   {"name":"👕 Спортформа", "price":60,"desc":"+10 настроения"},
    "shaker":   {"name":"🧴 Шейкер",    "price":30,"desc":"+5 монет за каждую еду"},
    "band":     {"name":"🏋️ Резинки",   "price":45,"desc":"+10% XP за лёгкие тренировки"},
}

def buy_item(char, item_key):
    item=SHOP_ITEMS.get(item_key)
    if not item: return False,"Товар не найден"
    if item_key in char.get("inventory",[]): return False,"У тебя уже есть этот предмет!"
    if char.get("coins",0)<item["price"]: return False,f"Не хватает монет! Нужно {item['price']} 🪙"
    char["coins"]-=item["price"]
    char.setdefault("inventory",[]).append(item_key)
    return True,f"Куплено: {item['name']}!"

def stat_bar(value,total=100,length=10):
    filled=round(value/total*length)
    return "█"*filled+"░"*(length-filled)

def energy_emoji(v):
    if v>=70: return "⚡"
    if v>=40: return "🔋"
    return "😴"

def mood_emoji(v):
    if v>=70: return "😄"
    if v>=40: return "😐"
    return "😤"
