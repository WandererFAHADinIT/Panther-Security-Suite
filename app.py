from flask import Flask, render_template, request, jsonify
import re
import math
import itertools
import time

app = Flask(__name__)

# Common passwords list
COMMON_PASSWORDS = [
    "password", "123456", "password123", "admin", "letmein",
    "qwerty", "abc123", "monkey", "1234567", "dragon",
    "111111", "baseball", "iloveyou", "master", "sunshine",
    "ashley", "bailey", "passw0rd", "shadow", "123123",
    "654321", "superman", "qazwsx", "michael", "football"
]

# Keyboard patterns
KEYBOARD_PATTERNS = [
    "qwerty", "asdf", "zxcv", "qazwsx", "1234", "12345",
    "123456", "abcd", "abcde", "abcdef"
]

def calculate_entropy(password):
    charset = 0
    if re.search(r'[a-z]', password): charset += 26
    if re.search(r'[A-Z]', password): charset += 26
    if re.search(r'[0-9]', password): charset += 10
    if re.search(r'[^a-zA-Z0-9]', password): charset += 32
    if charset == 0:
        return 0
    entropy = len(password) * math.log2(charset)
    return round(entropy, 2)

def estimate_crack_time(entropy):
    # Assuming 1 billion guesses per second
    guesses = 2 ** entropy
    seconds = guesses / 1_000_000_000

    if seconds < 1:
        return "Less than a second ⚡"
    elif seconds < 60:
        return f"{round(seconds)} seconds"
    elif seconds < 3600:
        return f"{round(seconds/60)} minutes"
    elif seconds < 86400:
        return f"{round(seconds/3600)} hours"
    elif seconds < 31536000:
        return f"{round(seconds/86400)} days"
    elif seconds < 3153600000:
        return f"{round(seconds/31536000)} years"
    else:
        return "Millions of years 🔒"

def analyze_password(password):
    score = 0
    suggestions = []

    # Length check
    length = len(password)
    if length >= 16:
        score += 3
    elif length >= 12:
        score += 2
    elif length >= 8:
        score += 1
    else:
        suggestions.append("Use at least 8 characters — longer is always better")

    # Character checks
    has_upper = bool(re.search(r'[A-Z]', password))
    has_lower = bool(re.search(r'[a-z]', password))
    has_numbers = bool(re.search(r'[0-9]', password))
    has_symbols = bool(re.search(r'[^a-zA-Z0-9]', password))

    if has_upper: score += 1
    else: suggestions.append("Add uppercase letters (A-Z)")

    if has_lower: score += 1
    else: suggestions.append("Add lowercase letters (a-z)")

    if has_numbers: score += 1
    else: suggestions.append("Add numbers (0-9)")

    if has_symbols: score += 2
    else: suggestions.append("Add symbols like !@#$%^&*")

    # Common password check
    is_common = password.lower() in COMMON_PASSWORDS
    if is_common:
        score = max(0, score - 4)
        suggestions.append("This is a very common password — change it immediately!")

    # Keyboard pattern check
    has_pattern = any(p in password.lower() for p in KEYBOARD_PATTERNS)
    if has_pattern:
        score = max(0, score - 2)
        suggestions.append("Avoid keyboard patterns like qwerty or 12345")

    # Repeated characters check
    if re.search(r'(.)\1{2,}', password):
        score = max(0, score - 1)
        suggestions.append("Avoid repeating characters like aaa or 111")

    # Entropy
    entropy = calculate_entropy(password)
    crack_time = estimate_crack_time(entropy)

    # Cap score at 10
    score = min(10, score)

    return {
        "score": score,
        "length": length,
        "has_upper": has_upper,
        "has_lower": has_lower,
        "has_numbers": has_numbers,
        "has_symbols": has_symbols,
        "is_common": is_common,
        "has_pattern": has_pattern,
        "entropy": entropy,
        "crack_time": crack_time,
        "suggestions": suggestions
    }

# ===== ROUTES =====

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyzer')
def analyzer():
    return render_template('analyzer.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    password = data.get('password', '')
    result = analyze_password(password)
    return jsonify(result)


# ===== BRUTE FORCE =====

CHAR_SETS = {
    'digits': '0123456789',
    'lower': 'abcdefghijklmnopqrstuvwxyz',
    'alphanumeric': 'abcdefghijklmnopqrstuvwxyz0123456789'
}

def get_comparison_table(charset_size, target_length):
    comparison = []
    # Assuming 1 million attempts per second for realistic demo
    speed = 1_000_000
    for length in range(1, target_length + 4):
        combinations = charset_size ** length
        seconds = combinations / speed
        if seconds < 1:
            time_str = "< 1 second"
        elif seconds < 60:
            time_str = f"{round(seconds)} seconds"
        elif seconds < 3600:
            time_str = f"{round(seconds/60)} minutes"
        elif seconds < 86400:
            time_str = f"{round(seconds/3600)} hours"
        elif seconds < 31536000:
            time_str = f"{round(seconds/86400)} days"
        elif seconds < 3153600000:
            time_str = f"{round(seconds/31536000)} years"
        else:
            time_str = "Millions of years"
        comparison.append({
            "length": length,
            "combinations": f"{combinations:,}",
            "time": time_str
        })
    return comparison

def brute_force_attack(target, charset_str):
    attempts = 0
    for length in range(1, len(target) + 1):
        for combo in itertools.product(charset_str, repeat=length):
            attempts += 1
            guess = ''.join(combo)
            if guess == target:
                return guess, attempts
    return None, attempts

@app.route('/bruteforce')
def bruteforce_page():
    return render_template('bruteforce.html')

@app.route('/bruteforce', methods=['POST'])
def bruteforce_attack():
    data = request.get_json()
    target = data.get('password', '')
    charset_key = data.get('charSet', 'digits')
    charset_str = CHAR_SETS.get(charset_key, '0123456789')

    cracked, attempts = brute_force_attack(target, charset_str)
    comparison = get_comparison_table(len(charset_str), len(target))

    return jsonify({
        "cracked": cracked,
        "attempts": attempts,
        "comparison": comparison
    })

# ===== DICTIONARY ATTACK =====

WORDLIST = [
    "password", "123456", "password123", "admin", "letmein",
    "qwerty", "abc123", "monkey", "dragon", "master",
    "sunshine", "ashley", "bailey", "shadow", "superman",
    "michael", "football", "iloveyou", "baseball", "welcome",
    "login", "hello", "charlie", "donald", "password1",
    "qwerty123", "1q2w3e4r", "zxcvbnm", "trustno1", "starwars",
    "passw0rd", "hunter", "ranger", "test", "root",
    "toor", "pass", "abc", "default", "guest",
    "alpine", "changeme", "secret", "security", "hacker",
    "cyber", "shield", "attack", "defend", "network"
]

def generate_mutations(word):
    mutations = []
    # Capitalization
    mutations.append(word.capitalize())
    mutations.append(word.upper())

    # Common suffixes
    for suffix in ['123', '1', '!', '@', '#', '2024', '2023', '123!', '1234']:
        mutations.append(word + suffix)
        mutations.append(word.capitalize() + suffix)

    # Leet speak
    leet = word.replace('a', '@').replace('e', '3').replace('i', '1').replace('o', '0').replace('s', '$')
    mutations.append(leet)
    mutations.append(leet.capitalize())

    # Reverse
    mutations.append(word[::-1])

    # Double word
    mutations.append(word + word)

    return mutations

def dictionary_attack(target, attack_mode):
    attempts = 0
    total_mutations = 0

    for word in WORDLIST:
        # Basic check
        attempts += 1
        if word == target:
            return word, attempts, total_mutations, f'Found as plain word: "{word}" in wordlist'

        if attack_mode == 'mutations':
            mutations = generate_mutations(word)
            total_mutations += len(mutations)
            for mutation in mutations:
                attempts += 1
                if mutation == target:
                    return mutation, attempts, total_mutations, f'Base word "{word}" was mutated to "{mutation}"'

    return None, attempts, total_mutations, "Not found in wordlist or mutations"
@app.route('/dictionary', methods=['GET'])
def dictionary_page():
    return render_template('dictionary.html')
@app.route('/dictionary', methods=['POST'])
def dictionary_attack_route():
    data = request.get_json()
    target = data.get('password', '')
    attack_mode = data.get('attackMode', 'mutations')
    custom_words = data.get('customWords', None)

   
    if custom_words and len(custom_words) > 0:
        wordlist_to_use = custom_words
    else:
        wordlist_to_use = WORDLIST

    
    original_wordlist = WORDLIST.copy()
    WORDLIST.clear()
    WORDLIST.extend(wordlist_to_use)

    cracked, attempts, total_mutations, mutation_info = dictionary_attack(target, attack_mode)

    # Restore original wordlist
    WORDLIST.clear()
    WORDLIST.extend(original_wordlist)

    return jsonify({
        "cracked": cracked,
        "attempts": attempts,
        "total_words": len(wordlist_to_use),
        "total_mutations": total_mutations,
        "mutation_info": mutation_info
    })
# ===== HASH CRACKER =====
import hashlib
import os

HASH_INFO = {
    'MD5': 'MD5 produces a 32 character hex hash. It was widely used in the early 2000s but is now considered completely broken. Collisions can be found in seconds and rainbow tables exist for billions of common passwords. Never use MD5 for password storage.',
    'SHA1': 'SHA1 produces a 40 character hex hash. It was deprecated by NIST in 2011. While stronger than MD5, it is still vulnerable to rainbow table attacks and should not be used for passwords.',
    'SHA256': 'SHA256 produces a 64 character hex hash and is part of the SHA-2 family. It is much stronger than MD5 and SHA1 but still vulnerable to brute force without salting. Modern systems use SHA256 with bcrypt or Argon2 for proper password storage.',
    'bcrypt': 'bcrypt is a password hashing function designed to be slow and resistant to brute force attacks. It automatically salts passwords and can be tuned to become slower as hardware improves. This is the industry standard for password storage today.',
    'Unknown': 'Hash type could not be identified. Make sure you pasted the complete hash.'
}

def identify_hash(hash_str):
    if len(hash_str) == 32 and re.match(r'^[a-f0-9]+$', hash_str, re.I):
        return 'MD5'
    elif len(hash_str) == 40 and re.match(r'^[a-f0-9]+$', hash_str, re.I):
        return 'SHA1'
    elif len(hash_str) == 64 and re.match(r'^[a-f0-9]+$', hash_str, re.I):
        return 'SHA256'
    elif hash_str.startswith('$2b$') or hash_str.startswith('$2a$'):
        return 'bcrypt'
    return 'Unknown'

def hash_password(password, hash_type):
    if hash_type == 'MD5':
        return hashlib.md5(password.encode()).hexdigest()
    elif hash_type == 'SHA1':
        return hashlib.sha1(password.encode()).hexdigest()
    elif hash_type == 'SHA256':
        return hashlib.sha256(password.encode()).hexdigest()
    return None

def crack_hash(target_hash, hash_type, attack_mode):
    attempts = 0
    phase = '📖 Dictionary phase'

    # Build full wordlist with mutations
    all_words = list(WORDLIST)
    if attack_mode == 'both':
        for word in WORDLIST:
            all_words.extend(generate_mutations(word))

    # Try every word
    for word in all_words:
        attempts += 1
        hashed = hash_password(word, hash_type)
        if hashed and hashed.lower() == target_hash.lower():
            return word, attempts, phase

    # Brute force phase for short passwords
    if attack_mode == 'both':
        phase = '⚡ Brute force phase'
        charset = 'abcdefghijklmnopqrstuvwxyz0123456789'
        for length in range(1, 5):
            for combo in itertools.product(charset, repeat=length):
                attempts += 1
                guess = ''.join(combo)
                hashed = hash_password(guess, hash_type)
                if hashed and hashed.lower() == target_hash.lower():
                    return guess, attempts, phase

    return None, attempts, phase

def generate_salt_demo(password, hash_type):
    salt = os.urandom(8).hex()[:8]
    salted = password + salt
    if hash_type == 'MD5':
        salted_hash = hashlib.md5(salted.encode()).hexdigest()
    elif hash_type == 'SHA1':
        salted_hash = hashlib.sha1(salted.encode()).hexdigest()
    else:
        salted_hash = hashlib.sha256(salted.encode()).hexdigest()
    return salt, salted_hash

@app.route('/hashcracker')
def hashcracker_page():
    return render_template('hashcracker.html')

@app.route('/hashcracker', methods=['POST'])
def hashcracker_route():
    data = request.get_json()
    target_hash = data.get('hash', '').strip()
    attack_mode = data.get('attackMode', 'both')

    hash_type = identify_hash(target_hash)

    if hash_type == 'Unknown' or hash_type == 'bcrypt':
        return jsonify({
            "cracked": None,
            "attempts": 0,
            "phase": "❌ Unsupported hash type",
            "hash_info": HASH_INFO.get(hash_type, ''),
            "salt_example": '',
            "salted_hash": ''
        })

    cracked, attempts, phase = crack_hash(target_hash, hash_type, attack_mode)

    salt_example = ''
    salted_hash = ''
    if cracked:
        salt_example, salted_hash = generate_salt_demo(cracked, hash_type)

    return jsonify({
        "cracked": cracked,
        "attempts": attempts,
        "phase": phase,
        "hash_info": HASH_INFO.get(hash_type, ''),
        "salt_example": salt_example,
        "salted_hash": salted_hash
    })
from fpdf import FPDF
from datetime import datetime

# ===== REPORT GENERATOR =====

class ReportPDF(FPDF):
    def header(self):
        self.set_fill_color(10, 10, 26)
        self.rect(0, 0, 210, 30, 'F')
        self.set_font('Helvetica', 'B', 18)
        self.set_text_color(0, 212, 255)
        self.cell(0, 15, 'CyberShield Security Report', align='C', new_x='LMARGIN', new_y='NEXT')
        self.set_font('Helvetica', '', 10)
        self.set_text_color(150, 150, 150)
        self.cell(0, 8, 'Password Security Analysis Suite | PUCIT | BS Information Technology',
                  align='C', new_x='LMARGIN', new_y='NEXT')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, f'Page {self.page_no()} | CyberShield | Educational Purpose Only',
                  align='C')

def add_section(pdf, title, color, rows):
    # Section header
    pdf.set_fill_color(*color)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 10, title, fill=True, new_x='LMARGIN', new_y='NEXT')
    pdf.ln(2)

    # Rows
    for label, value in rows:
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_text_color(150, 150, 150)
        pdf.set_fill_color(15, 15, 30)
        pdf.cell(70, 9, label, fill=True)
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(220, 220, 220)
        pdf.set_fill_color(20, 20, 40)
        pdf.cell(0, 9, str(value), fill=True, new_x='LMARGIN', new_y='NEXT')

    pdf.ln(5)

@app.route('/report')
def report_page():
    return render_template('report.html')

@app.route('/generate_report', methods=['POST'])
def generate_report():
    data = request.get_json()

    pdf = ReportPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_margins(15, 35, 15)

    # Student info
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(0, 212, 255)
    pdf.cell(0, 8, 'Student Information', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(200, 200, 200)
    pdf.cell(0, 7, f"Name: {data['studentName']}    |    Roll No: {data['rollNumber']}    |    Date: {datetime.now().strftime('%B %d, %Y')}",
             new_x='LMARGIN', new_y='NEXT')
    pdf.ln(8)

    # Module 1
    add_section(pdf, 'Module 1 - Password Strength Analyzer', (0, 80, 160), [
        ('Password Tested', data['m1']['password']),
        ('Strength Score', f"{data['m1']['score']} / 10"),
        ('Strength Level', data['m1']['strength']),
        ('Estimated Crack Time', data['m1']['crackTime']),
    ])

    # Module 2
    add_section(pdf, 'Module 2 - Brute Force Attack', (160, 30, 0), [
        ('Password Cracked', data['m2']['password']),
        ('Total Attempts', data['m2']['attempts']),
        ('Time Taken', data['m2']['time']),
        ('Character Set', data['m2']['charset']),
    ])

    # Module 3
    add_section(pdf, 'Module 3 - Dictionary Attack', (160, 80, 0), [
        ('Password Cracked', data['m3']['password']),
        ('Words Tried', data['m3']['words']),
        ('Crack Method', data['m3']['method']),
        ('Time Taken', data['m3']['time']),
    ])

    # Module 4
    add_section(pdf, 'Module 4 - Hash Identifier & Cracker', (100, 0, 160), [
        ('Hash Type', data['m4']['hashType']),
        ('Original Password', data['m4']['password']),
        ('Attempts Made', data['m4']['attempts']),
        ('Time Taken', data['m4']['time']),
    ])

    # Conclusion
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(0, 212, 255)
    pdf.cell(0, 8, 'Conclusion & Recommendations', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(180, 180, 180)
    conclusions = [
        '1. Short and common passwords are extremely vulnerable to brute force and dictionary attacks.',
        '2. MD5 and SHA1 hashes can be cracked within seconds using wordlists.',
        '3. Passwords should be at least 12 characters with mixed case, numbers and symbols.',
        '4. Always use modern hashing algorithms like bcrypt or Argon2 with salting.',
        '5. Enable multi-factor authentication wherever possible for additional security.'
    ]
    for line in conclusions:
        pdf.cell(0, 8, line, new_x='LMARGIN', new_y='NEXT')

    # Output PDF
    from flask import make_response
    pdf_bytes = pdf.output()
    response = make_response(bytes(pdf_bytes))
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=CyberShield_Report.pdf'
    return response
if __name__ == '__main__':
    app.run(debug=True)