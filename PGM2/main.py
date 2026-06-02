from arc4 import ARC4
from card import keys
from card.orleg2 import CharacterType


def get_checksum(data) -> int:
    checksum = 0
    for i in data:
        checksum ^= i
    return checksum

def guess_checksum(data: bytes) -> list[int]:
    guess_list = []
    card_data = data[1:]
    for i in range(256):
        fix_data = bytes([i]) + card_data
        decrypted_data = ARC4(keys.ORLEG2).decrypt(fix_data)
        checksum = get_checksum(decrypted_data[1:])
        character_type = decrypted_data[0x2c]
        if checksum == decrypted_data[0] and character_type in CharacterType._value2member_map_:
            guess_list.append(hex(i))
    return guess_list

def check_card(full_data: bytes) -> None:
    
    data = full_data[0x21:0x100]
    
    card_data = ARC4(keys.ORLEG2).decrypt(data)
    card_checksum = card_data[0]
    real_checksum = get_checksum(card_data[1:])
    if card_checksum == real_checksum:
        with open("card_data.bin", "wb") as f:
            f.write(full_data[0x20].to_bytes(1, "big"))
            f.write(card_data)
        print("卡片校验正常")
    else:
        guess_list = guess_checksum(data)
        print(f"卡片校验失败，可能的校验和: {guess_list}")
        

with open("orleg2_p1.mcd", "rb") as f:
    full_data = f.read()
check_card(full_data)