import typing
import enum
import os
import json
import traceback
import requests
import bs4

DB_URL = "https://tiphereth.zasz.su"
DB_COMBAT_CARDS_URL = "https://tiphereth.zasz.su/cards/"


class Rarity(enum.Enum):
    Common = "common"
    Uncommon = "uncommon"
    Rare = "rare"
    Unique = "unique"


class CardType(enum.Enum):
    Melee = "melee"
    Ranged = "ranged"
    Special = "special"
    Immediate = "immediate"
    MassSummation = "mass_summation"
    MassIndividual = "mass_individual"


class ActionGroup(enum.Enum):
    Offensive = "offensive"
    Defensive = "defensive"
    Counter = "counter"


class ActionType(enum.Enum):
    Slash = "slash"
    Pierce = "pierce"
    Blunt = "blunt"
    Evade = "evade"
    Guard = "guard"


class Availability(enum.Enum):
    Collectable = "collectable"
    Obtainable = "obtainable"
    EnemyOnly = "enemy_only"


class Action(typing.NamedTuple):
    group: ActionGroup
    type: ActionType
    min: int
    max: int
    description: str
    html_description: str

    def serialize(self) -> dict:
        return {
            "group": self.group.value,
            "type": self.type.value,
            "min": self.min,
            "max": self.max,
            "description": self.description,
            "html_description": self.html_description
        }


class Card(typing.NamedTuple):
    name: str
    availability: Availability
    rarity: Rarity
    type: CardType
    is_ego: bool
    cost: int
    image: str
    description: str
    actions: typing.List[Action]

    def serialize(self) -> dict:
        return {
            "name": self.name,
            "availability": self.availability.value,
            "rarity": self.rarity.value,
            "type": self.type.value,
            "is_ego": self.is_ego,
            "cost": self.cost,
            "image": self.image,
            "description": self.description,
            "actions": [action.serialize() for action in self.actions]
        }


def scrap(queries: typing.Dict[str, typing.Any] = {}) -> typing.List[Card]:
    raw = requests.get(DB_COMBAT_CARDS_URL, queries).text
    soup = bs4.BeautifulSoup(raw, "html.parser")

    cards = []
    raw_cards: typing.List[bs4.Tag] = soup.find_all("lor-card")

    for raw_card in raw_cards:
        try:
            front: bs4.Tag = raw_card.select_one("lor-card-front")
            front_heading: bs4.Tag = front.select_one("lor-card-heading")
            back: bs4.Tag = raw_card.select_one("lor-card-back")

            name = front_heading.select_one(
                "lor-card-name > a > span").get_text()

            match raw_card.attrs["data-availability"]:
                case "Collectable":
                    availability = Availability.Collectable
                case "Obtainable":
                    availability = Availability.Obtainable
                case "EnemyOnly":
                    availability = Availability.EnemyOnly

            match raw_card.attrs["data-rarity"]:
                case "Common":
                    rarity = Rarity.Common
                case "Uncommon":
                    rarity = Rarity.Uncommon
                case "Rare":
                    rarity = Rarity.Rare
                case "Unique":
                    rarity = Rarity.Unique

            match front_heading.select_one("lor-card-icon > i").attrs["title"]:
                case "Melee":
                    card_type = CardType.Melee
                case "Ranged":
                    card_type = CardType.Ranged
                case "Special":
                    card_type = CardType.Special
                case "Immediate":
                    card_type = CardType.Immediate
                case "Mass-Individual":
                    card_type = CardType.MassIndividual
                case "Mass-Summation":
                    card_type = CardType.MassSummation
            is_ego = bool(raw_card.attrs.get("data-ego"))

            cost = int(front_heading.select_one("lor-card-icon").get_text())
            try:
                description = back.select_one(
                    "lor-card-desc > span > b").get_text()
            except AttributeError:
                description = None
            image = DB_URL + front.select_one("lor-card-image > a > img").attrs["src"]
            actions = []
            for raw_action in (back.select_one("lor-card-desc > table > tbody") or back.select_one("lor-card-desc > table")).select("tr"):

                raw_group = raw_action.attrs["data-type"]
                raw_type = raw_action.attrs["data-detail"]

                match raw_group:
                    case "Atk":
                        action_group = ActionGroup.Offensive
                    case "Def":
                        action_group = ActionGroup.Defensive
                    case "Standby":
                        action_group = ActionGroup.Counter

                match raw_type:
                    case "Slash":
                        action_type = ActionType.Slash
                    case "Pierce":
                        action_type = ActionType.Pierce
                    case "Blunt":
                        action_type = ActionType.Blunt
                    case "Evade":
                        action_type = ActionType.Evade
                    case "Guard":
                        action_type = ActionType.Guard

                try:
                    action_description: bs4.Tag = raw_action.select_one(
                        "td > span").get_text()
                    action_html_description = str(
                        raw_action.select_one("td > span"))
                except AttributeError:
                    action_description = None
                    action_html_description = None

                min, max = [int(n) for n in raw_action.find("td", {
                    "class": "range"
                }).get_text().replace(" ", "").split("-")]

                action = Action(action_group, action_type,
                                min, max, action_description, action_html_description)
                actions.append(action)
            card = Card(name, availability, rarity, card_type, is_ego,
                        cost, image, description, actions)
            cards.append(card)
        except Exception as e:
            traceback.print_exc()

    try:
        pages = list(soup.find("div", attrs={
            "class": "pages"
        }).select("*"))
        next: bs4.Tag = pages[-1]
        if next.attrs.get("class") == "disabled":
            return cards

        new_queries = queries.copy()
        if not new_queries.get("page"):
            new_queries["page"] = 2
        else:
            new_queries["page"] += 1

        return cards + scrap(new_queries)
    except Exception as e:
        return cards


BASE = os.path.dirname(__file__)
OUT = os.path.join(BASE, "out", "combat")


def normalize_filename(filename: str) -> str:
    return filename.replace("?", "[question_mark]") \
                   .replace("/", "[slash]") \
                   .replace("\\", "[black_slash]") \
                   .replace(":", "[colon]") \
                   .replace("*", "[asterisk]") \
                   .replace("<", "[left_angle_bracket]") \
                   .replace(">", "[right_angle_bracket]") \
                   .replace("|", "[vertical_bar]")


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    for card in scrap():
        with open(os.path.join(OUT, normalize_filename(f"{card.name}.json")), "w+", encoding="utf-8") as f:
            f.write(json.dumps(card.serialize(), indent=4))


if __name__ == "__main__":
    main()
