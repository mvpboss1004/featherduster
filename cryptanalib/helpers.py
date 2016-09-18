'''
Cryptanalib - A series of useful functions for cryptanalysis
by Daniel "unicornFurnace" Crowley

dependencies - PyCrypto, GMPy
'''

from Crypto.Hash import *
from Crypto.PublicKey import RSA

import string
import frequency
import gmpy
import zlib

#------------------------------------
# Helper functions
# 
# This section contains various functions that are not terribly
# useful on their own, but allow other functionality to work
#------------------------------------

def check_rsa_key(sample):
   """
   Returns a 3-tuple (is_rsa_key, has_private_component, n_bit_length)
   
   is_rsa_key - a bool indicating that the sample is, in fact, an RSA key
      in a format readable by Crypto.PublicKey.RSA.importKey
   has_private_component - a bool indicating whether or not d was in the
      analyzed key, or false if the sample is not an RSA key
   n_bit_length - an int representing the bit length of the modulus found
      in the analyzed key, or False if the sample is not an RSA key
   """
   is_rsa_key = has_private_component = n_bit_length = False

   try:
      rsakey = RSA.importKey(sample.strip())
      is_rsa_key = True
      if rsakey.has_private():
         has_private_component = True
      n_bit_length = gmpy.mpz(rsakey.n).bit_length()
   # Don't really care why it fails, just want to see if it did
   except:
      is_rsa_key = False
   return (is_rsa_key, has_private_component, n_bit_length)
      

def show_histogram(frequency_table, width=80, sort=True):
   '''
   Take a frequency distribution, such as one generated by
   generate_frequency_table() and represent it as a histogram with the
   specified width in characters

   frequency_table - A frequency distribution
   width - The width in characters for the histogram
   sort - (bool) Sort the histogram by frequency value?
   '''
   max_value = max(frequency_table.values())
   normalizing_multiplier = width / max_value

   if sort:
      frequency_table = sorted(frequency_table.items(),key=lambda (k,v): (v,k), reverse=True)
   else:
      frequency_table = frequency_table.items()

   print '0%' + ' ' * (width-6) + str(max_value*100)+'%'
   print '-' * width
   
   for key, value in frequency_table:
      freq_bars = int(value * normalizing_multiplier)
      if freq_bars != 0:
         print key + '|' + '=' * freq_bars

def is_base64_encoded(sample):
   '''
   Check if a sample is likely base64-encoded
   
   sample - (string) The sample to evaluate
   '''
   base64chars = string.letters + string.digits + string.whitespace
   base64chars += '/+='
   # Turns out a lot of crazy things will b64-decode happily with
   # sample.decode('base64'). This is the fix.
   if any([char not in base64chars for char in sample]):
      return False
   try:
      sample.decode('base64')
      return True
   except:
      return False


def is_hex_encoded(sample):
   '''
   Check if a sample hex-decodes without error

   sample - (string) The sample to evaluate
   '''
   try:
      sample.decode('hex')
      return True
   except:
      return False

def is_zlib_compressed(sample):
   '''
   Check if some sample can be zlib decompressed without error
   
   sample - (string) The sample to evaluate
   '''
   try:
      zlib.decompress(sample)
      return True
   except:
      return False


def detect_polybius(sample):
   '''
   Detect the use of the polybius cipher
   
   sample - (string) The sample to evaluate
   '''
   correct_charset = all([char in ' 01234567' for char in sample])
   correct_length = len(filter(lambda x: x in '01234567',sample)) % 2 == 0
   return correct_charset and correct_length


def monte_carlo_pi(sample):
   '''
   Monte Carlo Pi estimation test
   
   Good for determining the randomness of data, especially when looking at compressed
   vs encrypted data.
   
   Returns the estimated value of Pi. The closer the returned value to the value of Pi,
   the more entropy in the data.
   
   sample - (string) The sample to evaluate
   '''
   # cut down our sample to a multiple of four bytes in length so we
   # can take two two-byte samples for x/y coords
   if len(sample) < 4:
      return False
   if (len(sample) % 4) != 0:
      sample = sample[:-(len(sample)%4)]
   coords = []
   hits = 0
   for offset in range(0,len(sample),4):
      # extract four bytes from sample
      subsample = sample[offset:offset+4]
      # interpret the first two bytes as an X value between -32512.5 and 32512.5
      subsample_x = ((ord(subsample[0])*255)+(ord(subsample[1])))-32512.5
      # map this value down to one between -1.0 and 1.0
      subsample_x /= 32512.5
      # interpret the next two bytes as a Y value between -32512.5 and 32512.5
      subsample_y = ((ord(subsample[2])*255)+(ord(subsample[3])))-32512.5
      # map this value down to one between -1.0 and 1.0
      subsample_y /= 32512.5
      coords.append((subsample_x,subsample_y))
   for coordinate in coords:
      if coordinate[0]**2 + coordinate[1]**2 <= 1:
         hits += 1
   pi_estimate = 4*(float(hits) / (len(sample)/4))
   return pi_estimate


def check_key_reuse(samples):
   '''
   Check for key reuse between two or more messages
   
   Returns a boolean indicating whether two messages have high or low
   bitwise correspondence, which suggests key reuse.
   
   samples - (list) Two or more samples for evaluation
   '''
   if len(samples) == 1:
      print 'Need more than one sample'
      return None
   total_length = total_hamming_distance = 0
   for sample in samples[1:]:
      compare_length = min(len(samples[0]),len(sample))
      sample_hamming_distance = hamming_distance(samples[0],sample)
      total_hamming_distance += sample_hamming_distance
      total_length += compare_length
   mean_hamming_distance = total_hamming_distance / float(total_length)
   return ((mean_hamming_distance < 3.25) or (mean_hamming_distance > 4.75))



def do_simple_substitution(ciphertext, pt_charset, ct_charset):
   '''
   Perform simple substitution based on character sets

   Simplifies the use of string.translate(). If, for instance, you wish to
   transform a ciphertext where 'e' is swapped with 't', you would call this
   function like so:

   do_simple_substitution('Simplt subeieueion ciphtrs art silly','et','te')
   
   ciphertext - A string to translate
   pt_charset - The character set of the plaintext, usually 'abcdefghijk...xyz'
   ct_charset - The character set of the ciphertext
   '''
   #translate ciphertext to plaintext using mapping
   return string.translate(ciphertext, string.maketrans(ct_charset, pt_charset))


# TODO: Implement chi square and best compression ratio
def is_random(sample, verbose=False, boolean_results=True):
   '''
   Run randomness tests to determine likelihood of data being
   the output of strong crypto or CSPRNG or RNG a la ent
   
   with boolean_results=True
   Returns a boolean indicating whether all tests for randomness have passed
   
   with boolean_results=False
   Returns detailed results about what tests passed/failed

   sample - A string to evaluate for signs of randomness
   verbose - (bool) Whether to print information about results or not
   boolean_results - (bool) Whether to return True/False or show more details
      on what tests passed or failed
   '''
   results = {}
   sample_length = len(sample)
   if sample_length == 0:
      return False
   if sample_length < 100:
      if verbose:
         print '[*] Warning! Small sample size, results may be unreliable.'
   # Arithmetic mean test
   mean = sum([ord(char) for char in sample])/float(sample_length)
   if verbose:
      print '[+] Arithmetic mean of sample is '+str(mean)+'. (127.5 = random)'
   if ((mean <= 110) or (mean >= 145)):
      results['mean_failed'] = True
      if verbose:
         print '[!] Arithmetic mean of sample suggests non-random data.'
   else:
      results['mean_failed'] = False
   # Byte and digraph count test
   byte_count = generate_frequency_table(sample, map(chr,range(256)))
   min_to_max = max(byte_count.values())-min(byte_count.values())
   if verbose:
      print '[+] Distance between lowest and highest byte frequencies is '+str(min_to_max)+'.'
      print '[+] Distance for 100+ random bytes of data generally does not exceed 0.4'
   if min_to_max > 0.4:
      results['byte_count_failed'] = True
      if verbose:
         print '[!] Distance between byte frequencies suggests non-random data.'
   else:
      results['byte_count_failed'] = False
   # Longest bit run test
   binary_message = ''.join(['{0:08b}'.format(ord(char)) for char in sample])
   longest_bit_run_threshold = 20
   longest_run = 0
   current_run = 0
   prev_bit = None
   for bit in binary_message:
      if bit == prev_bit:
         current_run += 1
      else:
         current_run = 0
      if current_run > longest_run:
         longest_run = current_run
      prev_bit = bit
   if verbose:
      print '[+] Longest same-bit run in the provided sample is %s' % str(longest_run)
      print '[+] This value generally doesn\'t exceed 20 in random data.'
   results['bit_run_failed'] = (longest_run >= longest_bit_run_threshold)
   if results['bit_run_failed'] and verbose:
      print '[!] Long same-bit run suggests non-random data.'
   # Monte Carlo estimation of Pi test
   approximate_pi = 3.141592654
   monte_carlo_pi_value_deviation = abs(approximate_pi - monte_carlo_pi(sample)) 
   results['monte_carlo_failed'] = (monte_carlo_pi_value_deviation > 0.4)
   if verbose:
      print '[+] Deviation between the approx. value of pi and the one generated by this sample using Monte Carlo estimation is %s' % str(monte_carlo_pi_value_deviation)
      print '[+] Deviation for 100+ random bytes of data generally does not exceed 0.4.'
   if results['monte_carlo_failed'] and verbose:
      print '[!] Deviation exceeds 0.4. If no other randomness tests failed, this data may be compressed, not encrypted or random.'
   if boolean_results:
      if any(results.values()):
         if verbose:
            print '[!] One or more tests for randomness suggests non-random data.'
            print '[!] This data may be the result of weak encryption like XOR.'
            print '[!] This may also suggest a fixed IV or ECB mode.'
            print '[!] This data may also be simply compressed or in a proprietary format.'
         return False
      else:
         if verbose:
            print '[+] This data has passed all randomness tests performed.'
            print '[+] This suggests data generated by a RNG, CSPRNG, or strong encryption.'
         return True
   else:
      if verbose:
         if sum(results.values()) == 1:
            if results['monte_carlo_failed']:
               print '[+] Only the Monte Carlo Pi generation test has failed. This may indicate that the data is not encrypted, but simply compressed.'
            elif results['bit_run_failed']:
               print '[+] Only the longest-bit-run test has failed. This suggests that certain portions of the data are not encrypted.'
      return results

def gcd(a,b):
   '''
   Wrapper around extended_gcd() that simply returns the GCD alone.
   '''
   return extended_gcd(a,b)[2]


def extended_gcd(a, b): 
   '''
   Euclid's GCD algorithm, but with the addition that the last x and y values are returned.

   a, b - Two integers to find common factors for

   Returns (Last X value, Last Y value, Greatest common divisor)
   '''
   x,y = 0, 1
   lastx, lasty = 1, 0

   while b:
      a, (q, b) = b, divmod(a,b)
      x, lastx = lastx-q*x, x
      y, lasty = lasty-q*y, y

   return (lastx, lasty, a)

def chinese_remainder_theorem(items):
   '''
   The Chinese Remainder Theorem algorithm.

   items - A list of 2-tuples such as [(a1, n1),(a2, n2)] that map to congruences:
      a1 is congruent to x mod n1
      a2 is congruent to x mod n2
   '''
   N = 1 
   for a, n in items:
      N *= n

   result = 0 
   for a, n in items:
      m = N/n 
      r, s, d = extended_gcd(n, m)
      if d != 1:
         raise "Input not pairwise co-prime"
      result += a*s*m

   return result % N, N



def detect_block_cipher(ciphertext):
   '''
   Detect block cipher by length of ciphertext
   
   Return largest identified block size, or False if none

   ciphertext - (string) A sample to be evaluated for common block sizes
   '''
   for candidate_blocksize in [32,16,8]:
      if len(ciphertext) % candidate_blocksize == 0:
         return candidate_blocksize
   return False



def detect_plaintext(candidate_text, pt_freq_table=frequency.frequency_tables['english_letters'], detect_words=True, common_words=frequency.common_words['english'], individual_scores=False):
   '''
   Return score for likelihood that string is plaintext
   in specified language as a measure of deviation from
   expected frequency values (lower is better)

   candidate_text - (string) The sample to check for plaintext-like properties

   pt_freq_table - Expected frequency distribution for the plaintext, as generated
      by generate_frequency_table(). If only individual character frequency should
      be matched, ensure you're using a frequency table with only single character
      frequencies. If you're using the built-in tables, these are prefixed with
      'single_'.

   detect_words - (bool) Use a list of strings expected in the correct plaintext,
      aka 'cribs'.
      This can be used in a number of ways. For instance, when attempting to decrypt
      firmware, '\x00\x00\x00\x00\x00' may be a useful crib. When attempting to
      decrypt a PNG file, 'IHDR', 'IDAT', and 'IEND' are useful cribs.

   common_words - (list of strings) Words that are likely to appear in the plaintext.
      Requires detect_words=True.

   individual_scores - (bool) Whether or not to return a tuple with individual scores.
   '''

   # generate score as deviation from expected character frequency
   pt_freq_table_keys = pt_freq_table.keys()
   candidate_dict = generate_frequency_table(candidate_text, pt_freq_table_keys)
   char_deviation_score = 0
   for char in pt_freq_table_keys:
      char_deviation_score += abs(candidate_dict[char]-pt_freq_table[char])

   # generate score as total number of letters in common words found in sample
   word_count_score = 0
   if detect_words:
      word_count_score = count_words(candidate_text, common_words=common_words)
   
   if individual_scores:
      return (char_deviation_score, word_count_score)
   else:
      if word_count_score == 0:
         score = 1
      else:
         score = 1.0/word_count_score
      score += char_deviation_score
      return score


def generate_frequency_table(text,charset):
   '''
   Generate a character frequency table for a given text
   and charset as list of chars, digraphs, etc

   text - A sample of plaintext to analyze for frequency data
   charset - (list of strings) The set of items to count in the plaintext
      such as ['a','b','c', ... 'z','aa','ab','ac', ... 'zz']
   '''
   freq_table = {}
   text_len = 0 
   for char in charset:
      freq_table[char] = 0 
   for char in text:
      if char in charset:
         freq_table[char] += 1
         text_len += 1
   for multigraph in filter(lambda x: len(x)>1,charset):
      freq_table[multigraph] = string.count(text, multigraph)
   # Normalize frequencies with length of text
   for key in freq_table.keys():
      if text_len != 0:
         freq_table[key] /= float(text_len)
      else:
         freq_table[key] = 0 
   return freq_table

def generate_optimized_charset(text):
   '''
   Given a sample text, generate a frequency table and
   convert it to a string of characters sorted by frequency
   of appearance in the text. This can be used directly in
   some of the other cryptanalib functions, such as our
   Vaudenay padding oracle decryption function.

   (string) text - The corpus of text from which to learn
      frequency data.
   '''

   all_chars = map(chr, range(256))
   freq_table = generate_frequency_table(text, charset=all_chars)
   charset = sorted(freq_table, key=lambda x: freq_table[x], reverse=True)
   return ''.join(charset)
   
def hamming_distance(string1, string2):
   '''
   Calculate and return bitwise hamming distance between two strings
   
   string1 - The first string to compare
   string2 - The second string to compare
   '''
   distance = 0
   for char1, char2 in zip(string1, string2):
      for digit1, digit2 in zip('{0:08b}'.format(ord(char1)),'{0:08b}'.format(ord(char2))):
         if digit1 != digit2:
            distance += 1
   return distance

def output_mask(text, charset):
   '''
   Output masking - mask all characters besides those in the provided character
   set with dots.
   
   Parameters:
   (string) text - output to mask
   (string) charset - string containing acceptable characters
   '''
   all_chars = output_chars = map(chr,range(256))
   charset = set(charset)
   for charnum in range(256):
      if all_chars[charnum] not in charset:
         output_chars[charnum] = '.'
   return string.translate(text,''.join(output_chars))

def string_to_long(instring):
   '''
   Take a raw string and convert it to a number
   
   instring - String to convert
   '''
   return long(instring.encode("hex"),16)

def long_to_string(inlong):
   '''
   Take a long and convert it to a string
   
   inlong - Long to convert
   '''
   hex_encoded = hex(inlong)[2:-1]
   if len(hex_encoded) % 2 == 1:
      return ('0'+hex_encoded).decode('hex')
   else:
      return hex_encoded.decode('hex')

"""
# Removed for now because gmpy provides its own invmod
# gmpy.invert() seems to be OK for its current uses,
# but we'll leave this here a while just in case.
def inverse_mod( a, m ):
  '''
  Inverse of a mod m from ecdsa python module by Peter Pearson.

  a - (int) Operand one
  m - (int) Modulus
  '''

  if a < 0 or m <= a: a = a % m 

  # From Ferguson and Schneier, roughly:

  c, d = a, m
  uc, vc, ud, vd = 1, 0, 0, 1
  while c != 0:
    q, c, d = divmod( d, c ) + ( c, )
    uc, vc, ud, vd = ud - q*uc, vd - q*vc, uc, vc

  # At this point, d is the GCD, and ud*a+vd*m = d.
  # If d == 1, this means that ud is a inverse.

  assert d == 1
  if ud > 0: return ud
  else: return ud + m 
"""

def split_into_blocks(ciphertext,blocksize):
   '''
   Split a string into blocks of length blocksize

   ciphertext - A string to be split
   blocksize - The size in bytes of blocks to output
   '''
   ciphertext_len = len(ciphertext)
   return [ciphertext[offset:offset+blocksize] for offset in xrange(0,ciphertext_len,blocksize)]


def sxor(string1, string2):
   '''
   XOR two strings and return the result up to the length
   of the shorter string

   string1 - The first string to be XORed
   string2 - The second string to be XORed
   '''
   return ''.join(chr(ord(chr1)^ord(chr2)) for chr1, chr2 in zip(string1,string2))

def count_words(candidate_text, common_words=frequency.common_words['english'], case_sensitive=True):
   '''
   Count the instances of common words in the expected plaintext
   language, return the total number of characters matched in each
   word 

   candidate_text - (string) Sample to analyze
   common_words - (list) Sequences expected to appear in the text
   case_sensitive - (bool) Whether or not to match case sensitively
   '''
   score = 0

   for word in common_words:
      if not case_sensitive:
         word = word.lower()
      num_found = candidate_text.count(word)
      if num_found > 0:
         score += num_found * len(word)
      
   return score


def make_polybius_square(password,extended=False):
   '''
   Polybius square generator. Returns a list of strings of equal
   length, either 5x5 or 6x6 depending on whether extended
   Polybius mode is on. Assumes I/J are represented as one letter

   password - (string) The password to use when generating the polybius square
   extended - (bool) Set to True to use a 6x6 square instead of a 5x5
   '''
   alphabet = string.lowercase
   if extended == True:
      alphabet += string.digits
   else:
      alphabet = string.replace(string.lowercase, 'j', '')
      password = string.replace(password, 'j', 'i')
   if any([x not in alphabet for x in set(password)]):
      return False
   unique_letters = []
   for letter in password:
      if letter not in unique_letters:
         unique_letters.append(letter)
   for letter in unique_letters:
      alphabet = string.replace(alphabet, letter, '')
   for letter in unique_letters[::-1]:
      alphabet = letter + alphabet
   ps = []
   alphabet_len = len(alphabet)
   grid_size = 5 + int(extended) # Not necessary, but looks cleaner
   for index in xrange(0,alphabet_len,grid_size):
      ps.append(alphabet[index:index+grid_size])
   return ps

def polybius_decrypt(ps, ciphertext):
   '''
   Decrypt given a polybius square (such as one generated
   by make_polybius_square() ) and a ciphertext.

   ps - A polybius square as generated by make_polybius_square()
   ciphertext - A string to decrypt
   '''
   ct_len = len(ciphertext)
   if (ct_len % 2) != 0:
      return False
   digraphs = []
   plaintext = ''
   for index in xrange(0,ct_len,2):
      digraphs.append(ciphertext[index:index+2])
   for digraph in digraphs:
      x = int(digraph[0]) - 1
      y = int(digraph[1]) - 1
      plaintext += ps[y][x]
   return plaintext

def detect_ecb(ciphertext):
   '''
   Attempts to detect use of ECB by detecting duplicate blocks using common
   block sizes.
   
   ciphertext - A string to analyze for the indicators of ECB mode
   '''
   ciphertext_len = len(ciphertext)
   for blocksize in [32,16,8]:
      if ciphertext_len % blocksize == 0:
         blocks = split_into_blocks(ciphertext,blocksize)
         seen = set()
         for block in blocks:
            if block in seen:
               return (True, blocksize, block)
            else:
               seen.add(block)
   return (False, 0, '')


def pkcs7_padding_remove(text, blocksize):
   '''
   PKCS7 padding remove - returns unpadded string if successful, returns False if unsuccessful

   text - The text to pkcs7-unpad
   blocksize - The blocksize of the text
   '''
   last_byte = ord(text[-1:])
   if last_byte > blocksize:
      return False
   if text[-last_byte:] != chr(last_byte)*last_byte:
      return False
   else:
      return text[:-last_byte]

def pkcs7_pad(text, blocksize):
   '''
   PKCS7 padding function, returns text with PKCS7 style padding
   
   text - The text to pkcs7-pad
   blocksize - The blocksize of the text
   '''
   pad_num = (blocksize - len(text)%blocksize)
   return text+chr(pad_num)*pad_num


def derive_d_from_pqe(p,q,e):
   '''
   Given p, q, and e from factored RSA modulus, derive the private component d
   
   p - The first of the two factors of the modulus
   q - The second of the two factors of the modulus
   e - The public exponent
   '''
   return long(gmpy.invert(e,(p-1)*(q-1)))

