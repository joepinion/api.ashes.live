import re
from typing import List, Union

from api import db
from api.models.card import Card, conjurations_table
from api.models.release import Release
from api.utils.helpers import stubify

from .stream import create_entity


MAGIC_COSTS = (
    "basic",
    "ceremonial",
    "charm",
    "illusion",
    "natural",
    "divine",
    "sympathy",
    "time",
)


class MissingConjurations(Exception):
    pass


def parse_cost_to_weight(cost: str) -> int:
    """Converts a cost string into a weight"""
    match = re.match(r"^\s*(\d*)\s*\[\[([^\]]+)\]\]\s*$", cost)
    if not match:
        return 0
    cost_count = int(match.group(1)) if match.group(1) else None
    cost_parts = match.group(2).split(":")
    cost_type = cost_parts[0].lower()
    cost_subtype = cost_parts[1].lower() if len(cost_parts) > 1 else None
    if cost_type in MAGIC_COSTS and cost_count:
        weight = cost_count * 100
        if cost_subtype == "class":
            weight += cost_count * 1
        elif cost_subtype == "power":
            weight += cost_count * 2
        return weight
    elif cost_type == "discard" and cost_count:
        return cost_count * 3
    elif cost_type == "side":
        return 4
    elif cost_type == "main":
        return 5
    return 0


def parse_costs_to_mapping(costs: List[Union[List[str], str]]) -> dict:
    """Converts a list of costs into an associative mapping between cost and number"""
    magic_cost_re = re.compile(
        r"(\d+)\s+\[\[((?:" + r"|".join(MAGIC_COSTS) + r")(?::\w+)?)\]\]"
    )
    data_object = {}
    for cost in costs:
        # Handle a split cost
        if isinstance(cost, list):
            split_1 = magic_cost_re.match(cost[0])
            split_2 = magic_cost_re.match(cost[1])
            if not split_1 or not split_2:
                continue
            split_key = f"{split_1.group(2)} / {split_2.group(2)}"
            alt_split_key = f"{split_2.group(2)} / {split_1.group(2)}"
            magic_cost = max(int(split_1.group(1)), int(split_2.group(1)))
            if split_key in data_object:
                data_object[split_key] += magic_cost
            elif alt_split_key in data_object:
                data_object[alt_split_key] += magic_cost
            else:
                data_object[split_key] = magic_cost
        else:
            # Normal cost, so just add it to our object
            cost_match = magic_cost_re.match(cost)
            if not cost_match:
                continue
            if cost_match.group(2) in data_object:
                data_object[cost_match.group(2)] += int(cost_match.group(1))
            else:
                data_object[cost_match.group(2)] = int(cost_match.group(1))
    return data_object


def dice_name_from_cost(cost: str) -> str:
    """Given a string like `magic:face` returns just `magic`"""
    return cost.split(":")[0]


def create_card(
    session: db.Session,
    name: str,
    card_type: str,
    release: "Release",
    placement: str = None,
    text: str = None,
    cost: Union[List[str], str, None] = None,
    effect_magic_cost: Union[List[str], str, None] = None,
    can_effect_repeat: bool = False,
    dice: List[str] = None,
    alt_dice: List[str] = None,
    phoenixborn: str = None,
    attack: Union[int, str] = None,
    battlefield: Union[int, str] = None,
    life: Union[int, str] = None,
    recover: Union[int, str] = None,
    spellboard: Union[int, str] = None,
    copies: Union[int, str] = None,
) -> "Card":
    """Creates a card, generating the necessary JSON and cost info"""
    card = Card()
    card.name = name
    card.stub = stubify(name)
    card.card_type = card_type
    card.placement = placement
    card.release_id = release.id
    card.search_text = f"{card.name}\n"
    card.is_summon_spell = name.startswith("Summon ")
    existing_conjurations = None
    if text:
        card.search_text += re.sub(
            r"\n+", " ", text.replace("[[", "").replace("]]", "")
        )
        # Check for conjurations before we do any more work
        conjuration_stubs = set()
        for match in re.finditer(
            r"\[\[([A-Z][A-Za-z' ]+)\]\](?=[ ](?:(?:conjuration|conjured alteration spell)s?|or))",
            text,
        ):
            conjuration_stubs.add(stubify(match.group(1)))
        existing_conjurations = (
            session.query(Card.id, Card.stub, Card.name)
            .filter(Card.stub.in_(conjuration_stubs), Card.is_legacy.is_(False))
            .all()
        )
        existing_stubs = set(x.stub for x in existing_conjurations)
        missing_conjurations = conjuration_stubs.symmetric_difference(existing_stubs)
        if missing_conjurations:
            raise MissingConjurations(
                f"The following conjurations must be added first: {', '.join([x for x in missing_conjurations])}"
            )

    if copies is not None:
        card.copies = copies
    card.phoenixborn = phoenixborn
    card.entity_id = create_entity(session)
    cost_list = re.split(r"\s+-\s+", cost) if isinstance(cost, str) else cost
    weight = 0
    json_cost_list = []
    if cost_list:
        for cost_entry in cost_list:
            split_cost = (
                re.split(r"\s+(?:/|or)\s+", cost_entry)
                if isinstance(cost_entry, str)
                else cost_entry
            )
            if len(split_cost) > 1:
                first_weight = parse_cost_to_weight(split_cost[0])
                second_weight = parse_cost_to_weight(split_cost[1])
                weight += max(first_weight, second_weight)
                json_cost_list.append(split_cost)
            else:
                weight += parse_cost_to_weight(split_cost[0])
                json_cost_list.append(split_cost[0])
    card.cost_weight = weight
    # Extract our effect costs into a list of strings and lists
    effect_cost_list = []
    effect_costs = (
        re.split(r"\s+-\s+", effect_magic_cost)
        if isinstance(effect_magic_cost, str)
        else effect_magic_cost
    )
    if effect_costs:
        for cost_entry in effect_costs:
            split_cost = (
                re.split(r"\s+(?:/|or)\s+", cost_entry)
                if isinstance(cost_entry, str)
                else cost_entry
            )
            effect_cost_list.append(split_cost) if len(
                split_cost
            ) > 1 else effect_cost_list.append(split_cost[0])
    # Convert our cost lists into magicCost and effectMagicCost mappings
    json_magic_cost = parse_costs_to_mapping(json_cost_list)
    json_effect_cost = parse_costs_to_mapping(effect_cost_list)
    # And finally, convert our mappings into lists of required dice
    dice_set = set()
    alt_dice_set = set()
    for dice_type in list(json_magic_cost.keys()) + list(json_effect_cost.keys()):
        both_types = dice_type.split(" / ")
        if len(both_types) > 1:
            alt_dice_set.add(dice_name_from_cost(both_types[0]))
            alt_dice_set.add(dice_name_from_cost(both_types[1]))
        else:
            dice_set.add(dice_name_from_cost(both_types[0]))
    if dice is None:
        dice = list(dice_set)
    if alt_dice is None:
        alt_dice = list(alt_dice_set)
    card.dice_flags = Card.dice_to_flags(dice)
    card.alt_dice_flags = Card.dice_to_flags(alt_dice)
    json_data = {
        "name": card.name,
        "stub": card.stub,
        "type": card.card_type,
        "release": {
            "name": release.name,
            "stub": release.stub,
        },
    }
    if existing_conjurations:
        json_data["conjurations"] = [
            {"name": x.name, "stub": x.stub} for x in existing_conjurations
        ]
    if placement:
        json_data["placement"] = placement
    if json_cost_list:
        json_data["cost"] = json_cost_list
    if dice:
        json_data["dice"] = dice
    if alt_dice:
        json_data["altDice"] = alt_dice
    if json_magic_cost:
        json_data["magicCost"] = json_magic_cost
    if json_effect_cost:
        json_data["effectMagicCost"] = json_effect_cost
    if text:
        json_data["text"] = text
    if phoenixborn is not None:
        json_data["phoenixborn"] = phoenixborn
    if attack is not None:
        json_data["attack"] = attack
    if battlefield is not None:
        json_data["battlefield"] = battlefield
    if life is not None:
        json_data["life"] = life
    if recover is not None:
        json_data["recover"] = recover
    if spellboard is not None:
        json_data["spellboard"] = spellboard
    if copies is not None:
        json_data["copies"] = copies
    if can_effect_repeat:
        json_data["effectRepeats"] = True
    card.json = json_data
    session.add(card)
    session.commit()
    # Now that we have a card entry, we can populate the conjuration relationship(s)
    if existing_conjurations:
        for conjuration in existing_conjurations:
            session.execute(
                conjurations_table.insert().values(
                    card_id=card.id, conjuration_id=conjuration.id
                )
            )
    return card
