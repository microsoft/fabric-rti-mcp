from typing import Any
from unittest.mock import Mock

from azure.kusto.data.response import KustoResponseDataSet

from fabric_rti_mcp.kusto.kusto_formatter import KustoFormatter


class TestFormatResults:
    """Test cases for the KustoFormatter.to_json function."""

    def test_KustoFormatter_to_json_with_valid_data(self) -> None:
        """Test KustoFormatter.to_json with valid KustoResponseDataSet containing data."""
        # Arrange
        mock_column1 = Mock()
        mock_column1.column_name = "Name"
        mock_column2 = Mock()
        mock_column2.column_name = "Age"
        mock_column3 = Mock()
        mock_column3.column_name = "City"

        mock_primary_result = Mock()
        mock_primary_result.columns = [mock_column1, mock_column2, mock_column3]
        mock_primary_result.rows = [["Alice", 30, "New York"], ["Bob", 25, "San Francisco"], ["Charlie", 35, "Chicago"]]

        mock_result_set = Mock(spec=KustoResponseDataSet)
        mock_result_set.primary_results = [mock_primary_result]

        expected_result: list[dict[str, Any]] = [
            {"Name": "Alice", "Age": 30, "City": "New York"},
            {"Name": "Bob", "Age": 25, "City": "San Francisco"},
            {"Name": "Charlie", "Age": 35, "City": "Chicago"},
        ]

        # Act
        result = KustoFormatter.to_json(mock_result_set)

        # Assert
        assert result.format == "json"
        assert result.data == expected_result
        assert len(result.data) == 3
        assert all(isinstance(row, dict) for row in result.data)

    def test_KustoFormatter_to_json_with_single_row(self) -> None:
        """Test KustoFormatter.to_json with a single row of data."""
        # Arrange
        mock_column = Mock()
        mock_column.column_name = "Message"

        mock_primary_result = Mock()
        mock_primary_result.columns = [mock_column]
        mock_primary_result.rows = [["Hello World"]]

        mock_result_set = Mock(spec=KustoResponseDataSet)
        mock_result_set.primary_results = [mock_primary_result]

        expected_result = [{"Message": "Hello World"}]

        # Act
        result = KustoFormatter.to_json(mock_result_set)

        # Assert
        assert result.format == "json"
        assert result.data == expected_result
        assert len(result.data) == 1

    def test_KustoFormatter_to_columnar_with_valid_data(self) -> None:
        """Test KustoFormatter.to_columnar with valid data containing escaped characters."""
        # Arrange
        mock_column1 = Mock()
        mock_column1.column_name = "ID"
        mock_column2 = Mock()
        mock_column2.column_name = "Message"
        mock_column3 = Mock()
        mock_column3.column_name = "Details"

        mock_primary_result = Mock()
        mock_primary_result.columns = [mock_column1, mock_column2, mock_column3]
        mock_primary_result.rows = [[1, "Hello\tWorld", "Line1\nLine2"], [2, 'Quote"Test', "Path\\File"]]

        mock_result_set = Mock(spec=KustoResponseDataSet)
        mock_result_set.primary_results = [mock_primary_result]

        expected_data = {
            "ID": [1, 2],
            "Message": ["Hello\tWorld", 'Quote"Test'],
            "Details": ["Line1\nLine2", "Path\\File"],
        }

        # Act
        result = KustoFormatter.to_columnar(mock_result_set)

        # Assert
        assert result.format == "columnar"
        assert result.data == expected_data
        assert len(result.data["ID"]) == 2
        assert result.data["Message"][0] == "Hello\tWorld"
        assert result.data["Details"][1] == "Path\\File"

    def test_KustoFormatter_to_csv_with_valid_data(self) -> None:
        """Test KustoFormatter.to_csv with valid data containing escaped characters."""
        # Arrange
        mock_column1 = Mock()
        mock_column1.column_name = "ID"
        mock_column2 = Mock()
        mock_column2.column_name = "Message"
        mock_column3 = Mock()
        mock_column3.column_name = "Details"

        mock_primary_result = Mock()
        mock_primary_result.columns = [mock_column1, mock_column2, mock_column3]
        mock_primary_result.rows = [[1, "Hello,World", "Line1\nLine2"], [2, 'Quote"Test', None]]

        mock_result_set = Mock(spec=KustoResponseDataSet)
        mock_result_set.primary_results = [mock_primary_result]

        # Act
        result = KustoFormatter.to_csv(mock_result_set)

        # Assert
        assert result.format == "csv"
        csv_data = result.data.strip()

        # Check that it starts with header
        assert csv_data.startswith("ID,Message,Details")

        # Check specific content is present - CSV handles escaping properly
        assert '"Hello,World"' in csv_data  # Comma properly quoted
        assert '"Quote""Test"' in csv_data  # Quote properly escaped as double quote
        assert '"Line1\nLine2"' in csv_data  # Newline preserved within quotes

        # Check that None is converted to empty string (CSV writer handles this)
        assert csv_data.endswith(",")  # Last field is empty (None becomes empty)


class TestParsingFunctionality:
    """Test cases for the KustoFormatter parsing functions."""

    def test_parse_json_format(self) -> None:
        """Test parsing JSON format data."""
        # Arrange
        json_data = [
            {"Name": "Alice", "Age": 30, "City": "New York"},
            {"Name": "Bob", "Age": 25, "City": "San Francisco"},
        ]
        response = {"format": "json", "data": json_data}

        # Act
        result = KustoFormatter.parse(response)

        # Assert
        assert result == json_data
        assert len(result) == 2
        assert result[0]["Name"] == "Alice"
        assert result[1]["Age"] == 25

    def test_parse_csv_format(self) -> None:
        """Test parsing CSV format data."""
        # Arrange
        csv_data = 'Name,Age,City\nAlice,30,"New York"\nBob,25,"San Francisco"'
        response = {"format": "csv", "data": csv_data}

        expected_result = [
            {"Name": "Alice", "Age": "30", "City": "New York"},
            {"Name": "Bob", "Age": "25", "City": "San Francisco"},
        ]

        # Act
        result = KustoFormatter.parse(response)

        # Assert
        assert result == expected_result
        assert len(result) == 2
        assert result[0]["Name"] == "Alice"
        assert result[1]["City"] == "San Francisco"

    def test_parse_csv_format_with_escaped_characters(self) -> None:
        """Test parsing CSV format with escaped characters."""
        # Arrange
        csv_data = 'ID,Message,Details\n1,"Hello,World","Line1\nLine2"\n2,"Quote""Test",""'
        response = {"format": "csv", "data": csv_data}

        expected_result = [
            {"ID": "1", "Message": "Hello,World", "Details": "Line1\nLine2"},
            {"ID": "2", "Message": 'Quote"Test', "Details": None},
        ]

        # Act
        result = KustoFormatter.parse(response)

        # Assert
        assert result == expected_result
        assert result[0]["Message"] == "Hello,World"  # Comma properly unescaped
        assert result[0]["Details"] == "Line1\nLine2"  # Newline preserved
        assert result[1]["Message"] == 'Quote"Test'  # Quote properly unescaped
        assert result[1]["Details"] is None  # Empty string converted to None

    def test_parse_tsv_format(self) -> None:
        """Test parsing TSV format data."""
        # Arrange
        tsv_data = "Name\tAge\tCity\nAlice\t30\tNew York\nBob\t25\tSan Francisco"
        response = {"format": "tsv", "data": tsv_data}

        expected_result = [
            {"Name": "Alice", "Age": "30", "City": "New York"},
            {"Name": "Bob", "Age": "25", "City": "San Francisco"},
        ]

        # Act
        result = KustoFormatter.parse(response)

        # Assert
        assert result == expected_result
        assert len(result) == 2
        assert result[0]["Name"] == "Alice"
        assert result[1]["City"] == "San Francisco"

    def test_parse_tsv_format_with_escaped_characters(self) -> None:
        """Test parsing TSV format with escaped characters."""
        # Arrange
        tsv_data = "ID\tMessage\tDetails\n1\tHello\\tWorld\tLine1\\nLine2\n2\tPath\\\\File\t"
        response = {"format": "tsv", "data": tsv_data}

        expected_result = [
            {"ID": "1", "Message": "Hello\tWorld", "Details": "Line1\nLine2"},
            {"ID": "2", "Message": "Path\\File", "Details": None},
        ]

        # Act
        result = KustoFormatter.parse(response)

        # Assert
        assert result == expected_result
        assert result[0]["Message"] == "Hello\tWorld"  # Tab properly unescaped
        assert result[0]["Details"] == "Line1\nLine2"  # Newline properly unescaped
        assert result[1]["Message"] == "Path\\File"  # Backslash properly unescaped
        assert result[1]["Details"] is None  # Empty string converted to None

    def test_parse_columnar_format(self) -> None:
        """Test parsing columnar format data."""
        # Arrange
        columnar_data = {"Name": ["Alice", "Bob"], "Age": [30, 25], "City": ["New York", "San Francisco"]}
        response = {"format": "columnar", "data": columnar_data}

        expected_result = [
            {"Name": "Alice", "Age": 30, "City": "New York"},
            {"Name": "Bob", "Age": 25, "City": "San Francisco"},
        ]

        # Act
        result = KustoFormatter.parse(response)

        # Assert
        assert result == expected_result
        assert len(result) == 2
        assert result[0]["Name"] == "Alice"
        assert result[1]["Age"] == 25

    def test_parse_header_arrays_format(self) -> None:
        """Test parsing header_arrays format data."""
        # Arrange
        header_arrays_data = '["Name","Age","City"]\n["Alice",30,"New York"]\n["Bob",25,"San Francisco"]'
        response = {"format": "header_arrays", "data": header_arrays_data}

        expected_result = [
            {"Name": "Alice", "Age": 30, "City": "New York"},
            {"Name": "Bob", "Age": 25, "City": "San Francisco"},
        ]

        # Act
        result = KustoFormatter.parse(response)

        # Assert
        assert result == expected_result
        assert len(result) == 2
        assert result[0]["Name"] == "Alice"
        assert result[1]["Age"] == 25

    def test_parse_with_KustoResponseFormat_object(self) -> None:
        """Test parsing with KustoResponseFormat object instead of dict."""
        # Arrange
        from fabric_rti_mcp.kusto.kusto_formatter import KustoResponseFormat

        json_data = [{"Name": "Alice", "Age": 30}]
        response = KustoResponseFormat(format="json", data=json_data)

        # Act
        result = KustoFormatter.parse(response)

        # Assert
        assert result == json_data
        assert len(result) == 1
        assert result[0]["Name"] == "Alice"

    def test_parse_with_invalid_format(self) -> None:
        """Test parsing with unsupported format raises ValueError."""
        # Arrange
        response = {"format": "invalid_format", "data": []}

        # Act & Assert
        try:
            KustoFormatter.parse(response)
            assert False, "Expected ValueError to be raised"
        except ValueError as e:
            assert "Unsupported format: invalid_format" in str(e)

    def test_parse_empty_data_cases(self) -> None:
        """Test parsing with various empty data cases."""
        # Test empty JSON
        assert KustoFormatter.parse({"format": "json", "data": []}) == []

        # Test empty CSV
        assert KustoFormatter.parse({"format": "csv", "data": ""}) == []

        # Test empty TSV
        assert KustoFormatter.parse({"format": "tsv", "data": ""}) == []

        # Test empty columnar
        assert KustoFormatter.parse({"format": "columnar", "data": {}}) == []

        # Test empty header_arrays
        assert KustoFormatter.parse({"format": "header_arrays", "data": ""}) == []

    def test_parse_malformed_data_cases(self) -> None:
        """Test parsing with malformed data returns empty list."""
        # Test invalid json should raise
        try:
            KustoFormatter.parse({"format": "json", "data": "not a list"})
            assert False, "Expected ValueError to be raised"
        except ValueError as e:
            assert "Invalid JSON format" in str(e)

        # Test None is a noop
        assert KustoFormatter.parse({"format": "csv", "data": None}) is None

        # Test invalid TSV data should raise
        try:
            KustoFormatter.parse({"format": "tsv", "data": 123})
            assert False, "Expected ValueError to be raised"
        except ValueError as e:
            assert "Invalid TSV format" in str(e)

        # Test invalid columnar data should raise
        try:
            KustoFormatter.parse({"format": "columnar", "data": "not a dict"})
            assert False, "Expected ValueError to be raised"
        except ValueError as e:
            assert "Invalid columnar format" in str(e)

        # Test malformed JSON in header_arrays
        assert KustoFormatter.parse({"format": "header_arrays", "data": "invalid json"}) == []

    def test_round_trip_conversion(self) -> None:
        """Test that we can convert to a format and parse it back to get the same data."""
        # Arrange - create mock data
        mock_column1 = Mock()
        mock_column1.column_name = "Name"
        mock_column2 = Mock()
        mock_column2.column_name = "Age"

        mock_primary_result = Mock()
        mock_primary_result.columns = [mock_column1, mock_column2]
        mock_primary_result.rows = [["Alice", 30], ["Bob", 25]]

        mock_result_set = Mock(spec=KustoResponseDataSet)
        mock_result_set.primary_results = [mock_primary_result]

        expected_data = [{"Name": "Alice", "Age": 30}, {"Name": "Bob", "Age": 25}]

        # Test JSON round-trip
        json_result = KustoFormatter.to_json(mock_result_set)
        parsed_json = KustoFormatter.parse(json_result)
        assert parsed_json == expected_data

        # Test columnar round-trip
        columnar_result = KustoFormatter.to_columnar(mock_result_set)
        parsed_columnar = KustoFormatter.parse(columnar_result)
        assert parsed_columnar == expected_data

        # Test header_arrays round-trip
        header_arrays_result = KustoFormatter.to_header_arrays(mock_result_set)
        parsed_header_arrays = KustoFormatter.parse(header_arrays_result)
        assert parsed_header_arrays == expected_data
