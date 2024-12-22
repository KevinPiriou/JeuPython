# inventory.py

class Item:
    def __init__(self, name, effect_type, effect_value):
        """
        :param name: Nom de l'objet
        :param effect_type: 'heal', 'buff_attack', etc.
        :param effect_value: valeur chiffrée de l'effet
        """
        self.name = name
        self.effect_type = effect_type
        self.effect_value = effect_value

    def use(self, player):
        """
        Applique l'effet de l'objet au joueur.
        """
        if self.effect_type == "heal":
            player.hp = min(player.hp + self.effect_value, 100)
        elif self.effect_type == "buff_attack":
            player.damage += self.effect_value
        # d'autres types d'effets sont possibles


class Inventory:
    def __init__(self):
        self.items = []

    def add_item(self, item):
        self.items.append(item)

    def use_item(self, index, player):
        """
        Utilise l'item à l'index 'index', s'il existe.
        L'objet est consommé après usage.
        """
        if 0 <= index < len(self.items):
            self.items[index].use(player)
            del self.items[index]
