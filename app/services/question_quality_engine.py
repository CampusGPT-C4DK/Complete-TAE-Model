from rapidfuzz import fuzz


def remove_similar_questions(questions, threshold=75):

    final = []

    for q in questions:

        duplicate = False

        for f in final:

            score = fuzz.token_sort_ratio(q, f)

            if score > threshold:
                duplicate = True
                break

        if not duplicate:
            final.append(q)

    return final