# inventory.py

class Item:
    def __init__(self, name, effect_type, effect_value):
        self.name = name
        self.effect_type = effect_type
        self.effect_value = effect_value

    def use(self, player):
        if self.effect_type == "heal":
            player.hp = min(player.hp + self.effect_value, 100)
        elif self.effect_type == "buff_attack":
            player.damage += self.effect_value


class Inventory:
    def __init__(self):
        self.items = []

    def add_item(self, item):
        self.items.append(item)

    def use_item(self, index, player):
        if 0 <= index < len(self.items):
            self.items[index].use(player)
            del self.items[index]
