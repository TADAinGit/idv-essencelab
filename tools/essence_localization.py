"""Safe subset of the observed client TID name formatting; no eval or game calls."""
import re


def resolve_tid(value, texts, depth=0):
    if not isinstance(value, str):
        return ''
    if depth > 8:
        return value
    if value in texts:
        return texts[value]
    match = re.fullmatch(r'(TID_[A-Za-z0-9_]+)\(([^()]*)\)', value)
    if not match:
        return value
    template = texts.get(match[1])
    if not isinstance(template, str):
        return value
    args = [arg.strip() for arg in match[2].split(',') if arg.strip()]
    args = [resolve_tid(arg, texts, depth+1) if arg.startswith('TID_') else arg for arg in args]
    # Only string substitutions are needed for these UI names. Unsupported
    # formats stay unresolved rather than guessing coercions or syntax.
    tokens = re.findall(r'%%|%s|%.', template)
    if any(token not in ('%%', '%s') for token in tokens) or tokens.count('%s') != len(args):
        return value
    try:
        return template % tuple(args)
    except (TypeError, ValueError):
        return value
