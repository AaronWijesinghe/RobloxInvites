def game_ends_in_punctuation(game_name):
    try:
        last_letter = game_name[-1]
        if last_letter in [".", "?", "!", ";", ":"]:
            return True
        else:
            return False
    except:
        return False