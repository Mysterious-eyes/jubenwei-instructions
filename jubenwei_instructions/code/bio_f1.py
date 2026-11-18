"""Standard BIO entity micro-F1 used by the offline evaluation entry point."""

def _entities(sequence):
    entities = set()
    start = category = None
    for index, label in enumerate(list(sequence) + ['O']):
        prefix, _, current_category = label.partition('-')
        if start is not None and (prefix != 'I' or current_category != category):
            entities.add((start, index, category))
            start = category = None
        if prefix == 'B' or (prefix == 'I' and start is None):
            start, category = index, current_category
    return entities

def entity_counts(gold, predicted):
    """Return pooled (true positives, false positives, false negatives) for BIO entities."""
    if len(gold) != len(predicted):
        raise ValueError('Gold and predicted sequence counts differ')
    true_positive = false_positive = false_negative = 0
    for gold_sequence, predicted_sequence in zip(gold, predicted):
        if len(gold_sequence) != len(predicted_sequence):
            raise ValueError('Gold and predicted character counts differ')
        g, p = _entities(gold_sequence), _entities(predicted_sequence)
        true_positive += len(g & p)
        false_positive += len(p - g)
        false_negative += len(g - p)
    return true_positive, false_positive, false_negative


def f1_score(gold, predicted, zero_division=0):
    true_positive, false_positive, false_negative = entity_counts(gold, predicted)
    denominator = 2 * true_positive + false_positive + false_negative
    return 2 * true_positive / denominator if denominator else float(zero_division)
