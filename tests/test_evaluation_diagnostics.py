from ir_workbench.core import evaluate_rankings


def test_missing_queries_duplicates_and_error_analysis():
    result = evaluate_rankings({'q1': ['wrong', 'a', 'a']}, {'q1': ['a', 'b'], 'q2': ['c']}, k=3)
    first, missing = result['rows']
    assert first['returned_count'] == 2
    assert first['reciprocal_rank'] == .5
    assert first['missed_relevant_ids'] == ['b']
    assert missing['returned_count'] == 0 and missing['missed_relevant_ids'] == ['c']
    assert result['summary']['mrr'] == .25
    assert result['summary']['recall'] == .25
