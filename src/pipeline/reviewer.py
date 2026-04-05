from state import ShortsState

def reviewer(state: ShortsState) -> str:
    if not state['is_reviewed']:
        return 'no_review'  # or add a separate 'skip' route
    if state['review_type'] == 'none':
        return 'no_review'
    elif state['review_type'] == 'script':
        return 'script_change'
    elif state['review_type'] == 'media':
        return 'media_change'
    else:
        return 'both_change'