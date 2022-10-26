import string

def alpha_shift(plaintext, key):
   ciphertext = ''
   for char in plaintext.lower():
      if char in string.ascii_lowercase:
         ciphertext += string.ascii_lowercase[(string.ascii_lowercase.find(char)+key)%26]
      else:
         ciphertext += char
   return ciphertext

print(alpha_shift('This is my ciphertext. It\'s awesome and wonderful.', 6))
