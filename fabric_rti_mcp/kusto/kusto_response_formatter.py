from typing import Any, Dict, List, Optional

from azure.kusto.data.response import KustoResponseDataSet


def format_results(result_set: Optional[KustoResponseDataSet]) -> List[Dict[str, Any]]:
    if not result_set or not getattr(result_set, "primary_results", None):
        return []

    first_result = result_set.primary_results[0]
    column_names = [col.column_name for col in first_result.columns]

    return [dict(zip(column_names, row)) for row in first_result.rows]
