"""CSV parser service for processing transaction CSV files."""

import csv
import html
from decimal import Decimal, InvalidOperation
from io import StringIO
from typing import List
from pydantic import ValidationError
from src.schemas import TransactionCreate


class CSVParseError(Exception):
    """Exception raised when CSV parsing fails."""

    pass


class CSVParser:
    """Parser for Chase CSV transaction files."""

    REQUIRED_COLUMNS = {
        "Transaction Date",
        "Post Date",
        "Description",
        "Category",
        "Type",
        "Amount",
        "Memo",
    }

    def parse(self, csv_content: str) -> List[TransactionCreate]:
        """
        Parse CSV content and return list of TransactionCreate objects.

        Args:
            csv_content: CSV file content as string

        Returns:
            List of TransactionCreate objects

        Raises:
            CSVParseError: If CSV parsing fails
        """
        if not csv_content or not csv_content.strip():
            raise CSVParseError("CSV content is empty")

        try:
            # Parse CSV
            csv_file = StringIO(csv_content)
            reader = csv.DictReader(csv_file)

            # Validate header
            if not reader.fieldnames:
                raise CSVParseError("CSV file is missing header row")

            missing_columns = self.REQUIRED_COLUMNS - set(reader.fieldnames)
            if missing_columns:
                raise CSVParseError(
                    f"CSV is missing required columns: {', '.join(missing_columns)}"
                )

            # Parse transactions
            transactions = []
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (after header)
                try:
                    transaction = self._parse_row(row)
                    transactions.append(transaction)
                except (ValidationError, ValueError, InvalidOperation) as e:
                    raise CSVParseError(
                        f"Error parsing row {row_num}: {str(e)}"
                    ) from e

            if not transactions:
                raise CSVParseError("CSV contains no transaction data")

            return transactions

        except csv.Error as e:
            raise CSVParseError(f"Invalid CSV format: {str(e)}") from e

    def _parse_row(self, row: dict) -> TransactionCreate:
        """
        Parse a single CSV row into a TransactionCreate object.

        Args:
            row: Dictionary representing a CSV row

        Returns:
            TransactionCreate object

        Raises:
            ValidationError: If row data is invalid
            ValueError: If amount conversion fails
        """
        # Decode HTML entities and strip whitespace
        description = html.unescape(row["Description"].strip())
        category = row["Category"].strip()
        type_value = row["Type"].strip()
        memo = row["Memo"].strip() if row["Memo"] else ""

        # Parse amount
        try:
            amount = Decimal(row["Amount"].strip())
        except (InvalidOperation, ValueError) as e:
            raise ValueError(f"Invalid amount value: {row['Amount']}") from e

        # Create transaction object (this will validate dates and required fields)
        transaction = TransactionCreate(
            transaction_date=row["Transaction Date"].strip(),
            post_date=row["Post Date"].strip(),
            description=description,
            category=category,
            type=type_value,
            amount=amount,
            memo=memo,
        )

        return transaction
