CLASSES = {
    "1|0|0": {"number": 1, "dummy": "BIC16rc", "asm": "bic #1, r3"},
    "11|00|00": {"number": 2, "dummy": "BIC16ri", "asm": "bic #42, r3"},
    "11001|00101|00000": {"number": 19, "dummy": "BIC16mi", "asm": "bic #0x42, &dummy"},
    "11001|00001|00000": {"number": 20, "dummy": "MOV16mi", "asm": "mov #0x42, &dummy"},
    "110001|010101|000000": {"number": 24, "dummy": "BIC16mm", "asm": "bic &dummy, &dummy"},
    "110001|010001|000000": {"number": 25, "dummy": "MOV16mm", "asm": "mov &dummy, &dummy"},
    "101|010|000": {"number": 34, "dummy": "MOV16rm", "asm": "mov &dummy, r3"},
    "1001|0101|0000": {"number": 41, "dummy": "SWPB16m", "asm": "swpb &dummy"},
    "1001|0001|0000": {"number": 42, "dummy": "MOV16mc", "asm": "mov #1, &dummy"},
    "10001|10101|00000": {"number": 46, "dummy": "BIC16mn", "asm": "bic @r1, &dummy"},
    "10001|10001|00000": {"number": 47, "dummy": "MOV16mn", "asm": "mov @r1, &dummy"},
    "01|10|00": {"number": 58, "dummy": "MOV16rn", "asm": "mov @r1, r3"},
}
