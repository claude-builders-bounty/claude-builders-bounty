#!/usr/bin/env python3
"""
Fix for issue #2746: Malformed command `/opire try` should be handled gracefully
or corrected to proper command format.
"""

import re

def parse_bounty_command(input_text: str) -> dict:
    """
    Parse bounty-related commands from input text.
    Handles edge cases like malformed commands.
    """
    # Normalize the input - strip whitespace
    cleaned = input_text.strip()
    
    # Pattern to match valid bounty commands
    # Valid prefixes: /claim, /attempt, /open, /openai, etc.
    valid_prefixes = ['claim', 'attempt', 'open', 'openai']
    
    # Check if input starts with a bounty command
    if not cleaned.startswith('/'):
        return {'valid': False, 'command': None, 'args': []}
    
    # Extract potential command
    match = re.match(r'^/(\w+)\s*(.*)', cleaned)
    if not match:
        return {'valid': False, 'command': None, 'args': []}
    
    cmd = match.group(1).lower()
    args = match.group(2).strip()
    
    # Validate command
    if cmd in valid_prefixes:
        return {
            'valid': True,
            'command': cmd,
            'args': args,
            'original': cleaned
        }
    
    # Handle malformed commands gracefully
    # Log warning but don't crash
    print(f"Warning: Unknown or malformed bounty command '{cleaned}'")
    return {
        'valid': False,
        'command': None,
        'args': [],
        'error': f'Malformed command: {cleaned}',
        'suggestion': _suggest_correction(cmd)
    }


def _suggest_correction(malformed_cmd: str) -> str:
    """
    Suggest corrections for malformed commands.
    For 'opire', suggest possible intended commands.
    """
    suggestions = {
        'opire': ['open', 'attempt'],
        'opn': ['open'],
        'aim': ['attempt', 'claim'],
    }
    
    if malformed_cmd in suggestions:
        return f"Did you mean: /{' or /'.join(suggestions[malformed_cmd])}?"
    
    # Fuzzy matching for typos
    valid = ['claim', 'attempt', 'open', 'openai']
    closest = min(valid, key=lambda x: _levenshtein_distance(malformed_cmd, x))
    return f"Did you mean: /{closest}?"


def _levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # Insertion, deletion, substitution
            insertion = previous_row[j + 1] + 1
            deletion = current_row[j] + 1
            substitution = previous_row[j] + (c1 != c2)
            current_row.append(min(insertion, deletion, substitution))
        previous_row = current_row
    
    return previous_row[-1]


# Test cases
if __name__ == '__main__':
    test_cases = [
        '/opire try',
        '/claim #2746',
        '/attempt',
        '/openai',
        'invalid',
        '/opn #123',
    ]
    
    for test in test_cases:
        result = parse_bounty_command(test)
        print(f"\nInput: {test!r}")
        print(f"Result: {result}")
