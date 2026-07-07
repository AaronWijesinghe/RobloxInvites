def game_ends_in_punctuation(game_name):
    try:
        last_letter = game_name[-1]
        if last_letter in [".", "?", "!", ";", ":"]:
            return True
        else:
            return False
    except:
        return False

def get_number(string):
    new_string = ""
    scanning_place_id = False
    for char in string:
        if char.isdigit() and not scanning_place_id:
            scanning_place_id = True
            new_string += char
        elif char.isdigit() and scanning_place_id:
            new_string += char
        elif not char.isdigit() and scanning_place_id:
            break
    return new_string